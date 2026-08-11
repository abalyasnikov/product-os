#!/usr/bin/env python3
"""Preview or apply a fail-closed Product OS workspace installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import string
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, SchemaError

from .manifest import IGNORED_PARTS, ManifestSecurityError, tree_digest, verify


CANONICAL_ASSETS = ("schemas", "templates", "skills", "adapters", "integrations")
PLAN_ACTIONS = {"create", "update", "delete", "unchanged", "conflict"}
OWNERSHIP_CLASSES = {"managed", "preserved", "generated"}
GENERATED_PATHS = {
    ".product-os/release-manifest.json",
    ".product-os/install-plan.json",
    ".product-os/installed-manifest.json",
}
WORKSPACE_GUIDE_SOURCE = PurePosixPath("docs/workspace-guide.md")
CLIENT_ROOTS = {
    "codex": PurePosixPath(".agents/skills"),
    "claude-code": PurePosixPath(".claude/skills"),
    "openclaw": PurePosixPath("skills"),
}


class InstallError(ValueError):
    """Raised when installation cannot proceed without crossing a trust boundary."""


@dataclass(frozen=True)
class PlannedFile:
    source: Path | None
    destination: Path
    display_source: str
    display_destination: str
    expected_sha256: str
    size: int
    action: str = "create"
    ownership: str = "managed"
    content: bytes | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.display_source,
            "destination": self.display_destination,
            "action": self.action,
            "ownership": self.ownership,
            "sha256": self.expected_sha256,
            "size": self.size,
        }


@dataclass(frozen=True)
class InstallPlan:
    source: Path
    target: Path
    client: str
    files: tuple[PlannedFile, ...]
    product: str
    release: str
    canonical_origin: str
    publisher: str
    tree_digest: str
    config_sha256: str
    baseline_tree_digest: str | None = None
    source_commit: str | None = None
    target_parent_commit: str | None = None
    previous_operation_commit: str | None = None
    previous_source_commit: str | None = None
    review_mode: str = "unspecified"
    source_state: str = "unknown"

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "plan_version": 2,
            "client": self.client,
            "release_tree_digest": self.tree_digest,
            "config_sha256": self.config_sha256,
            "baseline_tree_digest": self.baseline_tree_digest,
            "files": [item.to_dict() for item in self.files],
        }

    @property
    def plan_hash(self) -> str:
        return _sha256_bytes(_canonical_json(self.canonical_payload()))

    def document(self) -> dict[str, Any]:
        return {**self.canonical_payload(), "plan_hash": self.plan_hash}

    def to_dict(self, *, mode: str = "preview") -> dict[str, Any]:
        action_counts = {
            action: sum(item.action == action for item in self.files)
            for action in sorted(PLAN_ACTIONS)
        }
        ownership_counts = {
            ownership: sum(item.ownership == ownership for item in self.files)
            for ownership in sorted(OWNERSHIP_CLASSES)
        }
        skipped_context: list[dict[str, str]] = []
        if self.baseline_tree_digest is None:
            planned_destinations = {item.display_destination for item in self.files}
            snippets = {
                "README.md": "Product decisions live in `context/` and `product/`; `.product-os/` is installed machinery.",
                "AGENTS.md": "Read `README.md` and route Product OS work through `.product-os/skills/`.",
                "CLAUDE.md": "@AGENTS.md",
            }
            for relative, snippet in snippets.items():
                if relative not in planned_destinations and (self.target / relative).exists():
                    skipped_context.append({"path": relative, "copy_paste_snippet": snippet})
        return {
            "mode": mode,
            "source_root": str(self.source),
            "target_root": str(self.target),
            "release": self.release,
            "canonical_origin": self.canonical_origin,
            "publisher": self.publisher,
            "operation": "update" if self.baseline_tree_digest else "install",
            "source_commit": self.source_commit,
            "source_state": self.source_state,
            "target_parent_commit": self.target_parent_commit,
            "previous_operation_commit": self.previous_operation_commit,
            "previous_source_commit": self.previous_source_commit,
            "review_mode": self.review_mode,
            "action_counts": action_counts,
            "ownership_counts": ownership_counts,
            "conflicts": [
                item.display_destination for item in self.files if item.action == "conflict"
            ],
            "conflict_details": [
                {
                    "path": item.display_destination,
                    "summary": "local bytes differ from the installed baseline or occupy a managed destination",
                }
                for item in self.files
                if item.action == "conflict"
            ],
            "skipped_context": skipped_context,
            "reassurance": (
                "Product artifacts and configuration remain unchanged."
                if self.baseline_tree_digest
                else None
            ),
            **self.document(),
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _git_output(root: Path, *args: str, required: bool = False) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        value = result.stdout.strip()
        return value or None
    if required:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise InstallError(detail)
    return None


def _entry_bytes(item: PlannedFile) -> bytes:
    if item.content is not None:
        return item.content
    if item.source is None:
        return b""
    return _safe_existing_file(item.source, label=f"planned source {item.display_source}")


def _ownership_for(destination: str) -> str:
    if destination in GENERATED_PATHS:
        return "generated"
    if destination in {".product-os/config.yaml", "README.md", "AGENTS.md", "CLAUDE.md"}:
        return "preserved"
    return "managed"


WORKSPACE_README = """# Product decisions

This repository holds the decisions, not the machinery. Everything below is yours: written by you
and your agent, readable without any tool, and versioned by Git.

| Where | What lives there |
|---|---|
| `context/strategy.md` | Positioning, this year's goal, ordered principles, and the MUST/WON'T bands. Every workflow that judges strategic fit reads it. Start here; it is the file people skip. |
| `product/signals/` | One falsifiable observation each, with its source and how much it can carry |
| `product/opportunities/` | Problems worth an explicit decision, with contradictions and gaps kept rather than averaged, and the decision itself as an append-only event |
| `product/prds/` | The product contract for one problem, including how success will be judged before delivery starts |
| `product/learnings/` | What the measurement actually showed, and what was decided because of it |

`.product-os/` and `.claude/` are installed machinery. Do not edit them by hand; an update will
refuse to proceed if you have.

## Where raw material goes

Nowhere, by default. Paste the interview note, the support export, or the meeting summary straight
into your agent. It records a normalized Signal plus a SHA-256 fingerprint of what you pasted, and
the raw text never enters Git — that is what keeps customer wording, names, and transcripts out of
a repository you may later share.

If you want the originals versioned anyway, `inputs/` and `external/` are yours and the installer
never touches them. That is your call and your privacy review, not a step this system asks for.

## Connecting a provider

Granola, Linear, and analytics stay in their own tools; this workspace only records which of them
you enabled. Ask your agent to enable one, and it follows that provider's own authentication flow —
no credential is ever stored here.

Enabling a connector changes what the workspace installs, so it ends with an installer update that
adds that provider's descriptor. Until then `product-os check` will say the descriptor is missing,
and workflows that need it report a named gap instead of pretending to work.

## Working here

You talk to your agent; the agent reads and writes these files. Three prompts cover most of it:

- `Draft context/strategy.md from the template and interview me for it.`
- `Turn this note into decision-relevant evidence. Show the payload before writing it.`
- `Show my Decision Queue. If it is empty, tell me the next useful action.`

Three judgments stay yours: pursue, hold, or reject an Opportunity; approve the contract before
delivery; and decide scale, iterate, hold, kill, or complete once the result is in. The agent
investigates, drafts, links, and recommends between them.

## Checking it

Run this from the Product OS checkout you installed from:

```bash
uvx --from <source-checkout> product-os check .     # is the trail sound?
uvx --from <source-checkout> product-os queue .     # what needs you?
```

`check` verifies schemas, the relationship graph, that decision events were appended and never
rewritten, that approvals point at commits that exist, and that no credential or transcript
slipped into an artifact. It says nothing about whether a decision was good.

`queue` prints the decisions waiting on you, derived from these files and nothing else. It writes
nothing, so there is no inbox to maintain and no status to go stale. What it could not check —
a missing config, an unresolvable approval — it names rather than omitting.
"""


def _source_state(source: Path) -> str:
    """Describe what is actually being installed, not just what HEAD says.

    The trust gate asks a human to confirm a commit. A commit only describes the bytes when the
    tree is clean and there is a tree at all, so a dirty checkout or a copied folder says so
    instead of letting a reassuring SHA stand in for an unreviewed working tree. This reports;
    it does not refuse. Content integrity is already carried by the release manifest, and a
    refusal here would only be meaningful once there is a published origin to compare against.
    """
    if _git_output(source, "rev-parse", "--git-dir") is None:
        return "not_a_git_checkout"
    try:
        # Not _git_output: an empty status means clean, and that helper cannot tell empty
        # output from a failed command.
        status = subprocess.run(
            ["git", "-C", str(source), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    if status.returncode != 0:
        return "unknown"
    changed = [line for line in status.stdout.splitlines() if line.strip()]
    return f"uncommitted_changes:{len(changed)}" if changed else "clean"


def _workspace_context_files(target: Path) -> list[PlannedFile]:
    values = {
        "README.md": WORKSPACE_README.encode("utf-8"),
        "AGENTS.md": (
            b"# Product OS workspace\n\n"
            b"Read `README.md` for what this repository holds, then route Product OS work through "
            b"the canonical skills in `.product-os/skills/`. Product artifacts and context "
            b"are user-owned; never edit managed `.product-os/` files.\n"
        ),
        "CLAUDE.md": b"@AGENTS.md\n",
    }
    result: list[PlannedFile] = []
    for relative, content in values.items():
        destination = target / relative
        if destination.exists() or destination.is_symlink():
            continue
        result.append(
            PlannedFile(
                None,
                destination,
                "@generated-context",
                relative,
                _sha256_bytes(content),
                len(content),
                ownership="preserved",
                content=content,
            )
        )
    return result


def _load_installed_manifest(target: Path) -> dict[str, Any] | None:
    path = target / ".product-os/installed-manifest.json"
    if not path.exists() and not path.is_symlink():
        return None
    raw = _safe_existing_file(path, label="installed manifest")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InstallError(f"installed manifest is invalid JSON: {exc}") from exc
    if (
        not isinstance(value, dict)
        or value.get("manifest_kind") != "installed_workspace"
        or not isinstance(value.get("files"), list)
        or not isinstance(value.get("tree_digest"), str)
    ):
        raise InstallError("installed manifest has invalid identity or file metadata")
    entries = value["files"]
    paths: list[str] = []
    normalized: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise InstallError("installed manifest contains a non-object file entry")
        relative = entry.get("path")
        digest = entry.get("sha256")
        size = entry.get("size")
        ownership = entry.get("ownership", _ownership_for(str(relative)))
        if (
            not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in string.hexdigits for char in digest)
            or not isinstance(size, int)
            or size < 0
            or ownership not in OWNERSHIP_CLASSES
        ):
            raise InstallError("installed manifest contains unsafe or invalid file metadata")
        paths.append(relative)
        normalized.append({"path": relative, "sha256": digest.lower(), "size": size})
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise InstallError("installed manifest file entries must be unique and sorted")
    if tree_digest(normalized) != value["tree_digest"]:
        raise InstallError("installed manifest tree_digest does not match its baseline entries")
    return value


def _safe_existing_file(path: Path, *, label: str) -> bytes:
    if path.is_symlink():
        raise InstallError(f"{label} must not be a symlink: {path}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise InstallError(f"{label} is unavailable: {exc}") from exc
    if not resolved.is_file():
        raise InstallError(f"{label} is not a regular file: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise InstallError(f"cannot read {label}: {exc}") from exc


def _relative_path(value: Any, *, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise InstallError(f"{label} must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("/") or any(part in {"", ".", ".."} for part in path.parts):
        raise InstallError(f"{label} must be relative and contain no '.' or '..': {value!r}")
    return path


def _under(path: PurePosixPath, root: PurePosixPath) -> bool:
    return path == root or root in path.parents


def _assert_contained(path: Path, root: Path, *, label: str, strict: bool) -> Path:
    try:
        resolved_root = root.resolve(strict=False)
        resolved_path = path.resolve(strict=strict)
    except OSError as exc:
        raise InstallError(f"cannot resolve {label}: {exc}") from exc
    if not resolved_path.is_relative_to(resolved_root):
        raise InstallError(f"{label} resolves outside allowed root: {path}")
    return resolved_path


def _reject_symlink_components(root: Path, relative: PurePosixPath, *, label: str) -> None:
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise InstallError(f"{label} contains a symlink component: {current}")
        if not current.exists():
            break


def _reject_tree_symlinks(
    root: Path,
    *,
    label: str,
    skip_non_distributed_directories: bool = False,
) -> None:
    def walk_error(exc: OSError) -> None:
        raise InstallError(f"cannot traverse {label}: {exc}") from exc

    for current, directory_names, file_names in os.walk(root, followlinks=False, onerror=walk_error):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in directory_names:
            if skip_non_distributed_directories and (
                name in IGNORED_PARTS or name.endswith(".egg-info")
            ):
                continue
            candidate = current_path / name
            if candidate.is_symlink():
                raise InstallError(
                    f"{label} contains a symlink: {candidate.relative_to(root).as_posix()}"
                )
            kept_directories.append(name)
        directory_names[:] = kept_directories
        for name in file_names:
            candidate = current_path / name
            if candidate.is_symlink():
                raise InstallError(
                    f"{label} contains a symlink: {candidate.relative_to(root).as_posix()}"
                )


def _load_manifest(source: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    problems = verify(source)
    if problems:
        raise InstallError("source manifest verification failed: " + "; ".join(problems))
    raw = _safe_existing_file(source / "manifest.json", label="source manifest")
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InstallError(f"source manifest is invalid JSON: {exc}") from exc
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise InstallError("source manifest files must be an array")
    by_path: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise InstallError("source manifest contains an invalid file entry")
        by_path[entry["path"]] = entry
    return manifest, by_path


class _StrictLoader(yaml.SafeLoader):
    def compose_node(self, parent: yaml.Node | None, index: Any) -> yaml.Node:
        if self.check_event(yaml.AliasEvent):
            raise InstallError("workspace config must not contain YAML aliases")
        return super().compose_node(parent, index)


def _construct_unique_mapping(
    loader: _StrictLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise InstallError(f"workspace config contains duplicate key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def _load_config(source: Path, config: Path, client: str) -> tuple[Path, bytes, dict[str, Any]]:
    raw = _safe_existing_file(config, label="workspace config")
    if len(raw) > 1_000_000:
        raise InstallError("workspace config exceeds 1000000 bytes")
    try:
        value = yaml.load(raw, Loader=_StrictLoader)
    except InstallError:
        raise
    except (yaml.YAMLError, UnicodeError, TypeError) as exc:
        raise InstallError(f"workspace config is invalid strict YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise InstallError("workspace config root must be an object")

    schema_path = source / "schemas" / "config.schema.json"
    schema_raw = _safe_existing_file(schema_path, label="workspace config schema")
    try:
        schema = json.loads(schema_raw)
        Draft202012Validator.check_schema(schema)
    except (json.JSONDecodeError, SchemaError) as exc:
        raise InstallError(f"workspace config schema is invalid: {exc}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.absolute_path)
    )
    if errors:
        first = errors[0]
        field = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise InstallError(f"workspace config does not match schema at {field}: {first.message}")
    if value.get("selected_client") != client:
        raise InstallError(
            f"workspace config selected_client {value.get('selected_client')!r} does not match --client {client!r}"
        )
    return config.resolve(strict=True), raw, value


def _load_adapter(source: Path, client: str) -> tuple[dict[str, Any], bytes]:
    path = source / "adapters" / client / "manifest.yaml"
    raw = _safe_existing_file(path, label=f"{client} adapter manifest")
    try:
        value = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise InstallError(f"{client} adapter manifest is invalid YAML: {exc}") from exc
    if not isinstance(value, dict) or value.get("client") != client or value.get("generated") is not True:
        raise InstallError(f"{client} adapter manifest has invalid identity or generation metadata")
    return value, raw


def _projection_files(
    source: Path,
    target: Path,
    client: str,
    adapter: dict[str, Any],
    manifest_entries: dict[str, dict[str, Any]],
) -> list[PlannedFile]:
    allowed_root = CLIENT_ROOTS[client]
    projection_metadata = adapter.get("projection")
    if not isinstance(projection_metadata, dict) or projection_metadata.get("client_skill_location") != allowed_root.as_posix():
        raise InstallError(f"{client} adapter client_skill_location must be {allowed_root.as_posix()}")
    projections = adapter.get("projections")
    if not isinstance(projections, list) or not projections:
        raise InstallError(f"{client} adapter must declare at least one projection")

    names: set[str] = set()
    destinations: set[str] = set()
    planned: list[PlannedFile] = []
    for index, projection in enumerate(projections):
        if not isinstance(projection, dict):
            raise InstallError(f"projection {index} must be an object")
        name = projection.get("name")
        if not isinstance(name, str) or not name.startswith("product-os-") or "/" in name or "\\" in name:
            raise InstallError(f"projection {index} has an invalid product-os wrapper name")
        if name in names:
            raise InstallError(f"duplicate projection name: {name}")
        names.add(name)

        wrapper = _relative_path(projection.get("wrapper_source"), label=f"projection {name} wrapper_source")
        canonical = _relative_path(projection.get("canonical_source"), label=f"projection {name} canonical_source")
        destination = _relative_path(projection.get("destination"), label=f"projection {name} destination")
        expected_wrapper_root = PurePosixPath("adapters") / "_shared" / "skills"
        if not _under(wrapper, expected_wrapper_root):
            raise InstallError(f"projection {name} wrapper_source is outside {expected_wrapper_root}")
        if wrapper.name != "SKILL.md" or wrapper.parent.name != name:
            raise InstallError(f"projection {name} wrapper_source must end in {name}/SKILL.md")
        if not _under(canonical, PurePosixPath(".product-os/skills")):
            raise InstallError(f"projection {name} canonical_source is outside .product-os/skills")
        expected_canonical = PurePosixPath(".product-os/skills") / name.removeprefix("product-os-") / "SKILL.md"
        if canonical != expected_canonical:
            raise InstallError(f"projection {name} canonical_source must be {expected_canonical}")
        if not _under(destination, allowed_root):
            raise InstallError(f"projection {name} destination is outside {allowed_root}")
        if destination.name != "SKILL.md" or destination.parent.name != name:
            raise InstallError(f"projection {name} destination must end in {name}/SKILL.md")
        if destination.as_posix() in destinations:
            raise InstallError(f"duplicate projection destination: {destination}")
        destinations.add(destination.as_posix())

        wrapper_key = wrapper.as_posix()
        entry = manifest_entries.get(wrapper_key)
        if entry is None or not isinstance(entry.get("sha256"), str):
            raise InstallError(f"projection {name} wrapper is not covered by the source manifest")
        wrapper_path = source.joinpath(*wrapper.parts)
        _reject_symlink_components(source, wrapper, label=f"projection {name} wrapper_source")
        _assert_contained(wrapper_path, source, label=f"projection {name} wrapper_source", strict=True)
        if not wrapper_path.is_file():
            raise InstallError(f"projection {name} wrapper_source is not a regular file")

        canonical_source = source.joinpath(*canonical.parts[1:])
        canonical_relative = PurePosixPath(*canonical.parts[1:])
        _reject_symlink_components(source, canonical_relative, label=f"projection {name} canonical_source")
        _assert_contained(canonical_source, source, label=f"projection {name} canonical_source", strict=True)
        if not canonical_source.is_file():
            raise InstallError(f"projection {name} canonical_source does not exist in canonical assets")

        _reject_symlink_components(target, destination, label=f"projection {name} destination")
        destination_path = target.joinpath(*destination.parts)
        _assert_contained(destination_path, target / Path(*allowed_root.parts), label=f"projection {name} destination", strict=False)
        planned.append(
            PlannedFile(
                wrapper_path,
                destination_path,
                wrapper.as_posix(),
                destination.as_posix(),
                entry["sha256"].lower(),
                wrapper_path.stat().st_size,
            )
        )

    _reject_symlink_components(target, allowed_root, label=f"{client} client skill root")
    return planned


def _is_installed_asset(path: PurePosixPath, client: str, enabled_connectors: set[str]) -> bool:
    """A workspace receives what it selected, not the whole distribution.

    Adapters for clients the user did not choose and descriptors for providers they did not
    connect are machinery, not product context. Shipping them puts dozens of files a reader
    can never act on into a repository whose point is that everything in it was decided.
    """
    parts = path.parts
    if parts[0] == "adapters" and len(parts) > 1 and parts[1] in CLIENT_ROOTS and parts[1] != client:
        return False
    if parts[:2] == ("integrations", "providers") and len(parts) > 2:
        return PurePosixPath(parts[2]).stem in enabled_connectors
    return True


def plan_install(
    source: str | Path,
    target: str | Path,
    client: str,
    config_path: str | Path,
    *,
    allow_unpublished_local: bool = False,
) -> InstallPlan:
    if client not in CLIENT_ROOTS:
        raise InstallError(f"unknown client {client!r}; choose one of: {', '.join(CLIENT_ROOTS)}")
    source_path = Path(source)
    target_path = Path(target)
    if source_path.is_symlink() or target_path.is_symlink():
        raise InstallError("source and target roots must not be symlinks")
    try:
        source_path = source_path.resolve(strict=True)
        target_path = target_path.resolve(strict=True)
    except OSError as exc:
        raise InstallError(f"source or target is unavailable: {exc}") from exc
    if not source_path.is_dir() or not target_path.is_dir():
        raise InstallError("source and target must be existing directories")
    if source_path == target_path:
        raise InstallError("source and target must be different directories")

    _reject_tree_symlinks(
        source_path,
        label="source tree",
        skip_non_distributed_directories=True,
    )
    _reject_tree_symlinks(target_path, label="target tree")

    manifest, manifest_entries = _load_manifest(source_path)
    origin = manifest.get("canonical_origin")
    if not isinstance(origin, str) or not origin:
        raise InstallError("source manifest has no canonical_origin")
    if origin == "unpublished" and not allow_unpublished_local:
        raise InstallError("unpublished source requires explicit --allow-unpublished-local")

    installed = _load_installed_manifest(target_path)
    is_update = installed is not None
    config_input = target_path / ".product-os/config.yaml" if is_update else Path(config_path)
    config, config_raw, config_value = _load_config(source_path, config_input, client)
    if is_update and installed.get("client") != client:
        raise InstallError("installed manifest client does not match --client; switch clients via uninstall and reinstall")

    planned: list[PlannedFile] = []
    for asset in CANONICAL_ASSETS:
        asset_root = source_path / asset
        if asset_root.is_symlink() or not asset_root.is_dir():
            raise InstallError(f"canonical asset directory is missing or unsafe: {asset}")
    # config maps a capability to a provider name; the descriptor file is named for the provider
    enabled_connectors = {
        str(provider) for provider in (config_value.get("connectors") or {}).values()
    }
    for relative, entry in sorted(manifest_entries.items()):
        path = _relative_path(relative, label="source manifest entry path")
        if path.parts[0] not in CANONICAL_ASSETS:
            continue
        if not _is_installed_asset(path, client, enabled_connectors):
            continue
        source_file = source_path.joinpath(*path.parts)
        destination_relative = PurePosixPath(".product-os") / path
        destination = target_path.joinpath(*destination_relative.parts)
        _reject_symlink_components(source_path, path, label=f"canonical source {relative}")
        _assert_contained(source_file, source_path, label=f"canonical source {relative}", strict=True)
        _reject_symlink_components(target_path, destination_relative, label=f"canonical destination {relative}")
        _assert_contained(destination, target_path, label=f"canonical destination {relative}", strict=False)
        planned.append(
            PlannedFile(
                source_file,
                destination,
                path.as_posix(),
                destination_relative.as_posix(),
                entry["sha256"].lower(),
                source_file.stat().st_size,
            )
        )

    manifest_raw = _safe_existing_file(source_path / "manifest.json", label="source manifest")
    planned.append(
        PlannedFile(
            source_path / "manifest.json",
            target_path / ".product-os" / "release-manifest.json",
            "manifest.json",
            ".product-os/release-manifest.json",
            _sha256_bytes(manifest_raw),
            len(manifest_raw),
            ownership="generated",
        )
    )
    planned.append(
        PlannedFile(
            config,
            target_path / ".product-os" / "config.yaml",
            "@config",
            ".product-os/config.yaml",
            _sha256_bytes(config_raw),
            len(config_raw),
            action="unchanged" if is_update else "create",
            ownership="preserved",
        )
    )

    guide_path = source_path.joinpath(*WORKSPACE_GUIDE_SOURCE.parts)
    guide_raw = (
        _safe_existing_file(guide_path, label="workspace guide")
        if guide_path.is_file() and not guide_path.is_symlink()
        else b"# Product OS workspace\n\nRead `.product-os/skills/` for canonical workflows.\n"
    )
    planned.append(
        PlannedFile(
            guide_path if guide_path.is_file() else None,
            target_path / ".product-os/README.md",
            WORKSPACE_GUIDE_SOURCE.as_posix(),
            ".product-os/README.md",
            _sha256_bytes(guide_raw),
            len(guide_raw),
            content=None if guide_path.is_file() else guide_raw,
        )
    )

    adapter, _ = _load_adapter(source_path, client)
    planned.extend(_projection_files(source_path, target_path, client, adapter, manifest_entries))
    if not is_update:
        planned.extend(_workspace_context_files(target_path))

    baseline_entries: dict[str, dict[str, Any]] = {}
    if installed is not None:
        for entry in installed["files"]:
            if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                baseline_entries[entry["path"]] = entry

    desired: dict[str, PlannedFile] = {}
    for item in planned:
        action = item.action
        baseline = baseline_entries.get(item.display_destination)
        destination_exists = item.destination.exists() and not item.destination.is_symlink()
        if is_update and item.ownership == "generated":
            action = "update" if destination_exists else "create"
        elif is_update and item.ownership != "preserved":
            if baseline is None:
                action = "conflict" if destination_exists or item.destination.is_symlink() else "create"
            elif not destination_exists:
                action = "create"
            else:
                observed = _safe_existing_file(item.destination, label="managed destination")
                baseline_matches = (
                    _sha256_bytes(observed) == baseline.get("sha256")
                    and len(observed) == baseline.get("size")
                )
                if not baseline_matches:
                    action = "conflict"
                elif _sha256_bytes(observed) == item.expected_sha256 and len(observed) == item.size:
                    action = "unchanged"
                else:
                    action = "update"
        elif not is_update and (
            destination_exists or item.destination.is_symlink()
        ):
            action = "conflict"
        desired[item.display_destination] = PlannedFile(
            item.source,
            item.destination,
            item.display_source,
            item.display_destination,
            item.expected_sha256,
            item.size,
            action,
            item.ownership,
            item.content,
        )

    if is_update:
        for relative, baseline in baseline_entries.items():
            ownership = baseline.get("ownership", _ownership_for(relative))
            if relative in desired or ownership != "managed":
                continue
            destination = target_path / relative
            if not destination.exists() and not destination.is_symlink():
                continue
            observed = _safe_existing_file(destination, label="removed-upstream managed destination")
            action = "delete" if (
                _sha256_bytes(observed) == baseline.get("sha256")
                and len(observed) == baseline.get("size")
            ) else "conflict"
            desired[relative] = PlannedFile(
                None,
                destination,
                "@removed-upstream",
                relative,
                str(baseline.get("sha256", "0" * 64)),
                int(baseline.get("size", 0)),
                action,
                "managed",
            )

    active_root = target_path.joinpath(*CLIENT_ROOTS[client].parts)
    if active_root.is_dir():
        for candidate in sorted(active_root.glob("product-os-*")):
            relative = candidate.relative_to(target_path).as_posix()
            if candidate.is_symlink():
                raise InstallError(f"unexpected product-os wrapper symlink: {relative}")
            skill_file = candidate / "SKILL.md" if candidate.is_dir() else candidate
            display = skill_file.relative_to(target_path).as_posix()
            if display in desired:
                continue
            if not skill_file.is_file() or skill_file.is_symlink():
                raise InstallError(f"unexpected product-os wrapper file or directory: {relative}")
            raw = _safe_existing_file(skill_file, label="unexpected product-os wrapper")
            desired[display] = PlannedFile(
                None,
                skill_file,
                "@unexpected-wrapper",
                display,
                _sha256_bytes(raw),
                len(raw),
                "conflict",
                "managed",
            )

    planned = sorted(desired.values(), key=lambda item: item.display_destination)
    destinations: set[Path] = set()
    for item in planned:
        if item.destination in destinations:
            raise InstallError(f"duplicate install destination: {item.display_destination}")
        destinations.add(item.destination)

    return InstallPlan(
        source=source_path,
        target=target_path,
        client=client,
        files=tuple(planned),
        product=str(manifest.get("product", "product-os")),
        release=str(manifest.get("release", "unknown")),
        canonical_origin=origin,
        publisher=str(manifest.get("publisher", "unpublished")),
        tree_digest=str(manifest.get("tree_digest", "")),
        config_sha256=_sha256_bytes(config_raw),
        baseline_tree_digest=installed.get("tree_digest") if installed else None,
        source_commit=_git_output(source_path, "rev-parse", "HEAD"),
        source_state=_source_state(source_path),
        target_parent_commit=_git_output(target_path, "rev-parse", "HEAD"),
        previous_operation_commit=(
            _git_output(target_path, "log", "-1", "--format=%H", "--", ".product-os/installed-manifest.json")
            if installed else None
        ),
        previous_source_commit=(
            installed.get("source_commit") if installed and isinstance(installed.get("source_commit"), str) else None
        ),
        review_mode=(
            str(config_value.get("review", {}).get("mode", "unspecified"))
            if isinstance(config_value.get("review"), dict)
            else "unspecified"
        ),
    )


def _copy_exclusive(item: PlannedFile) -> None:
    data = _entry_bytes(item)
    destination_created = False
    try:
        destination_fd = os.open(
            item.destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o644,
        )
        destination_created = True
        try:
            view = memoryview(data)
            while view:
                written = os.write(destination_fd, view)
                view = view[written:]
            os.fsync(destination_fd)
        finally:
            os.close(destination_fd)
        if _sha256_bytes(data) != item.expected_sha256 or len(data) != item.size:
            raise InstallError(f"source changed after preview: {item.display_source}")
    except Exception:
        if destination_created:
            try:
                item.destination.unlink()
            except OSError:
                pass
        raise


def _write_atomic(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fchmod(descriptor, 0o644)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def _write_exclusive(path: Path, data: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o644,
    )
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
    finally:
        os.close(descriptor)


def _plan_bytes(plan: InstallPlan) -> bytes:
    return json.dumps(plan.document(), indent=2, sort_keys=True).encode("utf-8") + b"\n"


def write_plan(plan: InstallPlan, destination: str | Path) -> Path:
    path = Path(destination)
    if path.is_symlink() or path.exists():
        raise InstallError(f"plan destination already exists or is a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_exclusive(path, _plan_bytes(plan))
    return path


def load_plan_document(path: str | Path) -> dict[str, Any]:
    raw = _safe_existing_file(Path(path), label="confirmed install plan")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InstallError(f"confirmed install plan is invalid JSON: {exc}") from exc
    v1_keys = {
        "plan_version",
        "client",
        "release_tree_digest",
        "config_sha256",
        "files",
        "plan_hash",
    }
    v2_keys = {*v1_keys, "baseline_tree_digest"}
    expected_keys = v1_keys if isinstance(value, dict) and value.get("plan_version") == 1 else v2_keys
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise InstallError("confirmed install plan has unexpected or missing fields")
    payload = {key: value[key] for key in expected_keys - {"plan_hash"}}
    observed = _sha256_bytes(_canonical_json(payload))
    if value.get("plan_hash") != observed:
        raise InstallError("confirmed install plan hash does not match its canonical payload")
    return value


def _installed_manifest(plan: InstallPlan, install_plan_bytes: bytes) -> dict[str, Any]:
    entries = [
        {
            "path": item.display_destination,
            "sha256": item.expected_sha256,
            "size": item.size,
            "ownership": item.ownership,
        }
        for item in plan.files
        if item.action not in {"delete", "conflict"}
    ]
    if plan.baseline_tree_digest:
        previous = _load_installed_manifest(plan.target)
        planned_paths = {item.display_destination for item in plan.files}
        for entry in previous.get("files", []) if previous else []:
            if (
                isinstance(entry, dict)
                and entry.get("path") not in planned_paths
                and entry.get("ownership", _ownership_for(str(entry.get("path")))) == "preserved"
            ):
                entries.append(dict(entry))
    entries.append(
        {
            "path": ".product-os/install-plan.json",
            "sha256": _sha256_bytes(install_plan_bytes),
            "size": len(install_plan_bytes),
            "ownership": "generated",
        }
    )
    entries.sort(key=lambda entry: str(entry["path"]))
    return {
        "manifest_version": 1,
        "manifest_kind": "installed_workspace",
        "hash_algorithm": "sha256",
        "client": plan.client,
        "files": entries,
        "tree_digest": tree_digest(entries),
        "install_plan_sha256": plan.plan_hash,
        "source_commit": plan.source_commit,
        "target_parent_commit": plan.target_parent_commit,
        "previous_operation_commit": plan.previous_operation_commit,
        "parent_release": {
            "product": plan.product,
            "release": plan.release,
            "canonical_origin": plan.canonical_origin,
            "publisher": plan.publisher,
            "tree_digest": plan.tree_digest,
        },
    }


def apply_plan(plan: InstallPlan) -> None:
    _reject_tree_symlinks(
        plan.source,
        label="source tree",
        skip_non_distributed_directories=True,
    )
    _reject_tree_symlinks(plan.target, label="target tree")
    conflicts = [item.display_destination for item in plan.files if item.action == "conflict"]
    if conflicts:
        raise InstallError("managed-file conflicts halt the operation before writes: " + ", ".join(conflicts))
    baseline_entries: dict[str, dict[str, Any]] = {}
    if plan.baseline_tree_digest:
        installed = _load_installed_manifest(plan.target)
        if installed is None or installed.get("tree_digest") != plan.baseline_tree_digest:
            raise InstallError("installed baseline changed after preview; re-plan the update")
        baseline_entries = {
            entry["path"]: entry
            for entry in installed["files"]
            if isinstance(entry, dict) and isinstance(entry.get("path"), str)
        }
    for item in plan.files:
        if item.action == "create" and (item.destination.exists() or item.destination.is_symlink()):
            raise InstallError(f"destination conflict; refusing to overwrite: {item.display_destination}")
        if item.action in {"update", "unchanged", "delete"}:
            if not item.destination.exists() or item.destination.is_symlink():
                raise InstallError(f"planned destination drifted after preview: {item.display_destination}")
        if item.action == "unchanged":
            observed = _safe_existing_file(item.destination, label="unchanged destination")
            if _sha256_bytes(observed) != item.expected_sha256 or len(observed) != item.size:
                raise InstallError(f"unchanged destination drifted after preview: {item.display_destination}")
        if item.ownership == "managed" and item.action in {"update", "delete"}:
            baseline = baseline_entries.get(item.display_destination)
            observed = _safe_existing_file(item.destination, label="managed update baseline")
            if (
                baseline is None
                or _sha256_bytes(observed) != baseline.get("sha256")
                or len(observed) != baseline.get("size")
            ):
                raise InstallError(f"managed destination drifted after preview: {item.display_destination}")

    if plan.baseline_tree_digest:
        if _git_output(plan.target, "rev-parse", "--verify", "HEAD") is None:
            raise InstallError("update requires a committed install; commit the current workspace first")
        if _git_output(
            plan.target,
            "ls-files",
            "--error-unmatch",
            ".product-os/installed-manifest.json",
        ) is None:
            raise InstallError("update requires the install commit; commit Product OS before updating")
        guarded = [
            item.display_destination
            for item in plan.files
            if item.ownership == "managed" and item.action in {"update", "delete"}
        ]
        if guarded:
            status = _git_output(plan.target, "status", "--porcelain", "--", *guarded, required=True)
            if status:
                raise InstallError("update requires managed planned paths to be clean; commit or restore them first")
    generated_destinations = (
        plan.target / ".product-os" / "install-plan.json",
        plan.target / ".product-os" / "installed-manifest.json",
    )
    for destination in generated_destinations:
        if destination.is_symlink() or (not plan.baseline_tree_digest and destination.exists()):
            raise InstallError(
                f"destination conflict; refusing to overwrite: {destination.relative_to(plan.target)}"
            )

    created_files: list[Path] = []
    created_directories: list[Path] = []
    git_restorable: list[Path] = []
    try:
        for item in plan.files:
            if item.action == "unchanged":
                continue
            missing: list[Path] = []
            current = item.destination.parent
            while current != plan.target and not current.exists():
                missing.append(current)
                current = current.parent
            if current.is_symlink():
                raise InstallError(f"destination parent became a symlink: {current}")
            for directory in reversed(missing):
                directory.mkdir()
                created_directories.append(directory)
            if item.action == "create":
                _copy_exclusive(item)
                created_files.append(item.destination)
            elif item.action == "update":
                data = _entry_bytes(item)
                if _sha256_bytes(data) != item.expected_sha256 or len(data) != item.size:
                    raise InstallError(f"source changed after preview: {item.display_source}")
                _write_atomic(item.destination, data)
                git_restorable.append(item.destination)
            elif item.action == "delete":
                item.destination.unlink()
                git_restorable.append(item.destination)
        install_plan_bytes = _plan_bytes(plan)
        install_plan_path = generated_destinations[0]
        if plan.baseline_tree_digest:
            _write_atomic(install_plan_path, install_plan_bytes)
            git_restorable.append(install_plan_path)
        else:
            _write_exclusive(install_plan_path, install_plan_bytes)
            created_files.append(install_plan_path)
        manifest_bytes = (
            json.dumps(_installed_manifest(plan, install_plan_bytes), indent=2, sort_keys=True).encode(
                "utf-8"
            )
            + b"\n"
        )
        installed_manifest_path = generated_destinations[1]
        if plan.baseline_tree_digest:
            _write_atomic(installed_manifest_path, manifest_bytes)
            git_restorable.append(installed_manifest_path)
        else:
            _write_exclusive(installed_manifest_path, manifest_bytes)
            created_files.append(installed_manifest_path)
    except (InstallError, OSError):
        if git_restorable:
            relative_paths = [path.relative_to(plan.target).as_posix() for path in git_restorable]
            _git_output(plan.target, "checkout", "HEAD", "--", *relative_paths)
        for path in reversed(created_files):
            try:
                path.unlink()
            except OSError:
                pass
        for path in reversed(created_directories):
            try:
                path.rmdir()
            except OSError:
                pass
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--client", required=True, choices=sorted(CLIENT_ROOTS))
    parser.add_argument("--config", "--config-path", required=True, dest="config_path")
    parser.add_argument("--allow-unpublished-local", action="store_true")
    parser.add_argument("--write-plan", help="write the canonical preview plan without changing the target")
    parser.add_argument("--apply-plan", help="apply exactly this previously written canonical plan")
    parser.add_argument("--expect-plan-hash", help="confirmed SHA-256 of --apply-plan")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.write_plan and args.apply_plan:
            raise InstallError("--write-plan and --apply-plan are mutually exclusive")
        if bool(args.apply_plan) != bool(args.expect_plan_hash):
            raise InstallError("--apply-plan and --expect-plan-hash are required together")
        plan = plan_install(
            args.source,
            args.target,
            args.client,
            args.config_path,
            allow_unpublished_local=args.allow_unpublished_local,
        )
        if args.apply_plan:
            confirmed = load_plan_document(args.apply_plan)
            if args.expect_plan_hash != confirmed["plan_hash"]:
                raise InstallError("--expect-plan-hash does not match the confirmed install plan")
            if confirmed != plan.document():
                raise InstallError("current install plan differs from the confirmed install plan")
            apply_plan(plan)
            payload = plan.to_dict(mode="applied")
        else:
            payload = plan.to_dict()
            if args.write_plan:
                write_plan(plan, args.write_plan)
                payload["plan_file"] = str(Path(args.write_plan).resolve())
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except (InstallError, ManifestSecurityError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

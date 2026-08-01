#!/usr/bin/env python3
"""Preview or apply a fail-closed Product Decision OS workspace installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, SchemaError

if __package__:
    from .manifest import ManifestSecurityError, tree_digest, verify
else:
    from manifest import ManifestSecurityError, tree_digest, verify


CANONICAL_ASSETS = ("schemas", "templates", "skills", "adapters", "integrations")
CLIENT_ROOTS = {
    "codex": PurePosixPath(".agents/skills"),
    "claude-code": PurePosixPath(".claude/skills"),
    "openclaw": PurePosixPath("skills"),
}


class InstallError(ValueError):
    """Raised when installation cannot proceed without crossing a trust boundary."""


@dataclass(frozen=True)
class PlannedFile:
    source: Path
    destination: Path
    display_source: str
    display_destination: str
    expected_sha256: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.display_source,
            "destination": self.display_destination,
            "action": "create",
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

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "plan_version": 1,
            "client": self.client,
            "release_tree_digest": self.tree_digest,
            "config_sha256": self.config_sha256,
            "files": [item.to_dict() for item in self.files],
        }

    @property
    def plan_hash(self) -> str:
        return _sha256_bytes(_canonical_json(self.canonical_payload()))

    def document(self) -> dict[str, Any]:
        return {**self.canonical_payload(), "plan_hash": self.plan_hash}

    def to_dict(self, *, mode: str = "preview") -> dict[str, Any]:
        return {
            "mode": mode,
            "source_root": str(self.source),
            "target_root": str(self.target),
            "release": self.release,
            "canonical_origin": self.canonical_origin,
            "publisher": self.publisher,
            **self.document(),
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


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


def _reject_tree_symlinks(root: Path, *, label: str) -> None:
    def walk_error(exc: OSError) -> None:
        raise InstallError(f"cannot traverse {label}: {exc}") from exc

    for current, directory_names, file_names in os.walk(root, followlinks=False, onerror=walk_error):
        current_path = Path(current)
        for name in (*directory_names, *file_names):
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


def _load_config(source: Path, config: Path, client: str) -> tuple[Path, bytes]:
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
    return config.resolve(strict=True), raw


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
        expected_wrapper_root = PurePosixPath("adapters") / client / "skills"
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

    active_root = target.joinpath(*allowed_root.parts)
    _reject_symlink_components(target, allowed_root, label=f"{client} client skill root")
    if active_root.exists():
        for candidate in sorted(active_root.glob("product-os-*")):
            relative = candidate.relative_to(target).as_posix()
            expected = {item.display_destination for item in planned}
            if candidate.is_symlink():
                raise InstallError(f"unexpected product-os wrapper symlink: {relative}")
            if any(item == relative or item.startswith(relative.rstrip("/") + "/") for item in expected):
                raise InstallError(f"product-os wrapper conflict; refusing to overwrite: {relative}")
            raise InstallError(f"unexpected product-os wrapper file or directory: {relative}")
    return planned


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

    _reject_tree_symlinks(source_path, label="source tree")
    _reject_tree_symlinks(target_path, label="target tree")

    manifest, manifest_entries = _load_manifest(source_path)
    origin = manifest.get("canonical_origin")
    if not isinstance(origin, str) or not origin:
        raise InstallError("source manifest has no canonical_origin")
    if origin == "unpublished" and not allow_unpublished_local:
        raise InstallError("unpublished source requires explicit --allow-unpublished-local")

    config, config_raw = _load_config(source_path, Path(config_path), client)

    planned: list[PlannedFile] = []
    for asset in CANONICAL_ASSETS:
        asset_root = source_path / asset
        if asset_root.is_symlink() or not asset_root.is_dir():
            raise InstallError(f"canonical asset directory is missing or unsafe: {asset}")
    for relative, entry in sorted(manifest_entries.items()):
        path = _relative_path(relative, label="source manifest entry path")
        if path.parts[0] not in CANONICAL_ASSETS:
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
        )
    )

    adapter, _ = _load_adapter(source_path, client)
    planned.extend(_projection_files(source_path, target_path, client, adapter, manifest_entries))
    planned.sort(key=lambda item: item.display_destination)
    destinations: set[Path] = set()
    for item in planned:
        if item.destination in destinations:
            raise InstallError(f"duplicate install destination: {item.display_destination}")
        destinations.add(item.destination)
        if item.destination.exists() or item.destination.is_symlink():
            raise InstallError(f"destination conflict; refusing to overwrite: {item.display_destination}")

    return InstallPlan(
        source=source_path,
        target=target_path,
        client=client,
        files=tuple(planned),
        product=str(manifest.get("product", "product-decision-os")),
        release=str(manifest.get("release", "unknown")),
        canonical_origin=origin,
        publisher=str(manifest.get("publisher", "unpublished")),
        tree_digest=str(manifest.get("tree_digest", "")),
        config_sha256=_sha256_bytes(config_raw),
    )


def _copy_exclusive(item: PlannedFile) -> None:
    source_fd = os.open(item.source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    destination_created = False
    try:
        destination_fd = os.open(
            item.destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o644,
        )
        destination_created = True
        digest = hashlib.sha256()
        try:
            while chunk := os.read(source_fd, 1024 * 1024):
                digest.update(chunk)
                view = memoryview(chunk)
                while view:
                    written = os.write(destination_fd, view)
                    view = view[written:]
        finally:
            os.close(destination_fd)
        if digest.hexdigest() != item.expected_sha256:
            raise InstallError(f"source changed after preview: {item.source}")
    except Exception:
        if destination_created:
            try:
                item.destination.unlink()
            except OSError:
                pass
        raise
    finally:
        os.close(source_fd)


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
    expected_keys = {
        "plan_version",
        "client",
        "release_tree_digest",
        "config_sha256",
        "files",
        "plan_hash",
    }
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
        }
        for item in plan.files
    ]
    entries.append(
        {
            "path": ".product-os/install-plan.json",
            "sha256": _sha256_bytes(install_plan_bytes),
            "size": len(install_plan_bytes),
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
        "parent_release": {
            "product": plan.product,
            "release": plan.release,
            "canonical_origin": plan.canonical_origin,
            "publisher": plan.publisher,
            "tree_digest": plan.tree_digest,
        },
    }


def apply_plan(plan: InstallPlan) -> None:
    _reject_tree_symlinks(plan.source, label="source tree")
    _reject_tree_symlinks(plan.target, label="target tree")
    allowed_root = CLIENT_ROOTS[plan.client]
    active_root = plan.target.joinpath(*allowed_root.parts)
    expected_wrappers = {
        item.destination
        for item in plan.files
        if item.display_destination.startswith(allowed_root.as_posix() + "/product-os-")
    }
    if active_root.exists():
        for candidate in active_root.glob("product-os-*"):
            if candidate in {path.parent for path in expected_wrappers}:
                raise InstallError(
                    f"product-os wrapper conflict; refusing to overwrite: {candidate.relative_to(plan.target)}"
                )
            raise InstallError(
                f"unexpected product-os wrapper file or directory: {candidate.relative_to(plan.target)}"
            )
    for item in plan.files:
        if item.destination.exists() or item.destination.is_symlink():
            raise InstallError(f"destination conflict; refusing to overwrite: {item.display_destination}")
    generated_destinations = (
        plan.target / ".product-os" / "install-plan.json",
        plan.target / ".product-os" / "installed-manifest.json",
    )
    for destination in generated_destinations:
        if destination.exists() or destination.is_symlink():
            raise InstallError(
                f"destination conflict; refusing to overwrite: {destination.relative_to(plan.target)}"
            )

    created_files: list[Path] = []
    created_directories: list[Path] = []
    try:
        for item in plan.files:
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
            _copy_exclusive(item)
            created_files.append(item.destination)
        install_plan_bytes = _plan_bytes(plan)
        install_plan_path = generated_destinations[0]
        _write_exclusive(install_plan_path, install_plan_bytes)
        created_files.append(install_plan_path)
        manifest_bytes = (
            json.dumps(_installed_manifest(plan, install_plan_bytes), indent=2, sort_keys=True).encode(
                "utf-8"
            )
            + b"\n"
        )
        installed_manifest_path = generated_destinations[1]
        _write_exclusive(installed_manifest_path, manifest_bytes)
        created_files.append(installed_manifest_path)
    except (InstallError, OSError):
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

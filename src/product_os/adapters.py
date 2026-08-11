"""Generate deterministic client adapter metadata from canonical workflows."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Iterable

import yaml


CLIENTS = ("codex", "claude-code", "openclaw")
HASH_RE = re.compile(r"(?m)^(\s*content_hash:\s*)[0-9a-f]{64}\s*$")
MARKER_RE = re.compile(
    r"(?m)^<!-- GENERATED: canonical_version=1\.0\.0 canonical_sha256=[0-9a-f]{64} -->$"
)
WRAPPER_SOURCE_RE = re.compile(
    r"wrapper_source:\s*adapters/(?:codex|claude-code|openclaw)/skills/"
)
WRAPPER_ROOT_RE = re.compile(r"(?m)^(\s*wrapper_root:\s*).+$")


class AdapterGenerationError(ValueError):
    """Raised when generated adapter inputs do not satisfy their contract."""


def canonical_source_files(root: Path) -> list[Path]:
    """The files an adapter projects: the skills and the capability contract.

    Provider descriptors are data behind those capabilities, not part of the projection, and a
    workspace installs only the ones it connected. Including them would make the freshness check
    fail for every workspace that did not take all of them.
    """
    return sorted(
        path
        for base in (root / "skills", root / "integrations")
        if base.is_dir()
        for path in base.rglob("*")
        if path.is_file() and "providers" not in path.relative_to(root).parts
    )


def canonical_source_digest(root: Path) -> str:
    """The one implementation. The validator and the tests call this rather than restating it."""
    digest = hashlib.sha256()
    for path in canonical_source_files(root):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _render_manifest(path: Path, root: Path, digest: str) -> str:
    text = path.read_text(encoding="utf-8")
    text, hash_count = HASH_RE.subn(rf"\g<1>{digest}", text)
    text, root_count = WRAPPER_ROOT_RE.subn(r"\g<1>../_shared/skills", text)
    text = WRAPPER_SOURCE_RE.sub("wrapper_source: adapters/_shared/skills/", text)
    if hash_count != 1 or root_count != 1:
        raise AdapterGenerationError(f"{path} lacks exactly one generated hash/root marker")

    manifest = yaml.safe_load(text)
    projections = manifest.get("projections") if isinstance(manifest, dict) else None
    if not isinstance(projections, list) or not projections:
        raise AdapterGenerationError(f"{path} has no projections")
    for projection in projections:
        wrapper = projection.get("wrapper_source") if isinstance(projection, dict) else None
        if not isinstance(wrapper, str) or not wrapper.startswith("adapters/_shared/skills/"):
            raise AdapterGenerationError(f"{path} contains a non-shared wrapper source")
        if not (root / wrapper).is_file():
            raise AdapterGenerationError(f"missing shared wrapper: {wrapper}")
    return text


def _render_instructions(path: Path, digest: str) -> str:
    text = path.read_text(encoding="utf-8")
    rendered, count = MARKER_RE.subn(
        f"<!-- GENERATED: canonical_version=1.0.0 canonical_sha256={digest} -->",
        text,
    )
    if count != 1:
        raise AdapterGenerationError(f"{path} lacks exactly one generated marker")
    return rendered


def generate_adapters(root: Path, *, check: bool = False) -> list[Path]:
    root = root.resolve()
    digest = canonical_source_digest(root)
    changed: list[Path] = []
    for client in CLIENTS:
        directory = root / "adapters" / client
        rendered = {
            directory / "manifest.yaml": _render_manifest(
                directory / "manifest.yaml", root, digest
            ),
            directory / "ADAPTER.md": _render_instructions(directory / "ADAPTER.md", digest),
        }
        for path, content in rendered.items():
            if path.read_text(encoding="utf-8") == content:
                continue
            changed.append(path)
            if not check:
                path.write_text(content, encoding="utf-8")
    return changed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        changed = generate_adapters(Path(args.root), check=args.check)
    except (AdapterGenerationError, OSError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 2
    if args.check and changed:
        print("Generated adapters are stale:")
        for path in changed:
            print(path)
        return 1
    print(f"{'Would update' if args.check else 'Updated'} {len(changed)} adapter files.")
    return 0


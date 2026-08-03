#!/usr/bin/env python3
"""Build or verify the deterministic Product OS release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


IGNORED_PARTS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
IGNORED_NAMES = {"manifest.json", ".DS_Store"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
RELEASE_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")


class ManifestSecurityError(ValueError):
    """Raised when a distribution tree crosses a filesystem trust boundary."""


def _is_ignored_relative(path: Path) -> bool:
    return (
        path.name in IGNORED_NAMES
        or path.suffix in IGNORED_SUFFIXES
        or any(part in IGNORED_PARTS or part.endswith(".egg-info") for part in path.parts)
    )


def _secure_root(root: Path) -> Path:
    if root.is_symlink():
        raise ManifestSecurityError(f"distribution root must not be a symlink: {root}")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise ManifestSecurityError(f"distribution root is unavailable: {exc}") from exc
    if not resolved.is_dir():
        raise ManifestSecurityError(f"distribution root is not a directory: {root}")
    return resolved


def distributed_files(root: Path) -> list[Path]:
    resolved_root = _secure_root(root)
    files: list[Path] = []
    def walk_error(exc: OSError) -> None:
        raise ManifestSecurityError(f"cannot traverse distribution: {exc}") from exc

    for current, directory_names, file_names in os.walk(root, followlinks=False, onerror=walk_error):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in directory_names:
            candidate = current_path / name
            relative = candidate.relative_to(root)
            if _is_ignored_relative(relative):
                continue
            if candidate.is_symlink():
                raise ManifestSecurityError(f"symlink is not allowed in distribution: {relative.as_posix()}")
            resolved = candidate.resolve(strict=True)
            if not resolved.is_relative_to(resolved_root):
                raise ManifestSecurityError(f"path resolves outside distribution root: {relative.as_posix()}")
            kept_directories.append(name)
        directory_names[:] = kept_directories

        for name in file_names:
            candidate = current_path / name
            relative = candidate.relative_to(root)
            if _is_ignored_relative(relative):
                continue
            if candidate.is_symlink():
                raise ManifestSecurityError(f"symlink is not allowed in distribution: {relative.as_posix()}")
            resolved = candidate.resolve(strict=True)
            if not resolved.is_relative_to(resolved_root):
                raise ManifestSecurityError(f"path resolves outside distribution root: {relative.as_posix()}")
            if not candidate.is_file():
                raise ManifestSecurityError(f"non-regular distributed file: {relative.as_posix()}")
            files.append(candidate)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_digest(entries: Iterable[dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for entry in entries:
        digest.update(str(entry["path"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(entry["sha256"]).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _release_metadata(
    canonical_origin: str, publisher: str, release: str
) -> tuple[str, str, str]:
    if (
        not isinstance(canonical_origin, str)
        or not canonical_origin
        or len(canonical_origin) > 500
        or any(ord(char) < 32 for char in canonical_origin)
    ):
        raise ManifestSecurityError(
            "canonical_origin must be 'unpublished' or an absolute https repository URL"
        )
    if canonical_origin != "unpublished":
        parsed = urlparse(canonical_origin)
        if parsed.scheme != "https" or not parsed.netloc or not parsed.path.strip("/"):
            raise ManifestSecurityError(
                "canonical_origin must be 'unpublished' or an absolute https repository URL"
            )
        if parsed.params or parsed.query or parsed.fragment:
            raise ManifestSecurityError("canonical_origin must not contain params, query, or fragment")
    if (
        not isinstance(publisher, str)
        or not publisher.strip()
        or len(publisher) > 200
        or any(ord(char) < 32 for char in publisher)
    ):
        raise ManifestSecurityError("publisher must be a non-empty printable value up to 200 characters")
    if not isinstance(release, str) or not RELEASE_RE.fullmatch(release):
        raise ManifestSecurityError("release must be a semantic version such as 0.1.0")
    return canonical_origin, publisher.strip(), release


def build(
    root: Path,
    *,
    canonical_origin: str = "unpublished",
    publisher: str = "unpublished",
    release: str = "0.1.0",
) -> dict[str, object]:
    canonical_origin, publisher, release = _release_metadata(
        canonical_origin, publisher, release
    )
    if (root / "manifest.json").is_symlink():
        raise ManifestSecurityError("manifest.json must not be a symlink")
    entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256(path),
            "size": path.stat().st_size,
        }
        for path in distributed_files(root)
    ]
    return {
        "manifest_version": 1,
        "product": "product-decision-os",
        "release": release,
        "canonical_origin": canonical_origin,
        "publisher": publisher,
        "hash_algorithm": "sha256",
        "tree_digest": tree_digest(entries),
        "files": entries,
    }


def write_manifest(
    root: Path,
    *,
    canonical_origin: str = "unpublished",
    publisher: str = "unpublished",
    release: str = "0.1.0",
) -> Path:
    destination = root / "manifest.json"
    if destination.is_symlink():
        raise ManifestSecurityError("manifest.json must not be a symlink")
    destination.write_text(
        json.dumps(
            build(
                root,
                canonical_origin=canonical_origin,
                publisher=publisher,
                release=release,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return destination


def verify(root: Path) -> list[str]:
    try:
        _secure_root(root)
    except ManifestSecurityError as exc:
        return [str(exc)]
    manifest_path = root / "manifest.json"
    if manifest_path.is_symlink():
        return ["manifest.json must not be a symlink"]
    if not manifest_path.is_file():
        return ["manifest.json is missing; obtain a complete immutable release"]
    try:
        expected = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"manifest.json cannot be read: {exc}"]
    if not isinstance(expected, dict):
        return ["manifest.json root must be an object"]

    try:
        canonical_origin, publisher, release = _release_metadata(
            expected.get("canonical_origin"),
            expected.get("publisher"),
            expected.get("release"),
        )
        actual = build(
            root,
            canonical_origin=canonical_origin,
            publisher=publisher,
            release=release,
        )
    except (ManifestSecurityError, OSError, TypeError) as exc:
        return [str(exc)]
    problems: list[str] = []
    if expected.get("manifest_version") != 1:
        problems.append("unsupported manifest_version; expected 1")
    if expected.get("product") != "product-decision-os":
        problems.append("manifest product must be product-decision-os")
    if expected.get("hash_algorithm") != "sha256":
        problems.append("manifest hash_algorithm must be sha256")
    entries = expected.get("files")
    if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
        return problems + ["manifest files must be an array of objects"]
    if entries != actual["files"]:
        try:
            expected_files = {entry["path"]: entry for entry in entries}
        except (KeyError, TypeError):
            return problems + ["manifest file entry has no valid path"]
        actual_files = {entry["path"]: entry for entry in actual["files"]}
        for path in sorted(expected_files.keys() - actual_files.keys()):
            problems.append(f"missing distributed file: {path}")
        for path in sorted(actual_files.keys() - expected_files.keys()):
            problems.append(f"unexpected distributed file: {path}")
        for path in sorted(expected_files.keys() & actual_files.keys()):
            if expected_files[path] != actual_files[path]:
                problems.append(f"content or size mismatch: {path}")
    if expected.get("tree_digest") != actual["tree_digest"]:
        problems.append("release tree_digest mismatch")
    return problems


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--canonical-origin", default="unpublished")
    parser.add_argument("--publisher", default="unpublished")
    parser.add_argument("--release", default="0.1.0")
    args = parser.parse_args(argv)
    root = Path(args.root)
    if args.command == "build":
        try:
            path = write_manifest(
                root,
                canonical_origin=args.canonical_origin,
                publisher=args.publisher,
                release=args.release,
            )
        except (ManifestSecurityError, OSError) as exc:
            print(f"ERROR: {exc}")
            return 1
        print(path)
        return 0
    problems = verify(root)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        return 1
    print("manifest verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

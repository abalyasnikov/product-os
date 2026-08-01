from __future__ import annotations

from pathlib import Path

import pytest

from scripts.manifest import ManifestSecurityError, build, verify, write_manifest


def test_manifest_builder_rejects_file_symlink(tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    root = tmp_path / "release"
    root.mkdir()
    (root / "linked.txt").symlink_to(outside)

    with pytest.raises(ManifestSecurityError, match="symlink"):
        build(root)


def test_manifest_builder_rejects_directory_symlink(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "payload.txt").write_text("outside\n", encoding="utf-8")
    root = tmp_path / "release"
    root.mkdir()
    (root / "linked-directory").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ManifestSecurityError, match="symlink"):
        build(root)


def test_manifest_verifier_rejects_symlink_substitution(tmp_path: Path) -> None:
    root = tmp_path / "release"
    root.mkdir()
    distributed = root / "asset.txt"
    distributed.write_text("trusted\n", encoding="utf-8")
    write_manifest(root)
    outside = tmp_path / "outside.txt"
    outside.write_text("trusted\n", encoding="utf-8")
    distributed.unlink()
    distributed.symlink_to(outside)

    problems = verify(root)
    assert any("symlink" in problem for problem in problems)


def test_manifest_rejects_symlink_root(tmp_path: Path) -> None:
    root = tmp_path / "release"
    root.mkdir()
    (root / "asset.txt").write_text("trusted\n", encoding="utf-8")
    write_manifest(root)
    linked_root = tmp_path / "linked-release"
    linked_root.symlink_to(root, target_is_directory=True)

    assert any("root must not be a symlink" in problem for problem in verify(linked_root))


def test_manifest_builder_rejects_manifest_symlink(tmp_path: Path) -> None:
    root = tmp_path / "release"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    (root / "manifest.json").symlink_to(outside)

    with pytest.raises(ManifestSecurityError, match="manifest.json"):
        build(root)

from __future__ import annotations

import json
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from product_decision_os.installer import InstallError, main as install_main, plan_install, write_plan
from product_decision_os.manifest import build, main as manifest_main, verify, write_manifest


def test_release_manifest_matches_repository(repo_root: Path) -> None:
    assert (repo_root / "manifest.json").is_file()
    assert verify(repo_root) == []


def test_manifest_detects_changed_and_unexpected_files(tmp_path: Path) -> None:
    root = tmp_path / "release"
    root.mkdir()
    (root / "README.md").write_text("original\n", encoding="utf-8")
    write_manifest(root)
    assert verify(root) == []

    (root / "README.md").write_text("changed\n", encoding="utf-8")
    assert any("content or size mismatch" in problem for problem in verify(root))

    (root / "README.md").write_text("original\n", encoding="utf-8")
    (root / "unexpected.txt").write_text("surprise\n", encoding="utf-8")
    assert any("unexpected distributed file" in problem for problem in verify(root))


def test_manifest_is_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "release"
    root.mkdir()
    (root / "b.txt").write_text("b", encoding="utf-8")
    (root / "a.txt").write_text("a", encoding="utf-8")
    first = build(root)
    second = build(root)
    assert first == second
    assert [entry["path"] for entry in first["files"]] == ["a.txt", "b.txt"]


def test_manifest_preserves_validated_release_metadata_during_verify(tmp_path: Path) -> None:
    root = tmp_path / "release"
    root.mkdir()
    (root / "README.md").write_text("release\n", encoding="utf-8")
    write_manifest(
        root,
        canonical_origin="https://github.com/example/product-decision-os",
        publisher="Example Maintainers",
        release="1.2.3",
    )
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["canonical_origin"] == "https://github.com/example/product-decision-os"
    assert manifest["publisher"] == "Example Maintainers"
    assert manifest["release"] == "1.2.3"
    assert verify(root) == []


def test_manifest_build_cli_accepts_release_identity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "release"
    root.mkdir()
    (root / "README.md").write_text("release\n", encoding="utf-8")
    assert (
        manifest_main(
            [
                "build",
                str(root),
                "--canonical-origin",
                "https://github.com/example/product-decision-os",
                "--publisher",
                "Example Maintainers",
                "--release",
                "2.0.0",
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == str(root / "manifest.json")
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["publisher"] == "Example Maintainers"
    assert verify(root) == []


@pytest.mark.parametrize(
    ("origin", "publisher", "release"),
    [
        ("main", "Example", "1.2.3"),
        ("https://github.com/example/repo?ref=main", "Example", "1.2.3"),
        ("unpublished", "", "1.2.3"),
        ("unpublished", "Example", "latest"),
    ],
)
def test_manifest_rejects_invalid_release_metadata(
    tmp_path: Path, origin: str, publisher: str, release: str
) -> None:
    root = tmp_path / "release"
    root.mkdir()
    with pytest.raises(ValueError):
        build(root, canonical_origin=origin, publisher=publisher, release=release)


def test_readme_references_shipped_diagram(repo_root: Path) -> None:
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert "docs/assets/product-loop.png" in readme
    assert (repo_root / "docs/assets/product-loop.png").stat().st_size > 10_000


def test_agent_instruction_entrypoints_are_single_source(repo_root: Path) -> None:
    assert (repo_root / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "Canonical skills: `skills/`" in agents
    assert "Generated client adapters: `adapters/`" in agents
    install = (repo_root / "INSTALL.md").read_text(encoding="utf-8").lower()
    assert "v1 does not create repositories" in install
    assert "do not copy files manually" in install
    assert "copy these canonical directories" not in install


def test_repository_markdown_has_no_broken_relative_links(repo_root: Path) -> None:
    missing: list[str] = []
    for path in repo_root.rglob("*.md"):
        if any(part in {".git", ".venv", "build", "dist"} for part in path.parts):
            continue
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            relative_target = target.split("#", 1)[0]
            if relative_target and not (path.parent / relative_target).resolve().exists():
                missing.append(f"{path.relative_to(repo_root)} -> {relative_target}")
    assert missing == []


def test_solo_walkthrough_config_matches_canonical_schema(repo_root: Path) -> None:
    walkthrough = (repo_root / "docs/getting-started.md").read_text(encoding="utf-8")
    match = re.search(r"```yaml\n(.*?)\n```", walkthrough, re.DOTALL)
    assert match is not None
    config = yaml.safe_load(match.group(1))
    schema = json.loads((repo_root / "schemas/config.schema.json").read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(config)) == []


def _relocated_release(repo_root: Path, destination: Path) -> Path:
    shutil.copytree(
        repo_root,
        destination,
        ignore=shutil.ignore_patterns(
            ".git", ".pytest_cache", ".venv", "__pycache__", "*.egg-info", "build", "dist"
        ),
    )
    write_manifest(destination)
    assert verify(destination) == []
    return destination


@pytest.mark.parametrize(
    ("client", "wrapper_root"),
    [
        ("codex", ".agents/skills"),
        ("claude-code", ".claude/skills"),
        ("openclaw", "skills"),
    ],
)
def test_real_release_clean_install_matrix_and_installed_manifest(
    repo_root: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    client: str,
    wrapper_root: str,
) -> None:
    source = _relocated_release(repo_root, tmp_path / "relocated-source")
    target = tmp_path / "private-workspace"
    target.mkdir()
    subprocess.run(["git", "init", "-q", str(target)], check=True)
    config = yaml.safe_load((source / "tests/fixtures/config/valid-solo.yaml").read_text())
    config["selected_client"] = client
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    plan_path = tmp_path / "install-plan.json"

    preview_args = [
        str(source),
        str(target),
        "--client",
        client,
        "--config",
        str(config_path),
        "--allow-unpublished-local",
        "--write-plan",
        str(plan_path),
    ]
    assert install_main(preview_args) == 0
    preview = json.loads(capsys.readouterr().out)
    assert install_main(
        [
            str(source),
            str(target),
            "--client",
            client,
            "--config",
            str(config_path),
            "--allow-unpublished-local",
            "--apply-plan",
            str(plan_path),
            "--expect-plan-hash",
            preview["plan_hash"],
        ]
    ) == 0
    applied = json.loads(capsys.readouterr().out)
    assert applied["mode"] == "applied"

    active_wrappers = sorted((target / wrapper_root).glob("product-os-*/SKILL.md"))
    assert len(active_wrappers) == 9
    assert (target / ".product-os/release-manifest.json").read_bytes() == (
        source / "manifest.json"
    ).read_bytes()
    assert not (target / ".product-os/manifest.json").exists()

    installed_path = target / ".product-os/installed-manifest.json"
    installed = json.loads(installed_path.read_text())
    assert installed["manifest_kind"] == "installed_workspace"
    assert installed["client"] == client
    assert installed["install_plan_sha256"] == preview["plan_hash"]
    assert installed["parent_release"]["tree_digest"] == json.loads(
        (source / "manifest.json").read_text()
    )["tree_digest"]
    paths = [entry["path"] for entry in installed["files"]]
    assert paths == sorted(paths)
    assert ".product-os/install-plan.json" in paths
    assert ".product-os/installed-manifest.json" not in paths
    for entry in installed["files"]:
        payload = (target / entry["path"]).read_bytes()
        assert len(payload) == entry["size"]
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"]


def test_plan_hash_is_stable_across_source_relocation(repo_root: Path, tmp_path: Path) -> None:
    first = _relocated_release(repo_root, tmp_path / "first")
    second = _relocated_release(repo_root, tmp_path / "second")
    config = tmp_path / "config.yaml"
    config.write_bytes((first / "tests/fixtures/config/valid-solo.yaml").read_bytes())
    first_target = tmp_path / "first-target"
    second_target = tmp_path / "second-target"
    first_target.mkdir()
    second_target.mkdir()
    first_plan = plan_install(first, first_target, "claude-code", config, allow_unpublished_local=True)
    second_plan = plan_install(second, second_target, "claude-code", config, allow_unpublished_local=True)
    assert first_plan.plan_hash == second_plan.plan_hash
    assert first_plan.canonical_payload() == second_plan.canonical_payload()


def test_real_release_rejects_config_mismatch_and_confirmed_plan_drift(
    repo_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = _relocated_release(repo_root, tmp_path / "source")
    target = tmp_path / "target"
    target.mkdir()
    subprocess.run(["git", "init", "-q", str(target)], check=True)
    config_path = tmp_path / "config.yaml"
    config_path.write_bytes((source / "tests/fixtures/config/valid-solo.yaml").read_bytes())
    with pytest.raises(InstallError, match="selected_client.*does not match"):
        plan_install(source, target, "codex", config_path, allow_unpublished_local=True)

    config = yaml.safe_load(config_path.read_text())
    config["selected_client"] = "codex"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    plan = plan_install(source, target, "codex", config_path, allow_unpublished_local=True)
    plan_path = tmp_path / "plan.json"
    write_plan(plan, plan_path)
    common = [
        str(source),
        str(target),
        "--client",
        "codex",
        "--config",
        str(config_path),
        "--allow-unpublished-local",
        "--apply-plan",
        str(plan_path),
    ]
    assert install_main([*common, "--expect-plan-hash", "f" * 64]) == 1
    assert "does not match" in capsys.readouterr().out
    config_path.write_text(config_path.read_text() + "# changed after confirmation\n", encoding="utf-8")
    assert install_main([*common, "--expect-plan-hash", plan.plan_hash]) == 1
    assert "differs from the confirmed" in capsys.readouterr().out
    assert not (target / ".product-os").exists()

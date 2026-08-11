from __future__ import annotations

# The route-only wrappers a client install must place, derived from the canonical skill set.
EXPECTED_WRAPPERS = (
    "product-os-setup",
    "product-os-discovery",
    "product-os-initiative",
    "product-os-prd",
    "product-os-decision-queue",
    "product-os-outcome-review",
    "product-os-product-update",
)

import json
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from product_os.installer import InstallError, main as install_main, plan_install, write_plan
from product_os.validator import markdown_link_targets
from product_os.manifest import build, main as manifest_main, verify, write_manifest


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


def test_manifest_ignores_working_files(tmp_path: Path) -> None:
    """`uv run` drops uv.lock into the checkout and drafts live in docs/plans/.

    Neither is distributed behavior, so neither may fail provenance verification:
    before this, a maintainer's plan draft — or the demo's own `uv run` — turned
    the whole e2e suite red with an "unexpected distributed file".
    """
    root = tmp_path / "release"
    root.mkdir()
    (root / "README.md").write_text("release\n", encoding="utf-8")
    write_manifest(root)
    assert verify(root) == []

    (root / "uv.lock").write_text("lock\n", encoding="utf-8")
    plans = root / "docs" / "plans"
    plans.mkdir(parents=True)
    (plans / "draft.md").write_text("plan\n", encoding="utf-8")
    assert verify(root) == []


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
        canonical_origin="https://github.com/example/product-os",
        publisher="Example Maintainers",
        release="1.2.3",
    )
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["canonical_origin"] == "https://github.com/example/product-os"
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
                "https://github.com/example/product-os",
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


def test_readme_renders_the_loop_and_closes_it(repo_root: Path) -> None:
    """The README must draw the loop, and the drawing must stay true.

    This replaced a check that a diagram image existed and exceeded a byte
    count, which a stale export passes just as easily as a correct one. A
    Mermaid block is rendered by GitHub from source, so the diagram cannot
    silently drift away from the model it depicts.
    """
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert "```mermaid" in readme

    diagram = readme.split("```mermaid", 1)[1].split("```", 1)[0]
    for node in ("Strategy context", "Evidence", "Opportunity", "Outcome Contract"):
        assert node in diagram, f"loop diagram is missing {node!r}"

    # The point of the product is that the loop returns; a diagram that ends at
    # delivery would describe a different system.
    assert "Learning" in diagram
    assert re.search(r"(?m)^\s*L\s*-->\s*E\s*$", diagram), "loop must close back to evidence"


def test_agent_instruction_entrypoints_are_single_source(repo_root: Path) -> None:
    assert (repo_root / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "Canonical skills: `skills/`" in agents
    assert "Generated client adapters: `adapters/`" in agents
    install = (repo_root / "INSTALL.md").read_text(encoding="utf-8").lower()
    assert "v1 does not create repositories" in install
    assert "do not copy files manually" in install
    assert "copy these canonical directories" not in install


def test_manifest_verification_needs_no_third_party_dependency(repo_root: Path) -> None:
    """Provenance must be checkable before anything is installed from the source.

    CI verifies the release manifest as its first step, deliberately ahead of
    `pip install`: you check what a source claims to be before you run its code.
    That only works while `product_os.manifest` stays on the standard library,
    and it is easy to break from a distance — an eager re-export in the package
    `__init__` once pulled PyYAML in transitively and broke this on a clean
    runner while every developer machine stayed green.
    """
    probe = (
        "import sys; sys.path.insert(0, 'src');"
        "import product_os.manifest;"
        "leaked = sorted({'yaml', 'jsonschema'} & set(sys.modules));"
        "print(','.join(leaked))"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env={"PATH": os.environ.get("PATH", ""), "PYTHONNOUSERSITE": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", (
        f"product_os.manifest transitively imported {result.stdout.strip()}; "
        "manifest verification must run before dependencies are installed"
    )


PRD_SECTION_ORDER = [
    "Problem",
    "Evidence",
    "JTBD",
    "Current and desired journey",
    "Scope",
    "GTM hypothesis",
    "Risks and dependencies",
    "Open questions",
    "Outcome Contract",
    "Delivery",
]

INITIATIVE_SECTION_ORDER = [
    "Vision",
    "Why this matters",
    "Evidence and confidence",
    "Shared outcome",
    "Child PRDs",
    "Sequencing and dependencies",
    "GTM hypothesis",
    "Risks and open questions",
    "Outcome Contract",
]


def test_readable_artifacts_keep_the_machine_block_out_of_the_reading_path(
    repo_root: Path,
) -> None:
    """Every template, example, and golden file must order sections the same way.

    The validator only checks that required sections exist, so order can drift
    silently across a dozen documents. It matters most for the Outcome Contract:
    its payload is machine-readable YAML, and mid-document it interrupts the
    product argument a reviewer is actually reading. Optional sections may appear
    between the required ones, so this asserts relative order, not adjacency.
    """
    documents = sorted(
        path
        for path in repo_root.rglob("*.md")
        if ".git" not in path.parts
        and "_shared" not in path.parts
        and "```yaml product-os:outcome" in path.read_text(encoding="utf-8")
    )
    assert documents, "expected artifacts carrying an Outcome Contract"

    for path in documents:
        headings = re.findall(r"(?m)^## (.+?)\s*$", path.read_text(encoding="utf-8"))
        expected = (
            INITIATIVE_SECTION_ORDER if "Vision" in headings else PRD_SECTION_ORDER
        )
        required = [h for h in headings if h in expected]
        rel = path.relative_to(repo_root)
        assert required == expected, f"{rel} orders sections as {required}"


def test_repository_markdown_has_no_broken_relative_links(repo_root: Path) -> None:
    missing: list[str] = []
    for path in repo_root.rglob("*.md"):
        if any(part in {".git", ".venv", "build", "dist"} for part in path.parts):
            continue
        for target in markdown_link_targets(path.read_text(encoding="utf-8")):
            if target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            relative_target = target.split("#", 1)[0]
            if relative_target and not (path.parent / relative_target).resolve().exists():
                missing.append(f"{path.relative_to(repo_root)} -> {relative_target}")
    assert missing == []


def test_solo_walkthrough_config_matches_canonical_schema(repo_root: Path) -> None:
    """The workspace config the docs hand a reader must satisfy the shipped schema."""
    template = (repo_root / "templates/config.yaml").read_text(encoding="utf-8")
    config = yaml.safe_load(template)
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
    assert len(active_wrappers) == len(EXPECTED_WRAPPERS)
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

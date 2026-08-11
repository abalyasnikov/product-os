from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml
import product_os.installer as installer_module

from product_os.installer import (
    InstallError,
    apply_plan,
    load_plan_document,
    main,
    plan_install,
    write_plan,
)
from product_os.manifest import write_manifest


@pytest.fixture
def install_source(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    for asset in ("schemas", "templates", "skills", "adapters", "integrations"):
        (source / asset).mkdir()
    (source / "schemas/common.schema.json").write_text("{}\n", encoding="utf-8")
    (source / "schemas/config.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["schema_version", "selected_client"],
                "properties": {
                    "schema_version": {"const": 1},
                    "selected_client": {"enum": ["codex", "claude-code", "openclaw"]},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (source / "templates/signal.md").write_text("# Signal\n", encoding="utf-8")
    (source / "integrations/capabilities.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    (source / "skills/setup").mkdir()
    (source / "skills/setup/SKILL.md").write_text("# Canonical setup\n", encoding="utf-8")
    wrapper = source / "adapters/_shared/skills/product-os-setup"
    wrapper.mkdir(parents=True)
    (wrapper / "SKILL.md").write_text("# Wrapper\n", encoding="utf-8")
    (source / "adapters/codex").mkdir()
    adapter = {
        "adapter_schema_version": 1,
        "generated": True,
        "client": "codex",
        "projection": {"client_skill_location": ".agents/skills"},
        "projections": [
            {
                "name": "product-os-setup",
                "canonical_source": ".product-os/skills/setup/SKILL.md",
                "wrapper_source": "adapters/_shared/skills/product-os-setup/SKILL.md",
                "destination": ".agents/skills/product-os-setup/SKILL.md",
            }
        ],
    }
    (source / "adapters/codex/manifest.yaml").write_text(
        yaml.safe_dump(adapter, sort_keys=False), encoding="utf-8"
    )
    write_manifest(source)
    config = tmp_path / "config.yaml"
    config.write_text("schema_version: 1\nselected_client: codex\n", encoding="utf-8")
    return source, config


def _rewrite_projection(source: Path, field: str, value: str) -> None:
    path = source / "adapters/codex/manifest.yaml"
    adapter = yaml.safe_load(path.read_text(encoding="utf-8"))
    adapter["projections"][0][field] = value
    path.write_text(yaml.safe_dump(adapter, sort_keys=False), encoding="utf-8")
    write_manifest(source)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _install_and_commit(source: Path, config: Path, target: Path) -> None:
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    apply_plan(plan)
    _git(target, "init", "-b", "main")
    _git(target, "config", "user.email", "test@example.com")
    _git(target, "config", "user.name", "Test")
    _git(target, "add", ".")
    _git(target, "commit", "-m", "chore: install Product OS 0.1.0")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("destination", "/tmp/product-os-setup/SKILL.md"),
        ("destination", ".agents/skills/../../escape/SKILL.md"),
        ("wrapper_source", "../outside/SKILL.md"),
        ("canonical_source", ".product-os/skills/../../outside/SKILL.md"),
    ],
)
def test_projection_paths_reject_absolute_and_parent_traversal(
    install_source: tuple[Path, Path], tmp_path: Path, field: str, value: str
) -> None:
    source, config = install_source
    _rewrite_projection(source, field, value)

    with pytest.raises(InstallError, match="relative|contain no"):
        plan_install(source, tmp_path / "target", "codex", config, allow_unpublished_local=True)


def test_unpublished_source_requires_explicit_gate(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source

    with pytest.raises(InstallError, match="--allow-unpublished-local"):
        plan_install(source, tmp_path / "target", "codex", config)

    assert plan_install(
        source, tmp_path / "target", "codex", config, allow_unpublished_local=True
    ).canonical_origin == "unpublished"


def test_preview_is_read_only_and_apply_copies_exact_files(
    install_source: tuple[Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    plan_path = tmp_path / "plan.json"

    exit_code = main(
        [
            str(source),
            str(target),
            "--client",
            "codex",
            "--config",
            str(config),
            "--allow-unpublished-local",
            "--write-plan",
            str(plan_path),
        ]
    )
    preview = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert preview["mode"] == "preview"
    assert preview["plan_hash"] == json.loads(plan_path.read_text())["plan_hash"]
    assert preview["plan_version"] == 2
    assert preview["baseline_tree_digest"] is None
    assert all(
        set(item) == {"source", "destination", "action", "ownership", "sha256", "size"}
        for item in preview["files"]
    )
    assert list(target.rglob("*")) == []

    exit_code = main(
        [
            str(source),
            str(target),
            "--client",
            "codex",
            "--config",
            str(config),
            "--allow-unpublished-local",
            "--apply-plan",
            str(plan_path),
            "--expect-plan-hash",
            preview["plan_hash"],
        ]
    )
    applied = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert applied["mode"] == "applied"
    assert (target / ".product-os/schemas/common.schema.json").read_text() == "{}\n"
    assert (target / ".product-os/config.yaml").read_text() == "schema_version: 1\nselected_client: codex\n"
    assert (target / ".agents/skills/product-os-setup/SKILL.md").read_text() == "# Wrapper\n"
    assert not (target / ".product-os/manifest.json").exists()
    assert (target / ".product-os/release-manifest.json").is_file()
    installed = json.loads((target / ".product-os/installed-manifest.json").read_text())
    assert installed["manifest_kind"] == "installed_workspace"
    assert installed["install_plan_sha256"] == preview["plan_hash"]
    installed_paths = {entry["path"] for entry in installed["files"]}
    assert ".product-os/install-plan.json" in installed_paths
    assert ".product-os/release-manifest.json" in installed_paths
    assert ".agents/skills/product-os-setup/SKILL.md" in installed_paths
    assert ".product-os/installed-manifest.json" not in installed_paths


def test_install_preserves_existing_workspace_context_and_reports_snippet(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    existing = target / "AGENTS.md"
    existing.write_text("user instructions\n", encoding="utf-8")
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    assert "AGENTS.md" not in {item.display_destination for item in plan.files}
    assert plan.to_dict()["skipped_context"] == [
        {
            "path": "AGENTS.md",
            "copy_paste_snippet": "Read `README.md` and route Product OS work through `.product-os/skills/`.",
        }
    ]
    apply_plan(plan)
    assert existing.read_text() == "user instructions\n"


def test_config_must_validate_and_match_selected_client(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    config.write_text("schema_version: 1\nselected_client: claude-code\n", encoding="utf-8")
    with pytest.raises(InstallError, match="selected_client.*does not match"):
        plan_install(source, tmp_path / "target", "codex", config, allow_unpublished_local=True)

    config.write_text("schema_version: 2\nselected_client: codex\n", encoding="utf-8")
    with pytest.raises(InstallError, match="does not match schema"):
        plan_install(source, tmp_path / "target", "codex", config, allow_unpublished_local=True)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("schema_version: 1\nselected_client: codex\nselected_client: codex\n", "duplicate key"),
        ("schema_version: &version 1\nselected_client: codex\ncopy: *version\n", "YAML aliases"),
    ],
)
def test_config_strict_loader_rejects_ambiguous_yaml(
    install_source: tuple[Path, Path], tmp_path: Path, content: str, message: str
) -> None:
    source, config = install_source
    config.write_text(content, encoding="utf-8")
    with pytest.raises(InstallError, match=message):
        plan_install(source, tmp_path / "target", "codex", config, allow_unpublished_local=True)


def test_apply_cli_rejects_wrong_expected_hash_and_plan_drift(
    install_source: tuple[Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    plan_path = tmp_path / "plan.json"
    preview_plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    write_plan(preview_plan, plan_path)
    common = [
        str(source),
        str(target),
        "--client",
        "codex",
        "--config",
        str(config),
        "--allow-unpublished-local",
        "--apply-plan",
        str(plan_path),
    ]
    assert main([*common, "--expect-plan-hash", "0" * 64]) == 1
    assert "does not match" in capsys.readouterr().out
    assert list(target.rglob("*")) == []

    config.write_text("schema_version: 1\nselected_client: codex\n# drift\n", encoding="utf-8")
    assert main([*common, "--expect-plan-hash", preview_plan.plan_hash]) == 1
    assert "differs from the confirmed" in capsys.readouterr().out
    assert list(target.rglob("*")) == []


def test_tampered_plan_payload_is_rejected(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    plan = plan_install(source, tmp_path / "target", "codex", config, allow_unpublished_local=True)
    document = plan.document()
    document["files"][0]["destination"] = "escape"
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(InstallError, match="hash does not match"):
        load_plan_document(path)


def test_existing_destination_is_never_overwritten(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    conflict = target / ".product-os/schemas/common.schema.json"
    conflict.parent.mkdir(parents=True)
    conflict.write_text("user-owned\n", encoding="utf-8")

    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    assert next(
        item for item in plan.files if item.display_destination == ".product-os/schemas/common.schema.json"
    ).action == "conflict"
    with pytest.raises(InstallError, match="conflicts halt"):
        apply_plan(plan)
    assert conflict.read_text() == "user-owned\n"


def test_expected_and_unexpected_product_os_wrappers_are_rejected(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    unexpected = target / ".agents/skills/product-os-evil/SKILL.md"
    unexpected.parent.mkdir(parents=True)
    unexpected.write_text("malicious\n", encoding="utf-8")

    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    assert any(item.action == "conflict" and "product-os-evil" in item.display_destination for item in plan.files)

    unexpected.parent.rename(target / ".agents/skills/not-product-os")
    expected = target / ".agents/skills/product-os-setup/SKILL.md"
    expected.parent.mkdir(parents=True)
    expected.write_text("existing\n", encoding="utf-8")
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    assert any(item.action == "conflict" and item.display_destination == expected.relative_to(target).as_posix() for item in plan.files)
    assert expected.read_text() == "existing\n"


def test_target_symlink_component_is_rejected(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    outside = tmp_path / "outside"
    outside.mkdir()
    (target / ".agents").symlink_to(outside, target_is_directory=True)

    with pytest.raises(InstallError, match="contains a symlink"):
        plan_install(source, target, "codex", config, allow_unpublished_local=True)
    assert list(outside.iterdir()) == []


def test_unrelated_target_symlink_is_rejected(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (target / "unrelated-link").symlink_to(outside)

    with pytest.raises(InstallError, match="target tree contains a symlink"):
        plan_install(source, target, "codex", config, allow_unpublished_local=True)


@pytest.mark.parametrize(
    "ignored_directory",
    [
        ".git",
        ".pytest_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "product_os.egg-info",
    ],
)
def test_source_symlinks_in_non_distributed_directories_are_skipped(
    install_source: tuple[Path, Path],
    tmp_path: Path,
    ignored_directory: str,
) -> None:
    source, config = install_source
    local_directory = source / ignored_directory / "bin"
    local_directory.mkdir(parents=True)
    (local_directory / "python3").symlink_to(tmp_path / "local-runtime")

    plan = plan_install(
        source,
        tmp_path / "target",
        "codex",
        config,
        allow_unpublished_local=True,
    )

    assert all(ignored_directory not in item.display_source for item in plan.files)


def test_source_symlink_in_distributed_tree_is_rejected(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    (source / "templates/linked.md").symlink_to(outside)

    with pytest.raises(InstallError, match="source tree contains a symlink"):
        plan_install(
            source,
            tmp_path / "target",
            "codex",
            config,
            allow_unpublished_local=True,
        )


def test_apply_refuses_source_changed_after_preview(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    (source / "templates/signal.md").write_text("changed\n", encoding="utf-8")

    with pytest.raises(InstallError, match="source changed after preview"):
        apply_plan(plan)
    assert not any(path.is_file() for path in target.rglob("*"))


def test_apply_rechecks_conflicts_created_after_preview(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    conflict = target / ".agents/skills/product-os-setup/SKILL.md"
    conflict.parent.mkdir(parents=True)
    conflict.write_text("raced\n", encoding="utf-8")

    with pytest.raises(InstallError, match="destination conflict"):
        apply_plan(plan)
    assert conflict.read_text() == "raced\n"
    assert not (target / ".product-os").exists()


def test_clean_update_reconciles_managed_and_preserves_config(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    _install_and_commit(source, config, target)
    preserved = target / ".product-os/config.yaml"
    preserved.write_text("schema_version: 1\nselected_client: codex\n# user edit\n", encoding="utf-8")
    before_config = preserved.read_bytes()

    (source / "templates/signal.md").write_text("# Signal v2\n", encoding="utf-8")
    write_manifest(source)
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)

    assert plan.baseline_tree_digest
    actions = {item.display_destination: item.action for item in plan.files}
    assert actions[".product-os/templates/signal.md"] == "update"
    assert actions[".product-os/config.yaml"] == "unchanged"
    apply_plan(plan)
    assert (target / ".product-os/templates/signal.md").read_text() == "# Signal v2\n"
    assert preserved.read_bytes() == before_config
    installed = json.loads((target / ".product-os/installed-manifest.json").read_text())
    assert installed["target_parent_commit"]
    assert all(entry["ownership"] in {"managed", "preserved", "generated"} for entry in installed["files"])


def test_update_conflict_halts_and_deleted_managed_file_is_restored(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    _install_and_commit(source, config, target)
    managed = target / ".product-os/templates/signal.md"
    managed.write_text("local customization\n", encoding="utf-8")
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    assert next(item for item in plan.files if item.destination == managed).action == "conflict"
    with pytest.raises(InstallError, match="conflicts halt"):
        apply_plan(plan)
    assert managed.read_text() == "local customization\n"

    _git(target, "checkout", "HEAD", "--", managed.relative_to(target).as_posix())
    wrapper = target / ".agents/skills/product-os-setup/SKILL.md"
    wrapper.unlink()
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    assert next(item for item in plan.files if item.destination == wrapper).action == "create"
    apply_plan(plan)
    assert wrapper.read_text() == "# Wrapper\n"


def test_update_requires_committed_baseline_before_writing(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    apply_plan(plan_install(source, target, "codex", config, allow_unpublished_local=True))
    (source / "templates/signal.md").write_text("# changed\n", encoding="utf-8")
    write_manifest(source)
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    with pytest.raises(InstallError, match="committed install"):
        apply_plan(plan)
    assert (target / ".product-os/templates/signal.md").read_text() == "# Signal\n"

    target_with_head = tmp_path / "target-with-head"
    target_with_head.mkdir()
    _git(target_with_head, "init", "-b", "main")
    _git(target_with_head, "config", "user.email", "test@example.com")
    _git(target_with_head, "config", "user.name", "Test")
    (target_with_head / "README.md").write_text("existing repo\n", encoding="utf-8")
    _git(target_with_head, "add", "README.md")
    _git(target_with_head, "commit", "-m", "initial")
    apply_plan(plan_install(source, target_with_head, "codex", config, allow_unpublished_local=True))
    plan = plan_install(source, target_with_head, "codex", config, allow_unpublished_local=True)
    with pytest.raises(InstallError, match="install commit"):
        apply_plan(plan)


def test_update_deletes_removed_upstream_and_rolls_back_mid_apply(
    install_source: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    _install_and_commit(source, config, target)
    managed = target / ".product-os/templates/signal.md"

    (source / "templates/signal.md").unlink()
    (source / "schemas/common.schema.json").write_text('{"changed": true}\n', encoding="utf-8")
    write_manifest(source)
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    actions = {item.display_destination: item.action for item in plan.files}
    assert actions[".product-os/templates/signal.md"] == "delete"
    assert actions[".product-os/schemas/common.schema.json"] == "update"

    original_atomic = installer_module._write_atomic
    calls = 0

    def fail_after_first(path: Path, data: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected update failure")
        original_atomic(path, data)

    monkeypatch.setattr(installer_module, "_write_atomic", fail_after_first)
    with pytest.raises(OSError, match="injected"):
        apply_plan(plan)
    assert managed.read_text() == "# Signal\n"
    assert (target / ".product-os/schemas/common.schema.json").read_text() == "{}\n"


def test_update_validates_baseline_digest_and_rewrites_generated_files(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    _install_and_commit(source, config, target)
    release = target / ".product-os/release-manifest.json"
    release.write_text("locally damaged generated file\n", encoding="utf-8")
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    release_item = next(item for item in plan.files if item.destination == release)
    assert release_item.ownership == "generated"
    assert release_item.action == "update"

    installed_path = target / ".product-os/installed-manifest.json"
    installed = json.loads(installed_path.read_text())
    installed["tree_digest"] = "0" * 64
    installed_path.write_text(json.dumps(installed), encoding="utf-8")
    with pytest.raises(InstallError, match="tree_digest"):
        plan_install(source, target, "codex", config, allow_unpublished_local=True)


def test_update_apply_rechecks_managed_baseline_after_preview(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    _install_and_commit(source, config, target)
    (source / "templates/signal.md").write_text("# upstream v2\n", encoding="utf-8")
    write_manifest(source)
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    managed = target / ".product-os/templates/signal.md"
    managed.write_text("raced local edit\n", encoding="utf-8")

    with pytest.raises(InstallError, match="drifted after preview"):
        apply_plan(plan)
    assert managed.read_text() == "raced local edit\n"


def test_update_accepts_legacy_installed_manifest_without_ownership(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    _install_and_commit(source, config, target)
    manifest_path = target / ".product-os/installed-manifest.json"
    installed = json.loads(manifest_path.read_text())
    for entry in installed["files"]:
        entry.pop("ownership", None)
    for field in ("source_commit", "target_parent_commit", "previous_operation_commit"):
        installed.pop(field, None)
    manifest_path.write_text(json.dumps(installed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _git(target, "add", ".product-os/installed-manifest.json")
    _git(target, "commit", "-m", "fixture: legacy manifest")

    (source / "templates/signal.md").write_text("# legacy upgrade\n", encoding="utf-8")
    write_manifest(source)
    plan = plan_install(source, target, "codex", config, allow_unpublished_local=True)
    apply_plan(plan)
    assert (target / ".product-os/templates/signal.md").read_text() == "# legacy upgrade\n"


def test_plan_reports_whether_the_commit_describes_the_installed_bytes(install_source, tmp_path) -> None:
    """The gate asks a human to confirm a commit; a dirty tree must not hide behind its SHA."""
    source, config = install_source
    target = tmp_path / "target"
    target.mkdir(exist_ok=True)
    for args in (("init", "-q", "-b", "main"), ("config", "user.email", "t@e.x"), ("config", "user.name", "T")):
        subprocess.run(["git", "-C", str(source), *args], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(source), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(source), "commit", "-q", "-m", "source"], check=True, capture_output=True)

    clean = plan_install(source, target, "codex", config, allow_unpublished_local=True).to_dict()
    assert clean["source_state"] == "clean"

    # Modified after the commit and re-manifested, so content verification still passes. This is
    # the case where a SHA alone would be reassuring and wrong.
    (Path(source) / "templates" / "signal.md").write_text("dirtied\n", encoding="utf-8")
    write_manifest(Path(source))
    dirty = plan_install(source, target, "codex", config, allow_unpublished_local=True).to_dict()
    assert dirty["source_state"].startswith("uncommitted_changes:")
    assert dirty["source_commit"] == clean["source_commit"], "same SHA, different bytes"

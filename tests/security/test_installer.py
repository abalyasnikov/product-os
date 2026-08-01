from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.install_workspace import (
    InstallError,
    apply_plan,
    load_plan_document,
    main,
    plan_install,
    write_plan,
)
from scripts.manifest import write_manifest


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
    wrapper = source / "adapters/codex/skills/product-os-setup"
    wrapper.mkdir(parents=True)
    (wrapper / "SKILL.md").write_text("# Wrapper\n", encoding="utf-8")
    adapter = {
        "adapter_schema_version": 1,
        "generated": True,
        "client": "codex",
        "projection": {"client_skill_location": ".agents/skills"},
        "projections": [
            {
                "name": "product-os-setup",
                "canonical_source": ".product-os/skills/setup/SKILL.md",
                "wrapper_source": "adapters/codex/skills/product-os-setup/SKILL.md",
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
    assert all(set(item) == {"source", "destination", "action", "sha256", "size"} for item in preview["files"])
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

    with pytest.raises(InstallError, match="refusing to overwrite"):
        plan_install(source, target, "codex", config, allow_unpublished_local=True)
    assert conflict.read_text() == "user-owned\n"


def test_expected_and_unexpected_product_os_wrappers_are_rejected(
    install_source: tuple[Path, Path], tmp_path: Path
) -> None:
    source, config = install_source
    target = tmp_path / "target"
    unexpected = target / ".agents/skills/product-os-evil/SKILL.md"
    unexpected.parent.mkdir(parents=True)
    unexpected.write_text("malicious\n", encoding="utf-8")

    with pytest.raises(InstallError, match="unexpected product-os wrapper"):
        plan_install(source, target, "codex", config, allow_unpublished_local=True)

    unexpected.parent.rename(target / ".agents/skills/not-product-os")
    expected = target / ".agents/skills/product-os-setup/SKILL.md"
    expected.parent.mkdir(parents=True)
    expected.write_text("existing\n", encoding="utf-8")
    with pytest.raises(InstallError, match="wrapper conflict"):
        plan_install(source, target, "codex", config, allow_unpublished_local=True)
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

    with pytest.raises(InstallError, match="wrapper conflict"):
        apply_plan(plan)
    assert conflict.read_text() == "raced\n"
    assert not (target / ".product-os").exists()

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

from product_decision_os.validator import TYPE_CONFIG, _walk, validate_workspace
from product_decision_os.cli import main as cli_main
from scripts.install_workspace import apply_plan, plan_install
from scripts.manifest import write_manifest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def install_schemas(workspace: Path) -> None:
    schemas = workspace / "schemas"
    schemas.mkdir(parents=True)
    for artifact_type in TYPE_CONFIG:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["schema_version", "id", "type", "title", "created_at", "updated_at", "authors", "relationships"],
            "properties": {"schema_version": {"const": 1}},
        }
        (schemas / f"{artifact_type.replace('_', '-')}.schema.yaml").write_text(
            yaml.safe_dump(schema, sort_keys=False), encoding="utf-8"
        )
    (schemas / "config.schema.yaml").write_text(
        yaml.safe_dump({"type": "object"}, sort_keys=False), encoding="utf-8"
    )


def metadata(artifact_type: str = "signal", artifact_id: str = "signal_01TEST") -> dict:
    return {
        "schema_version": 1,
        "id": artifact_id,
        "type": artifact_type,
        "title": "Test artifact",
        "created_at": "2026-08-01T12:00:00Z",
        "updated_at": "2026-08-01T12:00:00Z",
        "authors": ["product-lead"],
        "relationships": {},
    }


def write_artifact(workspace: Path, data: dict, name: str | None = None, body: str = "# Test\n") -> Path:
    artifact_type = str(data["type"]).replace("-", "_")
    directory = TYPE_CONFIG[artifact_type][1]
    path = workspace / "product" / directory / (name or f"{data['id']}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{yaml.safe_dump(data, sort_keys=False)}---\n{body}", encoding="utf-8")
    return path


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    install_schemas(tmp_path)
    return tmp_path


def codes(report) -> set[str]:
    return {error.code for error in report.errors}


def complete_outcome(status: str = "planned") -> dict:
    binding = {
        "status": status,
        "owner": "analytics-team",
        "due_before": "release",
        "measurement_anchor": {"type": "exposure_event", "reference": "event:first_swap_exposed"},
    }
    if status == "executable":
        binding.update(
            {
                "provider": "amplitude",
                "query_reference": "query:first-swap-v1",
                "definition_version": "definition-v1",
                "verified_by": "analyst",
                "verified_at": "2026-08-01T12:00:00Z",
            }
        )
    return {
        "definition": {
            "version": "definition-v1",
            "baseline": 0.22,
            "target": 0.30,
            "metric": "funded users completing first swap",
            "window": "14 days",
            "slices": ["new_users", "returning_users"],
            "guardrails": ["failed_transaction_rate"],
            "decision_rule": "scale if target passes without guardrail regression",
        },
        "binding": binding,
    }


def test_valid_workspace_passes(workspace: Path) -> None:
    write_artifact(workspace, metadata())
    report = validate_workspace(workspace)
    assert report.exit_code == 0
    assert report.ok
    assert report.artifact_count == 1


def test_frontmatter_must_be_safe_mapping(workspace: Path) -> None:
    path = workspace / "product" / "signals" / "bad.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nvalue: !!python/object/apply:os.system [echo unsafe]\n---\n", encoding="utf-8")
    report = validate_workspace(workspace)
    assert "FRONTMATTER_INVALID" in codes(report)


def test_duplicate_yaml_keys_are_rejected(workspace: Path) -> None:
    path = workspace / "product" / "signals" / "bad.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nid: signal_ONE\nid: signal_TWO\n---\n", encoding="utf-8")
    assert "FRONTMATTER_INVALID" in codes(validate_workspace(workspace))


@pytest.mark.parametrize(
    "alias_yaml",
    [
        "cycle: &cycle [*cycle]",
        "a: &a [x, x, x]\nb: &b [*a, *a, *a]\nc: [*b, *b, *b]",
    ],
)
def test_yaml_aliases_are_rejected_before_cyclic_or_exponential_construction(
    workspace: Path, alias_yaml: str
) -> None:
    path = workspace / "product" / "signals" / "alias.md"
    path.parent.mkdir(parents=True)
    path.write_text(f"---\n{alias_yaml}\n---\n", encoding="utf-8")
    issue = next(error for error in validate_workspace(workspace).errors if error.code == "FRONTMATTER_INVALID")
    assert "aliases are not allowed" in issue.message


def test_recursive_walker_is_cycle_aware() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)
    assert len(list(_walk(cyclic))) == 2


def test_config_yaml_alias_is_rejected(workspace: Path) -> None:
    config = workspace / ".product-os" / "config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("base: &base {default_branch: main}\ncopy: *base\n", encoding="utf-8")
    assert "CONFIG_INVALID" in codes(validate_workspace(workspace))


def test_duplicate_artifact_ids_are_rejected(workspace: Path) -> None:
    write_artifact(workspace, metadata(), "one.md")
    write_artifact(workspace, metadata(), "two.md")
    assert "DUPLICATE_ARTIFACT_ID" in codes(validate_workspace(workspace))


def test_broken_internal_reference_is_actionable(workspace: Path) -> None:
    data = metadata("opportunity", "opportunity_01TEST")
    data["relationships"] = {"signals": ["signal_MISSING"]}
    write_artifact(workspace, data)
    report = validate_workspace(workspace)
    issue = next(error for error in report.errors if error.code == "BROKEN_INTERNAL_REFERENCE")
    assert issue.field == "relationships.signals.0"
    assert issue.hint


def test_relationship_container_and_named_target_type_are_validated(workspace: Path) -> None:
    signal = metadata()
    write_artifact(workspace, signal)
    opportunity = metadata("opportunity", "opportunity_01TEST")
    opportunity["relationships"] = {"patterns": [signal["id"]]}
    write_artifact(workspace, opportunity)
    assert "RELATIONSHIP_TYPE_MISMATCH" in codes(validate_workspace(workspace))

    opportunity["relationships"] = [{"type": "evidence", "id": signal["id"]}]
    write_artifact(workspace, opportunity)
    assert "RELATIONSHIPS_MALFORMED" in codes(validate_workspace(workspace))


def test_type_id_and_directory_must_agree(workspace: Path) -> None:
    data = metadata("signal", "prd_01WRONG")
    write_artifact(workspace, data)
    report = validate_workspace(workspace)
    assert "ID_TYPE_MISMATCH" in codes(report)

    data = metadata("signal", "signal_01MOVED")
    path = write_artifact(workspace, data)
    moved = workspace / "product" / "patterns" / path.name
    moved.parent.mkdir(parents=True, exist_ok=True)
    path.rename(moved)
    assert "DIRECTORY_TYPE_MISMATCH" in codes(validate_workspace(workspace))


def test_symlinked_artifact_and_config_are_rejected(workspace: Path) -> None:
    target = workspace / "artifact-target.md"
    target.write_text("---\n{}\n---\n", encoding="utf-8")
    artifact = workspace / "product" / "signals" / "linked.md"
    artifact.parent.mkdir(parents=True)
    artifact.symlink_to(target)
    config_target = workspace / "config-target.yaml"
    config_target.write_text("{}\n", encoding="utf-8")
    config = workspace / ".product-os" / "config.yaml"
    config.parent.mkdir(parents=True)
    config.symlink_to(config_target)
    report = validate_workspace(workspace)
    assert report.exit_code == 2
    assert "SYMLINK_OR_ESCAPE_REJECTED" in codes(report)


def test_schema_validation_reports_field_path(workspace: Path) -> None:
    schema_path = workspace / "schemas" / "signal.schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    schema["properties"]["title"] = {"type": "string", "minLength": 5}
    schema_path.write_text(yaml.safe_dump(schema), encoding="utf-8")
    data = metadata()
    data["title"] = "x"
    write_artifact(workspace, data)
    issue = next(error for error in validate_workspace(workspace).errors if error.code == "SCHEMA_VALIDATION_FAILED")
    assert issue.field == "title"


def test_schema_errors_do_not_echo_invalid_values(workspace: Path) -> None:
    schema_path = workspace / "schemas" / "signal.schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    schema["properties"]["title"] = {"enum": ["Allowed title"]}
    schema_path.write_text(yaml.safe_dump(schema), encoding="utf-8")
    secret_value = "authorization: bearer super-secret-value-123456"
    data = metadata()
    data["title"] = secret_value
    write_artifact(workspace, data)
    issue = next(error for error in validate_workspace(workspace).errors if error.code == "SCHEMA_VALIDATION_FAILED")
    assert secret_value not in issue.message
    assert "allowed choices" in issue.message


def test_schema_failure_keeps_specific_field_without_remove_valid_domain_fields(tmp_path: Path) -> None:
    shutil.copytree(REPOSITORY_ROOT / "schemas", tmp_path / "schemas")
    data = metadata("opportunity", "opportunity_01JTEST999")
    data.update(
        {
            "blocked_value": "Users cannot finish a funded transaction.",
            "evidence_ids": ["signal_01JTEST999"],
            "affected_users": "Funded users",
            "impact": "Activation is blocked",
            "urgency": "High",
            "strategic_fit": "Trustworthy execution",
            "assumptions": ["Clear recovery improves completion"],
            "risks": ["Network failures may dominate"],
            "evidence_quality": ["malformed nested value"],
            "decision_events": [
                {
                    "id": "decision_01JTEST999",
                    "kind": "opportunity",
                    "choice": "pursue",
                    "decided_by": "product-lead",
                    "decided_at": "2026-08-01T12:00:00Z",
                    "rationale": "Material user blockage",
                    "based_on_version": "approved-v1",
                }
            ],
        }
    )
    write_artifact(tmp_path, data)

    schema_issues = [
        issue for issue in validate_workspace(tmp_path).errors
        if issue.code == "SCHEMA_VALIDATION_FAILED"
    ]

    assert any(issue.field == "evidence_quality" and "required type: object" in issue.message for issue in schema_issues)
    assert all(issue.field is not None for issue in schema_issues)
    assert all("Unevaluated properties are not allowed" not in issue.message for issue in schema_issues)
    assert all("blocked_value" not in issue.message for issue in schema_issues)
    assert all(issue.hint and "templates/opportunity.md" in issue.hint for issue in schema_issues)


def test_excerpt_limit_is_configurable_and_defaults_to_500(workspace: Path) -> None:
    data = metadata()
    data["evidence"] = {"excerpt": "x" * 501}
    write_artifact(workspace, data)
    assert "EVIDENCE_EXCERPT_TOO_LONG" in codes(validate_workspace(workspace))

    config = workspace / ".product-os" / "config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("evidence:\n  max_excerpt_chars: 600\n", encoding="utf-8")
    assert "EVIDENCE_EXCERPT_TOO_LONG" not in codes(validate_workspace(workspace))


def test_raw_transcript_and_transcript_sized_body_are_blocked(workspace: Path) -> None:
    data = metadata()
    data["source"] = {"transcript": "Speaker 1: this content belongs outside Git"}
    write_artifact(workspace, data)
    assert "TRANSCRIPT_CONTENT_FORBIDDEN" in codes(validate_workspace(workspace))

    data.pop("source")
    turns = "\n".join(f"Speaker {index % 2 + 1}: " + "x" * 700 for index in range(20))
    write_artifact(workspace, data, body=turns)
    assert "TRANSCRIPT_SIZED_CONTENT" in codes(validate_workspace(workspace))


def test_known_credential_patterns_are_blocked(workspace: Path) -> None:
    data = metadata()
    data["notes"] = "Synthetic leaked key AKIAABCDEFGHIJKLMNOP"
    write_artifact(workspace, data)
    issue = next(error for error in validate_workspace(workspace).errors if error.code == "CREDENTIAL_LIKE_CONTENT")
    assert "rotate" in issue.hint.lower()


def test_prd_requires_complete_outcome_contract(workspace: Path) -> None:
    data = metadata("prd", "prd_01TEST")
    write_artifact(workspace, data)
    assert "OUTCOME_CONTRACT_MISSING" in codes(validate_workspace(workspace))

    data["outcome"] = {"definition": {"baseline": 0}, "binding": {"status": "planned"}}
    write_artifact(workspace, data)
    report_codes = codes(validate_workspace(workspace))
    assert "OUTCOME_DEFINITION_INCOMPLETE" in report_codes
    assert "PLANNED_BINDING_NOT_READY" in report_codes
    # The actual anchor may be absent before exposure/release; readiness is
    # enforced when work is marked delivered or when a Learning is created.
    assert "MEASUREMENT_ANCHOR_MISSING" not in report_codes


def test_verified_executable_binding_passes_and_unverified_fails(workspace: Path) -> None:
    data = metadata("prd", "prd_01TEST")
    data["outcome"] = complete_outcome("executable")
    write_artifact(workspace, data)
    assert validate_workspace(workspace).exit_code == 0

    del data["outcome"]["binding"]["verified_by"]
    write_artifact(workspace, data)
    assert "EXECUTABLE_BINDING_UNVERIFIED" in codes(validate_workspace(workspace))


def test_executable_binding_version_must_match_definition(workspace: Path) -> None:
    data = metadata("prd", "prd_01TEST")
    data["outcome"] = complete_outcome("executable")
    data["outcome"]["binding"]["definition_version"] = "old-version"
    write_artifact(workspace, data)
    assert "OUTCOME_BINDING_STALE" in codes(validate_workspace(workspace))


def test_executable_binding_requires_versioned_definition(workspace: Path) -> None:
    data = metadata("prd", "prd_01TEST")
    data["outcome"] = complete_outcome("executable")
    del data["outcome"]["definition"]["version"]
    write_artifact(workspace, data)
    assert "OUTCOME_DEFINITION_VERSION_MISSING" in codes(validate_workspace(workspace))


def test_learning_requires_actual_measurement_anchor(workspace: Path) -> None:
    data = metadata("learning", "learning_01TEST")
    write_artifact(workspace, data)
    assert "MEASUREMENT_ANCHOR_MISSING" in codes(validate_workspace(workspace))

    data["measurement_anchor"] = {"type": "release", "occurred_at": "2026-08-01T12:00:00Z"}
    write_artifact(workspace, data)
    assert "MEASUREMENT_ANCHOR_MISSING" not in codes(validate_workspace(workspace))


def test_released_prd_requires_actual_anchor_reference(workspace: Path) -> None:
    data = metadata("prd", "prd_01TEST")
    data["outcome"] = complete_outcome()
    data["outcome"]["binding"]["measurement_anchor"] = {"type": "release"}
    data["delivery_state"] = "released"
    write_artifact(workspace, data)
    assert "MEASUREMENT_ANCHOR_MISSING" in codes(validate_workspace(workspace))


def test_implementation_ref_shape_owner_and_staleness(workspace: Path) -> None:
    data = metadata("prd", "prd_01TEST")
    data["outcome"] = complete_outcome()
    data["implementation_refs"] = [
        {
            "repository": "github.com/example/app",
            "path": "specs/plan.md",
            "based_on_prd_id": "prd_01TEST",
            "based_on_prd_version": "old-version",
        }
    ]
    write_artifact(workspace, data)
    state = workspace / ".product-os" / "review-state.yaml"
    state.parent.mkdir(parents=True)
    state.write_text("artifacts:\n  prd_01TEST:\n    approved_version: current-version\n", encoding="utf-8")
    assert "IMPLEMENTATION_REF_STALE" in codes(validate_workspace(workspace))

    data["implementation_refs"][0].pop("repository")
    data["implementation_refs"][0]["based_on_prd_id"] = "prd_OTHER"
    write_artifact(workspace, data)
    report_codes = codes(validate_workspace(workspace))
    assert "IMPLEMENTATION_REF_INCOMPLETE" in report_codes
    assert "IMPLEMENTATION_REF_PRD_MISMATCH" in report_codes


def test_implementation_refs_require_valid_named_review_state(workspace: Path) -> None:
    data = metadata("prd", "prd_01TEST")
    data["outcome"] = complete_outcome()
    data["implementation_refs"] = [
        {
            "repository": "github.com/example/app",
            "path": "specs/plan.md",
            "based_on_prd_id": data["id"],
            "based_on_prd_version": "v1",
        }
    ]
    write_artifact(workspace, data)
    assert "IMPLEMENTATION_REVIEW_STATE_UNAVAILABLE" in codes(validate_workspace(workspace))

    state = workspace / ".product-os" / "review-state.yaml"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text("- malformed\n", encoding="utf-8")
    assert "IMPLEMENTATION_REVIEW_STATE_INVALID" in codes(validate_workspace(workspace))


def canonical_hash(root: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted(
        path
        for directory in (root / "skills", root / "integrations")
        for path in directory.rglob("*")
        if path.is_file()
    )
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def install_adapter(
    workspace: Path,
    content_hash: str | None = None,
    *,
    client: str = "codex",
    install_destination: bool = True,
) -> Path:
    skill = workspace / "skills" / "discovery" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text("# Discovery\n", encoding="utf-8")
    integration = workspace / "integrations" / "providers" / "granola.yaml"
    integration.parent.mkdir(parents=True, exist_ok=True)
    integration.write_text("capability: transcript.search\n", encoding="utf-8")
    client_roots = {"codex": ".agents/skills", "claude-code": ".claude/skills", "openclaw": "skills"}
    manifest = workspace / "adapters" / client / "manifest.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    value = {
        "adapter_schema_version": 1,
        "generated": True,
        "client": client,
        "canonical_source": {
            "version": "1.0.0",
            "hash_algorithm": "sha256",
            "content_hash": content_hash or canonical_hash(workspace),
            "includes": ["skills/**", "integrations/**"],
        },
        "projection": {"client_skill_location": client_roots[client]},
        "projections": [
            {
                "name": "product-os-discovery",
                "canonical_source": ".product-os/skills/discovery/SKILL.md",
                "wrapper_source": f"adapters/{client}/skills/product-os-discovery/SKILL.md",
                "destination": f"{client_roots[client]}/product-os-discovery/SKILL.md",
            }
        ],
    }
    wrapper = workspace / "adapters" / client / "skills" / "product-os-discovery" / "SKILL.md"
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text("# Generated discovery router\n", encoding="utf-8")
    destination = workspace / client_roots[client] / "product-os-discovery" / "SKILL.md"
    if install_destination:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(wrapper.read_bytes())
    manifest.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    marker = manifest.parent / "ADAPTER.md"
    marker.write_text(
        f"<!-- GENERATED: canonical_version=1.0.0 canonical_sha256={value['canonical_source']['content_hash']} -->\n",
        encoding="utf-8",
    )
    return manifest


def install_provenance(workspace: Path) -> None:
    entries = []
    for path in sorted(
        (candidate for candidate in workspace.rglob("*") if candidate.is_file() and ".git" not in candidate.parts),
        key=lambda candidate: candidate.relative_to(workspace).as_posix(),
    ):
        if path.name == "manifest.json":
            continue
        entries.append(
            {
                "path": path.relative_to(workspace).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size": path.stat().st_size,
            }
        )
    digest = hashlib.sha256()
    for entry in entries:
        digest.update(entry["path"].encode())
        digest.update(b"\0")
        digest.update(entry["sha256"].encode())
        digest.update(b"\0")
    (workspace / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "hash_algorithm": "sha256",
                "tree_digest": digest.hexdigest(),
                "files": entries,
            }
        ),
        encoding="utf-8",
    )


def install_scoped_provenance(workspace: Path, *, client: str) -> None:
    installed_root = workspace / ".product-os"
    release = {
        "manifest_version": 1,
        "product": "product-decision-os",
        "release": "test-release",
        "canonical_origin": "test-fixture",
        "publisher": "test-publisher",
        "hash_algorithm": "sha256",
        "files": [],
        "tree_digest": hashlib.sha256(b"").hexdigest(),
    }
    release_path = installed_root / "release-manifest.json"
    release_path.write_text(json.dumps(release, sort_keys=True), encoding="utf-8")

    source_for = lambda destination: (
        "@config"
        if destination == ".product-os/config.yaml"
        else destination.removeprefix(".product-os/")
    )
    planned_paths = sorted(
        path for path in workspace.rglob("*")
        if path.is_file()
        and path.name not in {"installed-manifest.json", "install-plan.json"}
        and (
            ".product-os" in path.parts
            or "product-os-" in path.as_posix()
        )
    )
    plan_files = []
    for path in planned_paths:
        destination = path.relative_to(workspace).as_posix()
        plan_files.append(
            {
                "source": source_for(destination),
                "destination": destination,
                "action": "create",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size": path.stat().st_size,
            }
        )
    plan_files.sort(key=lambda item: item["destination"])
    config_hash = hashlib.sha256((installed_root / "config.yaml").read_bytes()).hexdigest()
    payload = {
        "plan_version": 1,
        "client": client,
        "release_tree_digest": release["tree_digest"],
        "config_sha256": config_hash,
        "files": plan_files,
    }
    plan_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    plan_path = installed_root / "install-plan.json"
    plan_path.write_text(json.dumps({**payload, "plan_hash": plan_hash}, sort_keys=True), encoding="utf-8")

    scoped_paths = sorted([*planned_paths, plan_path], key=lambda path: path.relative_to(workspace).as_posix())
    entries = [
        {
            "path": path.relative_to(workspace).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size": path.stat().st_size,
        }
        for path in scoped_paths
    ]
    digest = hashlib.sha256()
    for entry in entries:
        digest.update(entry["path"].encode())
        digest.update(b"\0")
        digest.update(entry["sha256"].encode())
        digest.update(b"\0")
    installed = {
        "manifest_version": 1,
        "manifest_kind": "installed_workspace",
        "hash_algorithm": "sha256",
        "client": client,
        "files": entries,
        "tree_digest": digest.hexdigest(),
        "install_plan_sha256": plan_hash,
        "parent_release": {
            key: release[key]
            for key in ("product", "release", "canonical_origin", "publisher", "tree_digest")
        },
    }
    (installed_root / "installed-manifest.json").write_text(
        json.dumps(installed, sort_keys=True), encoding="utf-8"
    )


def test_adapter_hash_passes_and_stale_hash_fails(workspace: Path) -> None:
    install_adapter(workspace)
    report = validate_workspace(workspace, "adapter-check")
    assert report.exit_code == 0

    install_adapter(workspace, "0" * 64)
    report = validate_workspace(workspace, "adapter-check")
    assert "ADAPTER_HASH_STALE" in codes(report)


def test_adapter_manifest_requires_generated_hash_metadata(workspace: Path) -> None:
    manifest = install_adapter(workspace)
    manifest.write_text("generated: false\n", encoding="utf-8")
    assert "ADAPTER_HASH_METADATA_INVALID" in codes(validate_workspace(workspace, "adapter-check"))


def test_smoke_test_combines_validation_adapter_and_skill_checks(workspace: Path) -> None:
    write_artifact(workspace, metadata())
    install_adapter(workspace)
    config = workspace / ".product-os" / "config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("default_branch: main\nselected_client: codex\nconnectors:\n  transcript: granola\n", encoding="utf-8")
    git(workspace, "init", "-b", "main")
    install_provenance(workspace)
    report = validate_workspace(workspace, "smoke-test")
    assert report.exit_code == 0
    assert {check.name for check in report.checks} >= {
        "frontmatter",
        "ids-and-relationships",
        "generated-adapters",
        "skill-discovery",
        "release-provenance",
        "git-access",
        "connector-descriptors",
        "credential-scan",
    }


def test_smoke_test_supports_installed_layout_from_unrelated_cwd(
    workspace: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_artifact(workspace, metadata())
    install_adapter(workspace)
    installed = workspace / ".product-os"
    installed.mkdir(exist_ok=True)
    for name in ("schemas", "skills", "integrations", "adapters"):
        shutil.move(str(workspace / name), str(installed / name))
    (installed / "config.yaml").write_text(
        "default_branch: main\nselected_client: codex\nconnectors:\n  transcript: granola\n", encoding="utf-8"
    )
    install_scoped_provenance(workspace, client="codex")
    git(workspace, "init", "-b", "main")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    monkeypatch.chdir(unrelated)

    report = validate_workspace(workspace, "smoke-test")

    assert report.exit_code == 0
    assert "PROVENANCE_MANIFEST_MISSING" not in codes(report)


@pytest.mark.parametrize(
    ("client", "client_root"),
    [
        ("codex", ".agents/skills"),
        ("claude-code", ".claude/skills"),
        ("openclaw", "skills"),
    ],
)
def test_clean_installed_empty_workspace_validates_and_smokes(workspace: Path, client: str, client_root: str) -> None:
    prepare_installed_empty_workspace(workspace, client=client, client_root=client_root)

    validate_report = validate_workspace(workspace)
    smoke_report = validate_workspace(workspace, "smoke-test")

    assert validate_report.exit_code == 0
    assert smoke_report.exit_code == 0
    assert validate_report.artifact_count == smoke_report.artifact_count == 0
    assert "EMPTY_WORKSPACE" in {warning.code for warning in validate_report.warnings}
    assert "EMPTY_WORKSPACE" in {warning.code for warning in smoke_report.warnings}


@pytest.mark.parametrize("client", ["codex", "claude-code", "openclaw"])
def test_real_installer_output_validates_and_smokes_for_each_client(tmp_path: Path, client: str) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    install_schemas(source)
    (source / "schemas" / "config.schema.json").write_text(
        json.dumps(
            {
                "type": "object",
                "required": ["schema_version", "selected_client"],
                "properties": {
                    "schema_version": {"const": 1},
                    "selected_client": {"enum": ["codex", "claude-code", "openclaw"]},
                },
            }
        ),
        encoding="utf-8",
    )
    templates = source / "templates"
    templates.mkdir()
    (templates / "signal.md").write_text("# Signal\n", encoding="utf-8")
    install_adapter(source, client=client, install_destination=False)
    write_manifest(source)
    config = tmp_path / "config.yaml"
    config.write_text(f"schema_version: 1\nselected_client: {client}\n", encoding="utf-8")

    plan = plan_install(source, target, client, config, allow_unpublished_local=True)
    apply_plan(plan)
    git(target, "init", "-b", "main")

    validate_report = validate_workspace(target)
    smoke_report = validate_workspace(target, "smoke-test")
    assert validate_report.exit_code == 0
    assert smoke_report.exit_code == 0
    assert "EMPTY_WORKSPACE" in {warning.code for warning in smoke_report.warnings}


def prepare_installed_empty_workspace(workspace: Path, *, client: str, client_root: str) -> None:
    install_adapter(workspace, client=client, install_destination=client != "openclaw")
    installed = workspace / ".product-os"
    installed.mkdir(exist_ok=True)
    for name in ("schemas", "skills", "integrations", "adapters"):
        shutil.move(str(workspace / name), str(installed / name))
    if client == "openclaw":
        source = installed / "adapters" / client / "skills" / "product-os-discovery" / "SKILL.md"
        destination = workspace / client_root / "product-os-discovery" / "SKILL.md"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(source.read_bytes())
    (installed / "config.yaml").write_text(
        f"default_branch: main\nselected_client: {client}\n", encoding="utf-8"
    )
    install_scoped_provenance(workspace, client=client)
    git(workspace, "init", "-b", "main")


def test_installed_provenance_rejects_plan_parent_and_scoped_file_tampering(workspace: Path) -> None:
    prepare_installed_empty_workspace(workspace, client="codex", client_root=".agents/skills")
    installed_path = workspace / ".product-os" / "installed-manifest.json"
    installed = json.loads(installed_path.read_text(encoding="utf-8"))
    installed["parent_release"]["publisher"] = "different-publisher"
    installed_path.write_text(json.dumps(installed, sort_keys=True), encoding="utf-8")
    assert "PARENT_RELEASE_PROVENANCE_MISMATCH" in codes(validate_workspace(workspace, "smoke-test"))

    install_scoped_provenance(workspace, client="codex")
    plan_path = workspace / ".product-os" / "install-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["plan_hash"] = "0" * 64
    plan_path.write_text(json.dumps(plan, sort_keys=True), encoding="utf-8")
    assert "INSTALL_PLAN_HASH_MISMATCH" in codes(validate_workspace(workspace, "smoke-test"))

    install_scoped_provenance(workspace, client="codex")
    config = workspace / ".product-os" / "config.yaml"
    config.write_text(config.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
    assert "PROVENANCE_FILE_MISMATCH" in codes(validate_workspace(workspace, "smoke-test"))


def test_existing_malformed_product_tree_still_fails(workspace: Path) -> None:
    invalid = workspace / "product" / "signals" / "raw.json"
    invalid.parent.mkdir(parents=True)
    invalid.write_text("{}\n", encoding="utf-8")
    report = validate_workspace(workspace)
    assert report.exit_code == 1
    assert "PRODUCT_TREE_INVALID" in codes(report)
    assert "EMPTY_WORKSPACE" not in {warning.code for warning in report.warnings}


def prepare_smoke_workspace(workspace: Path) -> None:
    write_artifact(workspace, metadata())
    install_adapter(workspace)
    config = workspace / ".product-os" / "config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("default_branch: main\nselected_client: codex\n", encoding="utf-8")
    git(workspace, "init", "-b", "main")


def test_active_wrapper_rejects_mismatch_extra_and_symlink(workspace: Path) -> None:
    prepare_smoke_workspace(workspace)
    destination = workspace / ".agents" / "skills" / "product-os-discovery" / "SKILL.md"
    destination.write_text("modified wrapper\n", encoding="utf-8")
    extra = workspace / ".agents" / "skills" / "product-os-stale" / "SKILL.md"
    extra.parent.mkdir(parents=True)
    extra.write_text("stale\n", encoding="utf-8")
    install_provenance(workspace)
    report_codes = codes(validate_workspace(workspace, "smoke-test"))
    assert "ACTIVE_WRAPPER_MISMATCH" in report_codes
    assert "ACTIVE_WRAPPER_EXTRA" in report_codes

    destination.unlink()
    source = workspace / "adapters" / "codex" / "skills" / "product-os-discovery" / "SKILL.md"
    destination.symlink_to(source)
    assert "SYMLINK_OR_ESCAPE_REJECTED" in codes(validate_workspace(workspace, "smoke-test"))


def test_smoke_scans_staged_secret_and_pii_without_echoing_values(workspace: Path) -> None:
    prepare_smoke_workspace(workspace)
    secret = "AKIAABCDEFGHIJKLMNOP"
    email = "private.person@example.invalid"
    artifact = next((workspace / "product").rglob("*.md"))
    artifact.write_text(artifact.read_text(encoding="utf-8") + f"\n{secret}\n{email}\n", encoding="utf-8")
    git(workspace, "add", str(artifact.relative_to(workspace)))
    install_provenance(workspace)
    report = validate_workspace(workspace, "smoke-test")
    staged = [issue for issue in report.errors if issue.path == "<staged-diff>"]
    assert any(issue.code == "CREDENTIAL_LIKE_CONTENT" for issue in staged)
    assert any(issue.code == "PII_LIKE_CONTENT" for issue in report.warnings)
    assert all(secret not in issue.message and email not in issue.message for issue in report.errors + report.warnings)
    assert any(issue.code == "HEURISTIC_CONTENT_SCAN_LIMITED" for issue in report.warnings)


def test_smoke_requires_reachable_full_decision_basis_sha(workspace: Path) -> None:
    prepare_smoke_workspace(workspace)
    git(workspace, "config", "user.email", "fixture@example.invalid")
    git(workspace, "config", "user.name", "Fixture")
    git(workspace, "commit", "--allow-empty", "-m", "review basis")
    sha = subprocess.run(
        ["git", "-C", str(workspace), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    data = metadata("opportunity", "opportunity_01DECIDE")
    data["decision_events"] = [decision_event(based_on_version="friendly-label")]
    write_artifact(workspace, data)
    install_provenance(workspace)
    assert "DECISION_EVENT_VERSION_UNVERIFIED" in codes(validate_workspace(workspace, "smoke-test"))

    data["decision_events"] = [decision_event(based_on_version=sha)]
    write_artifact(workspace, data)
    install_provenance(workspace)
    assert "DECISION_EVENT_VERSION_UNVERIFIED" not in codes(validate_workspace(workspace, "smoke-test"))


def test_malformed_config_is_actionable_configuration_error(workspace: Path) -> None:
    config = workspace / ".product-os" / "config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("- not\n- an-object\n", encoding="utf-8")
    report = validate_workspace(workspace)
    assert report.exit_code == 2
    assert "CONFIG_INVALID" in codes(report)


def test_adapter_marker_requires_exactly_one_matching_hash(workspace: Path) -> None:
    manifest = install_adapter(workspace)
    marker = manifest.parent / "ADAPTER.md"
    marker.write_text("generated adapter without provenance\n", encoding="utf-8")
    assert "ADAPTER_MARKER_INVALID" in codes(validate_workspace(workspace, "adapter-check"))

    digest = canonical_hash(workspace)
    marker.write_text(
        f"canonical_sha256={digest}\ncanonical_sha256={digest}\n", encoding="utf-8"
    )
    assert "ADAPTER_MARKER_INVALID" in codes(validate_workspace(workspace, "adapter-check"))


def test_cli_malformed_invocation_is_json_safe(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli_main(["unknown", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["exit_code"] == 2
    assert payload["errors"][0]["code"] == "INVOCATION_ERROR"


def test_nonexistent_workspace_is_invocation_error(tmp_path: Path) -> None:
    report = validate_workspace(tmp_path / "missing")
    assert report.exit_code == 2
    assert "WORKSPACE_NOT_FOUND" in codes(report)


def test_json_report_is_stable_and_actionable(workspace: Path) -> None:
    write_artifact(workspace, metadata(), body="Synthetic: AKIAABCDEFGHIJKLMNOP")
    payload = validate_workspace(workspace).to_dict()
    assert payload["report_version"] == 1
    assert payload["exit_code"] == 1
    assert payload["summary"]["errors"] >= 1
    assert all("code" in error and "message" in error for error in payload["errors"])


def test_typed_reference_fields_resolve_and_match_relationships(workspace: Path) -> None:
    signal = metadata("signal", "signal_01EVIDENCE")
    write_artifact(workspace, signal)
    opportunity = metadata("opportunity", "opportunity_01TARGET")
    opportunity["relationships"] = {"signals": [signal["id"]]}
    opportunity["evidence_ids"] = [signal["id"]]
    write_artifact(workspace, opportunity)
    report = validate_workspace(workspace)
    assert "BROKEN_TYPED_REFERENCE" not in codes(report)
    assert "REFERENCE_RELATIONSHIP_CONTRADICTION" not in codes(report)

    opportunity["evidence_ids"] = ["signal_01MISSING"]
    write_artifact(workspace, opportunity)
    report_codes = codes(validate_workspace(workspace))
    assert "BROKEN_TYPED_REFERENCE" in report_codes
    assert "REFERENCE_RELATIONSHIP_CONTRADICTION" in report_codes


@pytest.mark.parametrize(
    ("field_name", "value", "expected_prefix"),
    [
        ("opportunity_id", "signal_01EVIDENCE", "opportunity_"),
        ("initiative_id", "signal_01EVIDENCE", "initiative_"),
        ("product_bet_id", "signal_01EVIDENCE", "initiative_"),
        ("outcome_contract_id", "signal_01EVIDENCE", "outcome_"),
    ],
)
def test_singular_typed_reference_prefixes_are_enforced(
    workspace: Path, field_name: str, value: str, expected_prefix: str
) -> None:
    data = metadata()
    data[field_name] = value
    write_artifact(workspace, data)
    issue = next(
        error for error in validate_workspace(workspace).errors
        if error.code == "TYPED_REFERENCE_PREFIX_MISMATCH"
    )
    assert expected_prefix in issue.hint


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("evidence_ids", "signal_01MISSING"),
        ("supporting_signal_ids", "signal_01MISSING"),
        ("contradictory_signal_ids", "signal_01MISSING"),
        ("child_prd_ids", "prd_01MISSING"),
        ("owner_artifact_ids", "initiative_01MISSING"),
        ("product_bet_ids", "prd_01MISSING"),
        ("learnings", "learning_01MISSING"),
    ],
)
def test_all_typed_reference_arrays_reject_missing_targets(
    workspace: Path, field_name: str, value: str
) -> None:
    data = metadata()
    data[field_name] = [value]
    write_artifact(workspace, data)
    assert "BROKEN_TYPED_REFERENCE" in codes(validate_workspace(workspace))


@pytest.mark.parametrize(
    ("field_name", "wrong_value"),
    [
        ("child_prd_ids", "signal_01WRONG"),
        ("owner_artifact_ids", "signal_01WRONG"),
        ("product_bet_ids", "signal_01WRONG"),
        ("learnings", "signal_01WRONG"),
    ],
)
def test_typed_reference_arrays_reject_wrong_prefixes(
    workspace: Path, field_name: str, wrong_value: str
) -> None:
    data = metadata()
    data[field_name] = [wrong_value]
    write_artifact(workspace, data)
    assert "TYPED_REFERENCE_PREFIX_MISMATCH" in codes(validate_workspace(workspace))


def test_scalar_reference_contradiction_with_relationship_is_rejected(workspace: Path) -> None:
    first = metadata("opportunity", "opportunity_01FIRST")
    second = metadata("opportunity", "opportunity_01SECOND")
    write_artifact(workspace, first)
    write_artifact(workspace, second)
    source = metadata()
    source["opportunity_id"] = first["id"]
    source["relationships"] = {"opportunity": second["id"]}
    write_artifact(workspace, source)
    assert "REFERENCE_RELATIONSHIP_CONTRADICTION" in codes(validate_workspace(workspace))


def test_outcome_contract_ref_resolves_required_and_optional_ids(workspace: Path) -> None:
    initiative = metadata("initiative", "initiative_01OWNER")
    initiative["relationships"] = {"outcome_contract": "outcome_01CONTRACT"}
    initiative["outcome"] = complete_outcome()
    write_artifact(workspace, initiative)
    contract = metadata("outcome_contract", "outcome_01CONTRACT")
    contract["outcome"] = complete_outcome()
    write_artifact(workspace, contract)
    learning = metadata("learning", "learning_01RESULT")
    learning["relationships"] = {"initiative": initiative["id"], "outcome_contract": contract["id"]}
    learning["outcome_contract_ref"] = {
        "owner_artifact_id": initiative["id"],
        "definition_version": "definition-v1",
    }
    learning["measurement_anchor"] = {
        "type": "manual",
        "reference": "eval-1",
        "occurred_at": "2026-08-01T12:00:00Z",
    }
    write_artifact(workspace, learning)
    report_codes = codes(validate_workspace(workspace))
    assert "TYPED_REFERENCE_INVALID" not in report_codes
    assert "BROKEN_TYPED_REFERENCE" not in report_codes

    learning["outcome_contract_ref"]["extracted_artifact_id"] = "outcome_01MISSING"
    write_artifact(workspace, learning)
    assert "BROKEN_TYPED_REFERENCE" in codes(validate_workspace(workspace))


def test_learning_versions_must_match_owner_definition(workspace: Path) -> None:
    initiative = metadata("initiative", "initiative_01OWNER")
    initiative["outcome"] = complete_outcome()
    write_artifact(workspace, initiative)
    learning = metadata("learning", "learning_01RESULT")
    learning["relationships"] = {"initiative": initiative["id"]}
    learning["outcome_contract_ref"] = {
        "owner_artifact_id": initiative["id"],
        "definition_version": "old-definition",
    }
    learning["measurement_anchor"] = {"type": "manual", "reference": "eval-1"}
    learning["results"] = {"provenance": {"definition_version": "another-old-definition"}}
    write_artifact(workspace, learning)
    report_codes = codes(validate_workspace(workspace))
    assert "OUTCOME_CONTRACT_REF_STALE" in report_codes
    assert "RESULT_PROVENANCE_DEFINITION_STALE" in report_codes


def test_structured_product_update_artifact_sources_resolve(workspace: Path) -> None:
    signal = metadata("signal", "signal_01SOURCE")
    write_artifact(workspace, signal)
    update = metadata("product_update", "update_01REPORT")
    update["claims"] = [
        {
            "claim": "A sourced claim",
            "source_references": [
                {"kind": "artifact", "artifact_id": signal["id"], "version": "commit-1"},
                {"kind": "provider", "provider": "linear", "external_id": "project-fixture"},
            ],
        }
    ]
    write_artifact(workspace, update)
    assert "BROKEN_TYPED_REFERENCE" not in codes(validate_workspace(workspace))

    update["claims"][0]["source_references"][0]["artifact_id"] = "signal_01MISSING"
    write_artifact(workspace, update)
    assert "BROKEN_TYPED_REFERENCE" in codes(validate_workspace(workspace))


def decision_event(event_id: str = "decision_01BASE", **overrides) -> dict:
    event = {
        "id": event_id,
        "kind": "opportunity",
        "choice": "pursue",
        "decided_by": "product-lead",
        "decided_at": "2026-08-01T12:00:00Z",
        "rationale": "Baseline decision",
        "based_on_version": "commit-baseline",
    }
    event.update(overrides)
    return event


def git(workspace: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(workspace), *args], check=True, capture_output=True, text=True)


@pytest.fixture
def decision_git_workspace(workspace: Path) -> Path:
    data = metadata("opportunity", "opportunity_01DECIDE")
    data["decision_events"] = [decision_event()]
    write_artifact(workspace, data)
    git(workspace, "init", "-b", "main")
    git(workspace, "config", "user.email", "fixture@example.invalid")
    git(workspace, "config", "user.name", "Fixture")
    git(workspace, "add", ".")
    git(workspace, "commit", "-m", "baseline")
    return workspace


def test_decision_event_payload_mutation_is_rejected(decision_git_workspace: Path) -> None:
    data = metadata("opportunity", "opportunity_01DECIDE")
    data["decision_events"] = [decision_event(rationale="Changed in place")]
    write_artifact(decision_git_workspace, data)
    assert "DECISION_EVENT_MUTATED" in codes(
        validate_workspace(decision_git_workspace, base_ref="HEAD")
    )


def test_decision_event_removal_is_rejected(decision_git_workspace: Path) -> None:
    data = metadata("opportunity", "opportunity_01DECIDE")
    data["decision_events"] = []
    write_artifact(decision_git_workspace, data)
    report_codes = codes(validate_workspace(decision_git_workspace, base_ref="main"))
    assert "DECISION_EVENT_REMOVED" in report_codes
    assert "DECISION_EVENT_NOT_APPENDED" in report_codes


def test_appended_superseding_decision_event_is_allowed(decision_git_workspace: Path) -> None:
    data = metadata("opportunity", "opportunity_01DECIDE")
    data["decision_events"] = [
        decision_event(),
        decision_event(
            "decision_01CORRECT",
            choice="hold",
            rationale="Correction after new evidence",
            supersedes="decision_01BASE",
        ),
    ]
    write_artifact(decision_git_workspace, data)
    report_codes = codes(validate_workspace(decision_git_workspace, base_ref="HEAD"))
    assert not {
        "DECISION_EVENT_MUTATED",
        "DECISION_EVENT_REMOVED",
        "DECISION_EVENT_NOT_APPENDED",
        "DECISION_EVENT_SUPERSEDES_INVALID",
    }.intersection(report_codes)


def test_workspace_default_branch_config_selects_baseline(decision_git_workspace: Path) -> None:
    config = decision_git_workspace / ".product-os" / "config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("default_branch: main\n", encoding="utf-8")
    git(decision_git_workspace, "add", ".product-os/config.yaml")
    git(decision_git_workspace, "commit", "-m", "configure default branch")
    data = metadata("opportunity", "opportunity_01DECIDE")
    data["decision_events"] = [decision_event(rationale="Changed in place")]
    write_artifact(decision_git_workspace, data)
    assert "DECISION_EVENT_MUTATED" in codes(validate_workspace(decision_git_workspace))


def test_unreachable_default_branch_fails_with_history_even_without_events(workspace: Path) -> None:
    write_artifact(workspace, metadata())
    git(workspace, "init", "-b", "main")
    git(workspace, "config", "user.email", "fixture@example.invalid")
    git(workspace, "config", "user.name", "Fixture")
    git(workspace, "add", ".")
    git(workspace, "commit", "-m", "first")
    git(workspace, "commit", "--allow-empty", "-m", "second")
    config = workspace / ".product-os" / "config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("default_branch: missing-default\n", encoding="utf-8")
    assert "DECISION_BASELINE_UNAVAILABLE" in codes(validate_workspace(workspace))


def test_review_state_requires_reachable_verified_full_sha(workspace: Path) -> None:
    data = metadata("prd", "prd_01TEST")
    data["outcome"] = complete_outcome()
    data["implementation_refs"] = [
        {
            "repository": "github.com/example/app",
            "path": "specs/plan.md",
            "based_on_prd_id": data["id"],
            "based_on_prd_version": "placeholder",
        }
    ]
    write_artifact(workspace, data)
    git(workspace, "init", "-b", "main")
    git(workspace, "config", "user.email", "fixture@example.invalid")
    git(workspace, "config", "user.name", "Fixture")
    git(workspace, "add", ".")
    git(workspace, "commit", "-m", "approved PRD")
    sha = subprocess.run(
        ["git", "-C", str(workspace), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    data["implementation_refs"][0]["based_on_prd_version"] = sha
    write_artifact(workspace, data)
    state = workspace / ".product-os" / "review-state.yaml"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        yaml.safe_dump(
            {
                "approved_artifacts": {
                    data["id"]: {
                        "approved_version": sha,
                        "approved_by": "reviewer",
                        "approved_at": "2026-08-01T12:00:00Z",
                        "provenance": {
                            "git_sha": sha,
                            "verification_mode": "provider_review",
                            "verified_by": "reviewer",
                            "verified_at": "2026-08-01T12:00:00Z",
                            "provider_reference": "review-123",
                        },
                    }
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    assert "IMPLEMENTATION_REVIEW_STATE_UNVERIFIED" not in codes(validate_workspace(workspace))

    state.write_text("approved_artifacts:\n  prd_01TEST:\n    approved_version: not-a-sha\n", encoding="utf-8")
    assert "IMPLEMENTATION_REVIEW_STATE_UNVERIFIED" in codes(validate_workspace(workspace))


def test_missing_git_baseline_is_named_warning(workspace: Path) -> None:
    data = metadata("opportunity", "opportunity_01DECIDE")
    data["decision_events"] = [decision_event()]
    write_artifact(workspace, data)
    report = validate_workspace(workspace, base_ref="missing-ref")
    assert "DECISION_BASELINE_UNAVAILABLE" in {warning.code for warning in report.warnings}

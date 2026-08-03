from __future__ import annotations

from pathlib import Path

import yaml


PROVIDERS = {"granola", "linear", "amplitude", "mixpanel", "metabase", "github"}
EXTERNAL_SAAS = PROVIDERS
ANALYTICS = {"amplitude", "mixpanel", "metabase"}


def test_required_provider_descriptors_exist(repo_root: Path) -> None:
    found = {path.stem for path in (repo_root / "integrations/providers").glob("*.yaml")}
    assert found == PROVIDERS


def test_external_saas_descriptors_require_existing_provider_mcps(repo_root: Path) -> None:
    for provider in EXTERNAL_SAAS:
        path = repo_root / f"integrations/providers/{provider}.yaml"
        descriptor = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert descriptor["descriptor_kind"] == "existing_provider_mcp_mapping"
        assert descriptor["existing_mcp_required"] is True
        assert descriptor["implements_mcp"] is False
        assert descriptor["credentials"] == "provider_managed"
        assert descriptor["canonical_version"] == "1.0.0"
        assert descriptor["capability_mappings"]


def test_analytics_adapters_share_the_same_read_only_contract(repo_root: Path) -> None:
    for provider in ANALYTICS:
        descriptor = yaml.safe_load(
            (repo_root / f"integrations/providers/{provider}.yaml").read_text(encoding="utf-8")
        )
        query = descriptor["capability_mappings"]["analytics.query"]
        assert query["access"] == "read_only"
        assert set(query["required_inputs"]) == {
            "query_reference",
            "definition_version",
            "window",
            "slices",
            "guardrails",
        }
        assert {"result", "slice_results", "provenance"} <= set(query["required_outputs"])
        assert descriptor["smoke_test"]["mode"] == "read_only"


def test_linear_mapping_enforces_preview_confirmation_and_idempotency(repo_root: Path) -> None:
    descriptor = yaml.safe_load(
        (repo_root / "integrations/providers/linear.yaml").read_text(encoding="utf-8")
    )
    write = descriptor["capability_mappings"]["delivery.project.write"]
    assert write["access"] == "external_write"
    assert "exact_write_preview_shown" in write["preconditions"]
    assert "explicit_human_confirmation" in write["preconditions"]
    assert write["idempotency"]["key"] == "stable_prd_id"
    assert write["idempotency"]["excludes"] == ["approved_git_version"]
    assert write["mutable_sync_metadata"] == ["approved_git_version"]
    assert "idempotency_key" in write["required_inputs"]
    assert "idempotency_identity" not in write["required_inputs"]
    assert "Read before retry" in write["idempotency"]["after_timeout"]
    assert descriptor["smoke_test"]["mode"] == "read_only"


def test_github_maps_review_and_commit_reads_without_local_fallback(repo_root: Path) -> None:
    descriptor = yaml.safe_load(
        (repo_root / "integrations/providers/github.yaml").read_text(encoding="utf-8")
    )
    assert set(descriptor["capability_mappings"]) == {"git.review.read", "git.commit.read"}
    assert descriptor["capability_mappings"]["git.review.read"]["access"] == "read_only"
    assert "approval_is_after_last_material_change" in descriptor["capability_mappings"]["git.review.read"]["verification"]
    assert descriptor["smoke_test"]["mode"] == "read_only"
    assert "cannot substitute" in descriptor["guidance"]["solo_boundary"]


def test_local_git_is_agent_native_solo_guidance_not_an_mcp(repo_root: Path) -> None:
    guidance = (repo_root / "integrations/local-git.md").read_text(encoding="utf-8").lower()
    assert "agent-native repository capability, not an mcp mapping" in guidance
    assert "product-approval: explicit" in guidance
    assert "local git cannot satisfy `git.review.read`" in guidance
    assert "provider review mode therefore requires an existing provider mcp" in guidance
    assert "approval is `unknown` and handoff stops" in guidance


def test_no_hidden_connector_or_custom_mcp_implementation(repo_root: Path) -> None:
    integration_root = repo_root / "integrations"
    files = [path for path in integration_root.rglob("*") if path.is_file()]
    assert files
    assert {path.suffix for path in files} <= {".md", ".yaml"}

    capability_contract = yaml.safe_load(
        (integration_root / "capabilities.yaml").read_text(encoding="utf-8")
    )
    assert capability_contract["implementation"] == "none"
    assert capability_contract["transport"] == "none"
    assert capability_contract["safety"]["smoke_tests_are_read_only"] is True

    forbidden_config_keys = {
        "endpoint",
        "base_url",
        "command",
        "args",
        "headers",
        "token",
        "api_key",
        "oauth_client",
        "server_command",
    }

    def keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value) | {key for child in value.values() for key in keys(child)}
        if isinstance(value, list):
            return {key for child in value for key in keys(child)}
        return set()

    for path in integration_root.glob("providers/*.yaml"):
        descriptor = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert not (keys(descriptor) & forbidden_config_keys), path

from __future__ import annotations

from pathlib import Path

import yaml

from product_decision_os.frontmatter import parse_markdown
from product_decision_os.validator import validate_workspace


def _artifacts(workspace: Path) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for path in sorted((workspace / "product").glob("*/*.md")):
        document = parse_markdown(path)
        result[str(document.metadata["id"])] = document.metadata
    return result


def test_reference_journey_closes_the_evidence_to_learning_loop(repo_root: Path) -> None:
    workspace = repo_root / "examples/fixtures/valid-workspace"
    report = validate_workspace(workspace, command="smoke-test")
    assert report.ok, [error.to_dict() for error in report.errors]

    artifacts = _artifacts(workspace)
    assert len(artifacts) == 11

    opportunity = artifacts["opportunity_01JABCDE01"]
    assert opportunity["decision_events"][-1]["choice"] == "pursue"
    assert len(opportunity["relationships"]["signals"]) == 4

    initiative = artifacts["initiative_01JABCDE01"]
    assert set(initiative["child_prd_ids"]) == {"prd_01JABCDE01", "prd_01JABCDE02"}
    assert initiative["outcome"]["definition"]["version"] == "metric-v2"
    assert initiative["outcome"]["binding"]["status"] == "executable"

    route_prd = artifacts["prd_01JABCDE01"]
    assert route_prd["implementation_refs"][0]["based_on_prd_version"] == "3333333333333333333333333333333333333333"
    assert route_prd["outcome"]["binding"]["measurement_anchor"]["type"] == "manual"

    learning = artifacts["learning_01JABCDE01"]
    assert learning["product_bet_id"] == "initiative_01JABCDE01"
    assert learning["outcome_contract_ref"] == {
        "owner_artifact_id": "initiative_01JABCDE01",
        "definition_version": "metric-v2",
    }
    assert learning["results"]["observed"] >= initiative["outcome"]["definition"]["target"]
    assert learning["decision_events"][-1]["choice"] == "scale"
    assert learning["measurement_anchor"]["reference"] == "exposure-fixture-rollout-01"

    update = artifacts["update_01JABCDE01"]
    assert all(claim["source_references"] for claim in update["claims"])


def test_reference_handoff_is_idempotent_and_uses_approved_versions(repo_root: Path) -> None:
    external = repo_root / "examples/fixtures/valid-workspace/external"
    reviews = yaml.safe_load((external / "git/reviews.yaml").read_text(encoding="utf-8"))
    delivery = yaml.safe_load((external / "linear/projects.yaml").read_text(encoding="utf-8"))

    approved = {
        review["artifact_id"]: review["version"]
        for review in reviews["reviews"]
        if review["merged"]
    }
    projects = delivery["projects"]
    assert len({project["external_id"] for project in projects}) == len(projects) == 2
    assert all(project["approved_version"] == approved[project["prd_id"]] for project in projects)

    retry_attempts = [
        attempt
        for attempt in delivery["sync_attempts"]
        if attempt["idempotency_key"] == "prd_01JABCDE01"
    ]
    assert [attempt["result"] for attempt in retry_attempts] == [
        "timeout_after_provider_accept",
        "reused_existing",
    ]
    assert len({attempt["external_id"] for attempt in retry_attempts}) == 1


def test_new_evidence_produces_a_reviewed_material_change(repo_root: Path) -> None:
    workspace = repo_root / "examples/fixtures/valid-workspace"
    artifacts = _artifacts(workspace)
    challenging_signal = artifacts["signal_01JABCDE04"]
    assert challenging_signal["relationships"]["challenges"] == ["prd_01JABCDE02"]

    change = yaml.safe_load(
        (workspace / "external/git/prd-recovery-v2-material-change.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert change["artifact_id"] == "prd_01JABCDE02"
    assert change["material_changes"]["target_users"]["evidence"] == "signal_01JABCDE04"
    assert change["reviewed_by"]

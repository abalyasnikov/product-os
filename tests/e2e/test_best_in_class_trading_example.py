from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from product_decision_os.frontmatter import parse_markdown
from product_decision_os.validator import validate_workspace
from product_decision_os.reference_journey import REFERENCE_FIXTURE_ROOT, run_journey


HUMAN_EXAMPLE_ROOT = Path(__file__).resolve().parents[2] / "examples" / "best-in-class-trading-experience"


def test_human_trading_example_uses_lean_readable_documents() -> None:
    report = validate_workspace(HUMAN_EXAMPLE_ROOT)
    assert report.ok, [error.to_dict() for error in report.errors]

    documents = [
        parse_markdown(path)
        for path in sorted((HUMAN_EXAMPLE_ROOT / "product").glob("*/*.md"))
    ]
    assert len(documents) == 7
    assert {document.metadata["type"] for document in documents} == {
        "initiative",
        "prd",
        "learning",
    }
    assert sum(document.metadata["type"] == "prd" for document in documents) == 5

    narrative = [d for d in documents if d.metadata["type"] in {"initiative", "prd"}]
    for document in narrative:
        assert set(document.metadata) == {"schema_version", "id", "type", "title", "relationships"}
        assert len(document.body) > 1_000


def test_human_trading_example_closes_the_loop_on_one_barrier() -> None:
    """One barrier carries a measured result, and it closes honestly.

    The Learning keeps structured frontmatter because provenance and the decision
    must be machine-checkable; narrative artifacts stay lean by contrast.
    """
    learning = parse_markdown(
        HUMAN_EXAMPLE_ROOT / "product" / "learnings" / "auto-slippage-failure-rate.md"
    )
    assert learning.metadata["product_bet_id"] == "prd_01TRADX002"
    assert learning.metadata["outcome_contract_ref"] == {
        "owner_artifact_id": "prd_01TRADX002",
        "definition_version": "auto-slippage-v1",
    }

    # Guardrail results were never recovered, so the contract's decision rule
    # cannot be satisfied and the outcome decision must stop short of "scale".
    assert all(value is None for value in learning.metadata["results"]["guardrails"].values())
    assert learning.metadata["decision_events"][-1]["choice"] == "iterate"

    # The Initiative's aggregate outcome stays unmeasured; one child contract
    # passing is not evidence for the shared claim.
    initiative = parse_markdown(
        HUMAN_EXAMPLE_ROOT
        / "product"
        / "initiatives"
        / "best-in-class-trading-experience.md"
    )
    assert "learning" not in initiative.metadata.get("relationships", {})


def _artifacts(workspace: Path) -> dict[str, dict[str, object]]:
    artifacts: dict[str, dict[str, object]] = {}
    for path in sorted((workspace / "product").glob("*/*.md")):
        document = parse_markdown(path)
        artifacts[str(document.metadata["id"])] = document.metadata
    return artifacts


def test_reference_fixture_is_a_complete_multi_prd_product_bet() -> None:
    report = validate_workspace(REFERENCE_FIXTURE_ROOT, command="smoke-test")
    assert report.ok, [error.to_dict() for error in report.errors]

    artifacts = _artifacts(REFERENCE_FIXTURE_ROOT)
    by_type: dict[str, list[dict[str, object]]] = {}
    for artifact in artifacts.values():
        by_type.setdefault(str(artifact["type"]), []).append(artifact)

    assert {kind: len(items) for kind, items in by_type.items()} == {
        "initiative": 1,
        "learning": 1,
        "opportunity": 1,
        "pattern": 2,
        "prd": 4,
        "product_update": 1,
        "signal": 4,
    }
    initiative = by_type["initiative"][0]
    assert initiative["title"] == "Best-in-class trading experience"
    assert len(initiative["child_prd_ids"]) == 4
    assert set(initiative["child_prd_ids"]) == {
        artifact["id"] for artifact in by_type["prd"]
    }
    assert all(artifact["initiative_id"] == initiative["id"] for artifact in by_type["prd"])
    implementation_refs = [
        reference
        for artifact in by_type["prd"]
        for reference in artifact["implementation_refs"]
    ]
    assert len(implementation_refs) == 1
    assert implementation_refs[0]["based_on_prd_id"] == "prd_01TRADX001"

    learning = by_type["learning"][0]
    assert learning["product_bet_id"] == initiative["id"]
    assert learning["results"]["provenance"]["method"] in {
        "analytics_query",
        "manual_import",
    }
    assert learning["decision_events"][-1]["choice"] in {"iterate", "complete"}


@pytest.mark.parametrize("client", ["codex", "claude-code", "openclaw"])
def test_clean_install_reaches_final_learning_for_every_agent_client(
    tmp_path: Path, client: str
) -> None:
    workspace = tmp_path / client
    result = run_journey(workspace, client)

    assert result["status"] == "passed"
    assert result["scope"] == "deterministic_offline_reference"
    assert result["child_prds"] == 4
    assert result["artifacts"] == 14
    assert result["final_decision"] in {"iterate", "complete"}
    assert result["validation"]["errors"] == 0
    assert result["smoke_test"]["errors"] == 0
    assert result["not_proven"]

    final_artifacts = _artifacts(workspace)
    learning = next(
        artifact for artifact in final_artifacts.values() if artifact["type"] == "learning"
    )
    learning_basis = learning["decision_events"][-1]["based_on_version"]
    learning_path = next((workspace / "product" / "learnings").glob("*.md"))
    subprocess.run(
        [
            "git",
            "-C",
            str(workspace),
            "cat-file",
            "-e",
            f"{learning_basis}:{learning_path.relative_to(workspace).as_posix()}",
        ],
        check=True,
    )

    state = yaml.safe_load(
        (workspace / ".product-os" / "review-state.yaml").read_text(encoding="utf-8")
    )
    approved = state["approved_artifacts"]
    for prd_path in sorted((workspace / "product" / "prds").glob("*.md")):
        prd = parse_markdown(prd_path).metadata
        approval = approved[prd["id"]]
        assert approval["synthetic_reference"] is True
        assert approval["provenance"]["verification_mode"] == "solo_commit"
        subprocess.run(
            [
                "git",
                "-C",
                str(workspace),
                "cat-file",
                "-e",
                f"{approval['approved_version']}:{prd_path.relative_to(workspace).as_posix()}",
            ],
            check=True,
        )
    approval_message = subprocess.run(
        [
            "git",
            "-C",
            str(workspace),
            "show",
            "-s",
            "--format=%B",
            result["history"]["approved"],
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "Product-Approval: explicit" in approval_message.splitlines()

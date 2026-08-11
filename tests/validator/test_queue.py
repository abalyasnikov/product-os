"""The Decision Queue is the one place where a bug produces wrong product advice.

A missed state tells a Product Lead nothing is waiting on them. An invented one sends them to
review something that was never approved. Both are worse than an empty queue, so every state the
specification marks as needing a human is asserted here, and so is every state that must stay out.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import subprocess

import pytest
import yaml

from product_os.queue import compute_queue, render
from .test_validator import complete_outcome, metadata, write_artifact


AS_OF = date(2026, 8, 11)
TRAILER = "Product-Approval: explicit"


def _config(workspace: Path, mode: str = "solo") -> None:
    directory = workspace / ".product-os"
    directory.mkdir(parents=True, exist_ok=True)
    review = {
        "mode": mode,
        "approver_rule": {"initiative": "self", "prd": "self"},
        "solo_approval": {"allowed": mode == "solo", "commit_trailer": TRAILER},
        "git_capability": "git.commit.read" if mode == "solo" else "git.review.read",
    }
    (directory / "config.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "selected_client": "codex", "default_branch": "main", "review": review}),
        encoding="utf-8",
    )


def _git(workspace: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(workspace), *args], check=True, capture_output=True)


def _repo(workspace: Path) -> None:
    _git(workspace, "init", "-q", "-b", "main")
    _git(workspace, "config", "user.email", "test@example.invalid")
    _git(workspace, "config", "user.name", "Test")


def _commit(workspace: Path, message: str, *, approved: bool = False) -> None:
    _git(workspace, "add", "-A")
    args = ["commit", "-q", "-m", message]
    if approved:
        args += ["-m", TRAILER]
    _git(workspace, *args)


def _types(report) -> list[str]:
    return [item.type for item in report.items]


@pytest.fixture
def queue_workspace(tmp_path: Path) -> Path:
    _repo(tmp_path)
    _config(tmp_path)
    return tmp_path


def _opportunity(artifact_id: str = "opportunity_01QUEUE01", events: list | None = None) -> dict:
    data = metadata("opportunity", artifact_id)
    data["evidence_ids"] = ["signal_01QUEUE01"]
    data["evidence_quality"] = {"contradictions": [], "coverage_gaps": ["no cardholder interviewed"]}
    data["decision_events"] = events or []
    return data


def _pursue(decision_id: str = "decision_01QUEUE01", conditions: list | None = None) -> dict:
    event = {
        "id": decision_id,
        "kind": "opportunity",
        "choice": "pursue",
        "decided_by": "product-lead",
        "decided_at": "2026-08-01T12:00:00Z",
        "rationale": "Illustrative.",
        "based_on_version": "1" * 40,
    }
    if conditions:
        event["conditions"] = conditions
    return event


def test_undecided_opportunity_asks_for_the_human_decision(queue_workspace: Path) -> None:
    write_artifact(queue_workspace, _opportunity())
    report = compute_queue(queue_workspace, as_of=AS_OF)
    assert _types(report) == ["opportunity_decision"]
    item = report.items[0]
    assert item.decision_required == ("pursue", "hold", "reject")
    assert "no cardholder interviewed" in item.blocking_gaps


def test_pursued_opportunity_without_a_contract_stays_visible(queue_workspace: Path) -> None:
    """The state that used to disappear between the decision and the PRD."""
    write_artifact(queue_workspace, _opportunity(events=[_pursue()]))
    report = compute_queue(queue_workspace, as_of=AS_OF)
    assert _types(report) == ["bet_undrafted"]
    assert "no PRD or Initiative references it yet" in report.items[0].why_now


def test_unmet_decision_condition_surfaces_after_its_review_date(queue_workspace: Path) -> None:
    conditions = [{"statement": "Talk to three cardholders.", "review_by": "2026-07-01"}]
    write_artifact(queue_workspace, _opportunity(events=[_pursue(conditions=conditions)]))
    report = compute_queue(queue_workspace, as_of=AS_OF)
    assert "overdue_condition" in _types(report)
    assert report.items[0].type == "overdue_condition", "overdue items sort first"

    earlier = compute_queue(queue_workspace, as_of=date(2026, 6, 1))
    assert "overdue_condition" not in _types(earlier), "a condition is not overdue before its date"


def test_unapproved_contract_asks_for_review_and_hides_downstream_states(queue_workspace: Path) -> None:
    write_artifact(queue_workspace, _opportunity(events=[_pursue()]))
    prd = metadata("prd", "prd_01QUEUE01")
    prd["relationships"] = {"opportunity": "opportunity_01QUEUE01"}
    prd["outcome"] = complete_outcome("planned")
    write_artifact(queue_workspace, prd)
    _commit(queue_workspace, "draft the contract")

    report = compute_queue(queue_workspace, as_of=AS_OF)
    assert _types(report) == ["contract_review"]
    assert "never been approved" in report.items[0].why_now


def test_approved_contract_without_an_anchor_asks_for_one(queue_workspace: Path) -> None:
    write_artifact(queue_workspace, _opportunity(events=[_pursue()]))
    prd = metadata("prd", "prd_01QUEUE01")
    prd["relationships"] = {"opportunity": "opportunity_01QUEUE01"}
    outcome = complete_outcome("planned")
    outcome["binding"].pop("measurement_anchor", None)
    prd["outcome"] = outcome
    write_artifact(queue_workspace, prd)
    _commit(queue_workspace, "approve the contract", approved=True)

    report = compute_queue(queue_workspace, as_of=AS_OF)
    assert _types(report) == ["measurement_anchor"]
    assert report.items[0].blocking_gaps, "delivery state is unknown and must be said so"


def test_editing_an_approved_contract_returns_it_to_review(queue_workspace: Path) -> None:
    write_artifact(queue_workspace, _opportunity(events=[_pursue()]))
    prd = metadata("prd", "prd_01QUEUE01")
    prd["relationships"] = {"opportunity": "opportunity_01QUEUE01"}
    prd["outcome"] = complete_outcome("planned")
    path = write_artifact(queue_workspace, prd)
    _commit(queue_workspace, "approve the contract", approved=True)
    assert _types(compute_queue(queue_workspace, as_of=AS_OF)) != ["contract_review"]

    path.write_text(path.read_text(encoding="utf-8") + "\nA later edit.\n", encoding="utf-8")
    _commit(queue_workspace, "revise after approval")
    report = compute_queue(queue_workspace, as_of=AS_OF)
    assert "contract_review" in _types(report)
    assert "human judgment" in report.items[0].why_now, "materiality is not decided by the tool"


def test_learning_without_a_decision_is_the_outcome_call(queue_workspace: Path) -> None:
    write_artifact(queue_workspace, _opportunity(events=[_pursue()]))
    prd = metadata("prd", "prd_01QUEUE01")
    prd["relationships"] = {"opportunity": "opportunity_01QUEUE01"}
    prd["outcome"] = complete_outcome("planned")
    write_artifact(queue_workspace, prd)
    learning = metadata("learning", "learning_01QUEUE01")
    learning["relationships"] = {"prds": ["prd_01QUEUE01"]}
    learning["product_bet_id"] = "prd_01QUEUE01"
    write_artifact(queue_workspace, learning)
    _commit(queue_workspace, "record the learning", approved=True)

    report = compute_queue(queue_workspace, as_of=AS_OF)
    assert "outcome_decision" in _types(report)
    item = next(entry for entry in report.items if entry.type == "outcome_decision")
    assert item.decision_required == ("scale", "iterate", "hold", "kill", "complete")


def test_provider_mode_reports_unknown_rather_than_falling_back(tmp_path: Path) -> None:
    """Never resolve approval through the other review mode; say it was not checked."""
    _repo(tmp_path)
    _config(tmp_path, mode="provider")
    write_artifact(tmp_path, _opportunity(events=[_pursue()]))
    prd = metadata("prd", "prd_01QUEUE01")
    prd["relationships"] = {"opportunity": "opportunity_01QUEUE01"}
    prd["outcome"] = complete_outcome("planned")
    write_artifact(tmp_path, prd)
    _commit(tmp_path, "draft with a solo trailer that provider mode must ignore", approved=True)

    report = compute_queue(tmp_path, as_of=AS_OF)
    assert "contract_review" not in _types(report)
    assert any("git.review.read" in gap for gap in report.gaps)


def test_expired_strategy_is_one_item_for_the_workspace(queue_workspace: Path) -> None:
    context = queue_workspace / "context"
    context.mkdir()
    (context / "strategy.md").write_text(
        "---\nupdated: 2025-01-01\nreview_by: 2026-01-01\n---\n\n# Strategy\n", encoding="utf-8"
    )
    write_artifact(queue_workspace, _opportunity())
    write_artifact(queue_workspace, _opportunity("opportunity_01QUEUE02"))
    report = compute_queue(queue_workspace, as_of=AS_OF)
    assert _types(report).count("expired_strategy") == 1


def test_missing_strategy_is_a_named_gap_not_silence(queue_workspace: Path) -> None:
    report = compute_queue(queue_workspace, as_of=AS_OF)
    assert any("context/strategy.md" in gap for gap in report.gaps)


def test_empty_workspace_says_so_and_writes_nothing(queue_workspace: Path) -> None:
    before = sorted(path.name for path in queue_workspace.iterdir())
    report = compute_queue(queue_workspace, as_of=AS_OF)
    assert report.items == []
    assert "No product decisions need attention right now" in render(report)
    assert sorted(path.name for path in queue_workspace.iterdir()) == before

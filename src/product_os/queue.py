"""Compute the Decision Queue from repository truth.

The queue is a filter over the derived lifecycle: every state the specification marks as needing
a human appears here, and nothing else does. It is computed on request and never written, so the
repository keeps no inbox, no index, and no status field anybody could edit.

What cannot be established from the repository is reported as a named gap. A queue that guesses is
worse than no queue, because the reader cannot tell an empty queue from an unchecked one.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from .frontmatter import FrontmatterError, MarkdownDocument, parse_markdown, structured_blocks


# Lower sorts first. Mirrors the specification's ordering: overdue dates, then decisions that are
# ready now, then reviews, then the Opportunity decision, then evidence gaps.
ORDER = {
    "overdue_condition": 0,
    "expired_strategy": 1,
    "overdue_waiver": 2,
    "outcome_decision": 3,
    "measurement_anchor": 4,
    "no_path_to_measurement": 5,
    "contract_review": 6,
    "bet_undrafted": 7,
    "opportunity_decision": 8,
}
BET_TYPES = {"prd", "initiative"}


@dataclass(frozen=True)
class QueueItem:
    type: str
    artifact_id: str | None
    title: str
    why_now: str
    decision_required: tuple[str, ...]
    recommended_next_action: str
    evidence: tuple[str, ...] = ()
    owner: str | None = None
    blocking_gaps: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "artifact_id": self.artifact_id,
            "title": self.title,
            "why_now": self.why_now,
            "decision_required": list(self.decision_required),
            "evidence": list(self.evidence),
            "owner": self.owner,
            "blocking_gaps": list(self.blocking_gaps),
            "recommended_next_action": self.recommended_next_action,
        }


@dataclass
class QueueReport:
    workspace: Path
    as_of: date
    items: list[QueueItem] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace": str(self.workspace),
            "as_of": self.as_of.isoformat(),
            "items": [item.to_dict() for item in self.items],
            "gaps": self.gaps,
            "summary": self.summary,
        }


def _as_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def _git(workspace: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(workspace), *args], capture_output=True, text=True, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


@dataclass
class _Approval:
    state: str  # approved | changed_since_approval | never_approved | unknown
    version: str | None = None
    reason: str | None = None


def _resolve_approval(workspace: Path, relative: str, trailer: str) -> _Approval:
    """Solo mode only: the approved version is the commit carrying the configured trailer."""
    history = _git(workspace, "log", "--format=%H%x1f%B%x1e", "--", relative)
    if history is None:
        return _Approval("unknown", reason="Git history is unavailable for this workspace.")
    commits: list[tuple[str, str]] = []
    for record in history.split("\x1e"):
        record = record.strip()
        if not record or "\x1f" not in record:
            continue
        sha, message = record.split("\x1f", 1)
        commits.append((sha.strip(), message))
    if not commits:
        return _Approval("never_approved", reason="The artifact has never been committed.")
    for index, (sha, message) in enumerate(commits):
        if trailer in message:
            if index == 0:
                return _Approval("approved", version=sha)
            return _Approval("changed_since_approval", version=sha)
    return _Approval("never_approved")


class _Workspace:
    def __init__(self, workspace: Path, as_of: date) -> None:
        self.root = workspace
        self.as_of = as_of
        self.gaps: list[str] = []
        self.config = self._load_config()
        self.documents = self._load_documents()
        self.by_id = {
            str(document.metadata.get("id")): document
            for document in self.documents
            if isinstance(document.metadata.get("id"), str)
        }

    def _load_config(self) -> dict[str, Any]:
        path = self.root / ".product-os" / "config.yaml"
        if not path.is_file():
            self.gaps.append(
                "No `.product-os/config.yaml`: review mode and connectors are unknown, so approval "
                "state could not be resolved."
            )
            return {}
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError):
            self.gaps.append("`.product-os/config.yaml` could not be read; approval state is unknown.")
            return {}
        return value if isinstance(value, Mapping) else {}

    def _load_documents(self) -> list[MarkdownDocument]:
        product = self.root / "product"
        documents: list[MarkdownDocument] = []
        if not product.is_dir():
            return documents
        for path in sorted(product.glob("*/*.md")):
            try:
                documents.append(parse_markdown(path))
            except (FrontmatterError, OSError, UnicodeError):
                self.gaps.append(
                    f"`{path.relative_to(self.root).as_posix()}` could not be parsed and was skipped."
                )
        return documents

    def relative(self, document: MarkdownDocument) -> str:
        return document.path.relative_to(self.root).as_posix()

    def outcome(self, document: MarkdownDocument) -> Mapping[str, Any] | None:
        try:
            value = structured_blocks(document).get("outcome")
        except FrontmatterError:
            return None
        return value if isinstance(value, Mapping) else None

    def of_type(self, *types: str) -> list[MarkdownDocument]:
        wanted = set(types)
        return [
            document
            for document in self.documents
            if str(document.metadata.get("type", "")).replace("-", "_") in wanted
        ]

    def title(self, document: MarkdownDocument) -> str:
        value = document.metadata.get("title")
        return value if isinstance(value, str) and value else self.relative(document)


def _relationships(document: MarkdownDocument) -> Mapping[str, Any]:
    value = document.metadata.get("relationships")
    return value if isinstance(value, Mapping) else {}


def _decision_events(document: MarkdownDocument) -> list[Mapping[str, Any]]:
    value = document.metadata.get("decision_events")
    if not isinstance(value, list):
        return []
    return [event for event in value if isinstance(event, Mapping)]


def _collect_opportunity_items(space: _Workspace, items: list[QueueItem]) -> None:
    bets_by_opportunity: dict[str, list[MarkdownDocument]] = {}
    for bet in space.of_type(*BET_TYPES):
        opportunity = _relationships(bet).get("opportunity")
        if isinstance(opportunity, str):
            bets_by_opportunity.setdefault(opportunity, []).append(bet)
    for opportunity in space.of_type("opportunity"):
        artifact_id = str(opportunity.metadata.get("id"))
        events = _decision_events(opportunity)
        if not events:
            items.append(
                QueueItem(
                    type="opportunity_decision",
                    artifact_id=artifact_id,
                    title=space.title(opportunity),
                    why_now="An Opportunity is recorded and no human decision is attached to it.",
                    decision_required=("pursue", "hold", "reject"),
                    evidence=tuple(
                        str(item) for item in opportunity.metadata.get("evidence_ids", []) or []
                    ),
                    blocking_gaps=tuple(
                        str(gap)
                        for gap in (opportunity.metadata.get("evidence_quality") or {}).get(
                            "coverage_gaps", []
                        )
                        or []
                    ),
                    recommended_next_action=(
                        f"Open `{space.relative(opportunity)}`, read its contradictions and coverage "
                        "gaps, then record pursue, hold, or reject."
                    ),
                )
            )
            continue
        latest = events[-1]
        if latest.get("choice") != "pursue":
            continue
        # An Opportunity the team decided to act on, with nothing drafted against it yet, is the
        # state that used to fall out of view entirely between the decision and the PRD.
        linked = bets_by_opportunity.get(artifact_id, [])
        if not linked:
            items.append(
                QueueItem(
                    type="bet_undrafted",
                    artifact_id=artifact_id,
                    title=space.title(opportunity),
                    why_now=(
                        f"Pursued on {latest.get('decided_at', 'an unrecorded date')} and no PRD or "
                        "Initiative references it yet."
                    ),
                    decision_required=("draft the contract", "supersede the decision"),
                    owner=str(latest.get("decided_by")) if latest.get("decided_by") else None,
                    recommended_next_action=(
                        f"Interrogate for a standalone PRD from `{artifact_id}`, or append a "
                        "superseding decision if the bet no longer holds."
                    ),
                )
            )
        for event in events:
            for condition in event.get("conditions", []) or []:
                if not isinstance(condition, Mapping):
                    continue
                review_by = _as_date(condition.get("review_by"))
                if review_by is None or review_by >= space.as_of:
                    continue
                items.append(
                    QueueItem(
                        type="overdue_condition",
                        artifact_id=artifact_id,
                        title=space.title(opportunity),
                        why_now=(
                            f"A condition attached to this decision came due on "
                            f"{review_by.isoformat()}: {condition.get('statement')}"
                        ),
                        decision_required=("confirm", "waive", "supersede"),
                        owner=str(event.get("decided_by")) if event.get("decided_by") else None,
                        recommended_next_action=(
                            "Confirm the condition was met, record an explicit waiver, or append a "
                            "superseding decision. Do not leave it unanswered."
                        ),
                    )
                )


def _collect_bet_items(space: _Workspace, items: list[QueueItem]) -> None:
    review = space.config.get("review") if isinstance(space.config.get("review"), Mapping) else {}
    mode = review.get("mode")
    trailer = ((review.get("solo_approval") or {}) if isinstance(review.get("solo_approval"), Mapping) else {}).get(
        "commit_trailer"
    )
    learnings_by_bet: dict[str, list[MarkdownDocument]] = {}
    for learning in space.of_type("learning"):
        bet_id = learning.metadata.get("product_bet_id")
        if isinstance(bet_id, str):
            learnings_by_bet.setdefault(bet_id, []).append(learning)

    for bet in space.of_type(*BET_TYPES):
        artifact_id = str(bet.metadata.get("id"))
        relative = space.relative(bet)
        title = space.title(bet)
        outcome = space.outcome(bet)
        binding = outcome.get("binding") if isinstance(outcome, Mapping) else None
        binding = binding if isinstance(binding, Mapping) else {}

        if mode == "solo" and isinstance(trailer, str):
            approval = _resolve_approval(space.root, relative, trailer)
        elif mode == "provider":
            approval = _Approval(
                "unknown",
                reason="Provider review mode needs `git.review.read`; approval state was not checked.",
            )
        else:
            approval = _Approval("unknown", reason="Review mode is not configured.")

        if approval.state == "unknown" and approval.reason:
            gap = f"Approval for `{artifact_id}` is unknown. {approval.reason}"
            if gap not in space.gaps:
                space.gaps.append(gap)
        if approval.state in {"never_approved", "changed_since_approval"}:
            why = (
                "The contract has never been approved."
                if approval.state == "never_approved"
                else f"The artifact changed after its approved version `{(approval.version or '')[:12]}`; "
                "whether the change is material is a human judgment."
            )
            items.append(
                QueueItem(
                    type="contract_review",
                    artifact_id=artifact_id,
                    title=title,
                    why_now=why,
                    decision_required=("approve", "request changes"),
                    recommended_next_action=(
                        f"Review `{relative}` against its latest Git diff and record approval, or "
                        "state what blocks it."
                    ),
                )
            )
            continue  # nothing downstream of approval applies yet

        if approval.state != "approved":
            continue

        anchor = binding.get("measurement_anchor")
        anchor = anchor if isinstance(anchor, Mapping) else None
        status = binding.get("status")
        learnings = learnings_by_bet.get(artifact_id, [])

        if status in {None, "unconfigured"} or (anchor is not None and status == "planned"):
            items.append(
                QueueItem(
                    type="no_path_to_measurement",
                    artifact_id=artifact_id,
                    title=title,
                    why_now=(
                        "The contract is approved and its measurement binding is "
                        f"`{status or 'absent'}`, so nothing can currently produce the result its "
                        "decision rule depends on."
                    ),
                    decision_required=("assign an owner", "change the contract"),
                    owner=str(binding.get("owner")) if binding.get("owner") else None,
                    recommended_next_action=(
                        "Name who builds the measurement and by when, or revise the Outcome "
                        "Contract to something the team can actually observe."
                    ),
                )
            )
        elif anchor is None and not learnings:
            items.append(
                QueueItem(
                    type="measurement_anchor",
                    artifact_id=artifact_id,
                    title=title,
                    why_now=(
                        "The contract is approved with a resolved binding and no measurement anchor "
                        "is recorded, so the observation window has not started."
                    ),
                    decision_required=("record the anchor", "state that it cannot start"),
                    owner=str(binding.get("owner")) if binding.get("owner") else None,
                    blocking_gaps=(
                        "Delivery state was not read; whether the change shipped is unknown here.",
                    ),
                    recommended_next_action=(
                        "Record the actual exposure, release, or manual evaluation event, or say "
                        "plainly that the window cannot start yet."
                    ),
                )
            )

        for learning in learnings:
            if _decision_events(learning):
                continue
            items.append(
                QueueItem(
                    type="outcome_decision",
                    artifact_id=str(learning.metadata.get("id")),
                    title=space.title(learning),
                    why_now="A Learning is recorded against this bet and carries no outcome decision.",
                    decision_required=("scale", "iterate", "hold", "kill", "complete"),
                    evidence=(artifact_id,),
                    recommended_next_action=(
                        f"Compare `{space.relative(learning)}` with the approved Outcome Contract, "
                        "then record the decision and its rationale."
                    ),
                )
            )


def _collect_waiver_items(space: _Workspace, items: list[QueueItem]) -> None:
    for document in space.documents:
        waiver = document.metadata.get("evidence_waiver")
        if not isinstance(waiver, Mapping):
            continue
        review_date = _as_date(waiver.get("review_date"))
        if review_date is None or review_date >= space.as_of:
            continue
        items.append(
            QueueItem(
                type="overdue_waiver",
                artifact_id=str(document.metadata.get("id")),
                title=space.title(document),
                why_now=(
                    f"The evidence waiver on this artifact came up for review on "
                    f"{review_date.isoformat()} and the assumption it covers is still unconfirmed."
                ),
                decision_required=("confirm", "withdraw", "renew"),
                owner=str(waiver.get("approved_by")) if waiver.get("approved_by") else None,
                blocking_gaps=(str(waiver.get("assumption")),) if waiver.get("assumption") else (),
                recommended_next_action=(
                    "Get the evidence the waiver stood in for, or record that the assumption is "
                    "now accepted and why."
                ),
            )
        )


def _collect_strategy_item(space: _Workspace, items: list[QueueItem]) -> None:
    path = space.root / "context" / "strategy.md"
    if not path.is_file():
        space.gaps.append(
            "No `context/strategy.md`: every strategic-fit judgment in this workspace is an "
            "explicit gap until it exists."
        )
        return
    try:
        document = parse_markdown(path)
    except (FrontmatterError, OSError, UnicodeError):
        space.gaps.append("`context/strategy.md` could not be parsed; its review date is unknown.")
        return
    review_by = _as_date(document.metadata.get("review_by"))
    if review_by is None:
        space.gaps.append("`context/strategy.md` records no `review_by`, so staleness cannot be judged.")
        return
    if review_by >= space.as_of:
        return
    items.append(
        QueueItem(
            type="expired_strategy",
            artifact_id=None,
            title="Strategy context is past its review date",
            why_now=(
                f"`context/strategy.md` was due for review on {review_by.isoformat()}. Until it is "
                "confirmed, every strategic-fit judgment rests on a document nobody has checked."
            ),
            decision_required=("confirm", "revise"),
            recommended_next_action=(
                "Read it, confirm or revise it, and move `review_by` forward. One item for the "
                "workspace, not one per affected artifact."
            ),
        )
    )


def compute_queue(workspace: Path, *, as_of: date | None = None) -> QueueReport:
    resolved = workspace.resolve()
    today = as_of or datetime.now(timezone.utc).date()
    space = _Workspace(resolved, today)
    items: list[QueueItem] = []
    _collect_strategy_item(space, items)
    _collect_opportunity_items(space, items)
    _collect_bet_items(space, items)
    _collect_waiver_items(space, items)
    items.sort(key=lambda item: (ORDER.get(item.type, 99), item.artifact_id or "", item.title))
    report = QueueReport(workspace=resolved, as_of=today, items=items, gaps=space.gaps)
    report.summary = {
        "artifacts": len(space.documents),
        "items": len(items),
        "bets": len(space.of_type(*BET_TYPES)),
        "gaps": len(space.gaps),
    }
    return report


def render(report: QueueReport) -> str:
    lines: list[str] = []
    if not report.items:
        lines.append("No product decisions need attention right now.")
    else:
        for index, item in enumerate(report.items, start=1):
            lines.append(f"{index}. {item.title} — {', '.join(item.decision_required)} — {item.why_now}")
            lines.append(f"   next: {item.recommended_next_action}")
            for gap in item.blocking_gaps:
                lines.append(f"   gap: {gap}")
    if report.gaps:
        lines.append("")
        lines.append("Could not be checked:")
        lines.extend(f"- {gap}" for gap in report.gaps)
    lines.append("")
    lines.append(
        f"{report.summary['items']} decision(s) across {report.summary['bets']} bet(s), "
        f"{report.summary['artifacts']} artifact(s), as of {report.as_of.isoformat()}."
    )
    return "\n".join(lines)

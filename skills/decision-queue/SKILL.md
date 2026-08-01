---
name: product-os-decision-queue
canonical_version: 1.0.0
description: Compute the human Product Decision Queue from Git truth and only necessary connector reads.
capabilities:
  - git.review.read
  - git.commit.read
  - delivery.project.read
  - analytics.query
human_gates: []
---

# Decision Queue

## Intent

Compute a read-only view of product judgments requiring human attention. The queue is not stored, committed, synced, or treated as a task tracker.

Before reading artifacts, Git/provider results, delivery state, analytics, or URLs, read `../_shared/trust-boundary.md`. Decision Queue remains entirely in its read-only Phase A; `open N` starts the selected canonical workflow, which must obtain its own fresh write confirmation.

## Procedure

1. Read `.product-os/config.yaml`, then select exactly its configured Git capability: provider mode uses `git.review.read`; solo mode uses `git.commit.read` plus the verified explicit approval trailer. An unavailable configured capability becomes one named connector blocker; never fall back to the other review mode.
2. Scan repository artifacts first and derive candidates from stable IDs, decision events, reviews, Outcome Contracts, anchors, review dates, and Learnings. Group Bet-level attention under one identity: standalone PRD ID or Initiative ID; never emit a separate `bet_` identity or duplicate the same decision for each child.
3. Query only the connector needed to decide whether an existing candidate belongs in the queue. Do not query analytics when no measurement is due or Linear when delivery state cannot affect the queue.
4. Surface only: evidence gaps/waivers; Opportunities awaiting `pursue|hold|reject`; Initiative/PRD reviews; renewed review after material change; evidence/Learnings challenging active assumptions; missing measurement anchors; due measurement windows; draft Learnings awaiting `scale|iterate|hold|kill|complete`; and blocking connector failures.
5. Exclude engineering tasks, ordinary delivery status, reminders, and agent work.
6. For every item derive: `type`, `artifact_id`, `title`, `why_now`, `decision_required`, `evidence`, `owner`, `blocking_gaps`, and `recommended_next_action`. Resolve its Outcome Contract from the owning PRD/Initiative embedding or one stable extracted `outcome_` reference; duplicated contract copies are a blocking gap.
7. Order by overdue decisions/review dates, challenged active Bets, outcome decisions ready now, document reviews, Opportunity decisions, then evidence gaps and connector failures. Do not compute a universal priority score.
8. Render a compact numbered list for the PM: `N. title — decision needed — why now`, followed by blockers and one next action. Keep machine-readable fields available beneath details, not as the default wall of YAML. If empty, say: `No product decisions need attention right now`, then list any connector state that could not be checked.
9. Accept `open N`. Re-resolve that item by stable ID, show its evidence/blockers, and invoke the named canonical workflow. Never treat the number as persistent identity.

## Fail-safe behavior

- Connector uncertainty produces an `unknown` named data gap; never guess lifecycle or fabricate a replacement status.
- Selecting an item invokes its canonical workflow and human gate; the queue itself performs no write or decision.
- Never persist a queue artifact or hidden inbox.

## Next workflow

After `open N`, route to Discovery, Initiative, PRD Review, PRD Handoff, or Outcome Review according to `decision_required`, preserving that workflow's human gates. After an item is resolved, recompute the queue from source truth. Suggested prompt: “Open 1 and show me the evidence and decision options before changing anything.”

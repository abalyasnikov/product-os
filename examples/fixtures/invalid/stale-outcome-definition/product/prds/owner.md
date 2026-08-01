---
schema_version: 1
id: prd_01JSTAED01
type: prd
title: Owner PRD for stale binding fixture
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-01-01T00:00:00Z"
authors: [fixture-author]
relationships:
  opportunity: opportunity_01JSTAED01
  signal: signal_01JSTAED01
  outcome_contract: outcome_01JSTAED01
opportunity_id: opportunity_01JSTAED01
problem: Synthetic problem.
target_users: Synthetic users.
evidence_ids: [signal_01JSTAED01]
current_journey: Synthetic current journey.
desired_journey: Synthetic desired journey.
target_outcome: Synthetic owner outcome.
requirements: [Synthetic requirement]
non_goals: [Engineering design]
outcome:
  definition:
    version: owner-definition-v1
    method: behavioral_metric
    baseline: 0.10
    target: 0.20
    metric: synthetic owner metric
    window: 7 days
    slices: [fixture]
    guardrails: [synthetic_guardrail]
    decision_rule: Hold unless the synthetic target passes.
  binding:
    status: planned
    owner: fixture-author
    due_before: release
risks: [Synthetic risk]
dependencies: []
gtm_hypothesis:
  status: not_applicable
  reason: Synthetic validation fixture.
implementation_refs: []
delivery_refs: []
---

Synthetic owner artifact.

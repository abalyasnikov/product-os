---
schema_version: 1
id: prd_01JSTAE001
type: prd
title: PRD with stale Implementation Plan reference
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-02-01T00:00:00Z"
authors: [fixture-author]
relationships: {}
opportunity_id: opportunity_01JSTAE001
problem: Synthetic problem.
target_users: Synthetic users.
evidence_ids: [signal_01JSTAE001]
current_journey: Current synthetic journey.
desired_journey: Desired synthetic journey.
target_outcome: Synthetic outcome.
requirements: [One synthetic requirement]
non_goals: [Engineering design]
outcome:
  definition:
    version: stale-plan-definition-v1
    method: acceptance_journey
    baseline: failing
    target: passing
    metric: synthetic journey
    window: before release
    slices: [segment_a]
    guardrails: [synthetic_guardrail]
    decision_rule: Ship only when the journey passes.
    cases:
      - id: synthetic-pass
        description: Synthetic user completes the journey.
        expected: pass
      - id: synthetic-fail
        description: Synthetic user cannot complete the journey.
        expected: fail
  binding:
    status: planned
    owner: fixture-author
    due_before: release
risks: [Synthetic risk]
dependencies: []
gtm_hypothesis:
  status: not_applicable
  reason: Synthetic internal fixture.
implementation_refs:
  - repository: github.com/example/synthetic-app
    path: specs/stale-plan.md
    based_on_prd_id: prd_01JSTAE001
    based_on_prd_version: prd-old-v1
delivery_refs: []
---

Expected failure: the plan is based on `prd-old-v1`, but the approved PRD version is `prd-current-v2`.

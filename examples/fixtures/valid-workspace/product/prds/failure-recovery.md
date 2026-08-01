---
schema_version: 1
id: prd_01JABCDE02
type: prd
title: Guided transaction failure recovery
created_at: "2026-05-10T10:00:00Z"
updated_at: "2026-06-05T17:00:00Z"
authors: [product-lead]
relationships:
  opportunity: opportunity_01JABCDE01
  initiative: initiative_01JABCDE01
  signals: [signal_01JABCDE02, signal_01JABCDE04]
opportunity_id: opportunity_01JABCDE01
initiative_id: initiative_01JABCDE01
problem: New and returning users cannot understand or recover from a rejected transaction without leaving the flow.
target_users: New and returning users whose transaction is rejected before submission or fails after submission.
evidence_ids: [signal_01JABCDE02, signal_01JABCDE04, pattern_01JABCDE01]
current_journey: A generic failure state sends users away from the transaction flow without a safe next action.
desired_journey: The failure state names the observable cause category and offers a safe retry, adjustment, or exit action.
target_outcome: Users recover from a recoverable failure without external support.
requirements: [Explain the failure category without claiming certainty the system lacks, Offer a safe next action in the same flow, Cover new and returning users]
non_goals: [Eliminating upstream network failures, Building a support ticket system, Defining backend retry architecture]
outcome:
  definition:
    version: recovery-metric-v2
    method: behavioral_metric
    baseline: 0.18
    target: 0.28
    metric: users completing a transaction within one session after a recoverable failure
    window: 14 days after first eligible exposure
    slices: [new_users, returning_users]
    guardrails: [repeat_failure_rate]
    decision_rule: Iterate unless recovery reaches 0.28 in aggregate with no slice decline or repeat-failure regression.
  binding:
    status: manual
    provider: manual-import
    owner: analytics-lead
    measurement_anchor:
      type: exposure_event
      reference: exposure-fixture-rollout-01
      occurred_at: "2026-07-01T09:00:00Z"
risks: [Incorrect guidance could cause repeated failures, Failure categories may be incomplete]
dependencies: [Failure causes can be normalized into user-safe categories]
gtm_hypothesis:
  status: applicable
  audience: Users encountering a recoverable transaction failure
  promise: Understand what happened and take a safe next step
  discovery_channel: In-flow failure state
  adoption_action: Retry or adjust and complete the transaction
  launch_measurement: Same-session completion after recoverable failure
implementation_refs: []
delivery_refs:
  - provider: linear
    external_id: linear-project-recovery-fixture
    url: https://linear.example.invalid/project/recovery-fixture
    synced_from_version: "5555555555555555555555555555555555555555"
---

## Material update

The approved target-user scope now includes returning users because `signal_01JABCDE04` challenged the original assumption.

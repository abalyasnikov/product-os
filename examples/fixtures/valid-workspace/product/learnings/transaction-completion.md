---
schema_version: 1
id: learning_01JABCDE01
type: learning
title: Transaction completion improved without slice decline
created_at: "2026-07-20T11:00:00Z"
updated_at: "2026-07-20T12:00:00Z"
authors: [product-lead, analytics-lead]
relationships:
  initiative: initiative_01JABCDE01
  prds: [prd_01JABCDE01, prd_01JABCDE02]
  update: update_01JABCDE01
product_bet_id: initiative_01JABCDE01
outcome_contract_ref:
  owner_artifact_id: initiative_01JABCDE01
  definition_version: metric-v2
measurement_anchor:
  type: exposure_event
  reference: exposure-fixture-rollout-01
  occurred_at: "2026-07-01T09:00:00Z"
evaluation_scope: Eligible funded users in the fixture rollout from 2026-07-01 through 2026-07-15.
results:
  baseline: 0.22
  observed: 0.31
  by_slice:
    new_users: 0.30
    returning_users: 0.33
  guardrails:
    failed_transaction_rate: no_material_regression
    power_user_completion_time: no_material_regression
  provenance:
    method: analytics_query
    provider: amplitude
    reference: amp-fixture-first-transaction-v2
    definition_version: metric-v2
    retrieved_at: "2026-07-20T10:00:00Z"
confidence: medium
confounders: [Fixture rollout includes both child interventions]
data_limitations: [Fixture data proves workflow shape, not a real causal result]
thesis_change: The shared outcome passed; further work should test whether either intervention can be simplified without losing the gain.
decision_events:
  - id: decision_01JABCDE02
    kind: outcome
    choice: scale
    decided_by: product-lead
    decided_at: "2026-07-20T12:00:00Z"
    rationale: The target passed in aggregate and both required slices without material guardrail regression.
    based_on_version: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
---

## Interpretation

The fixture result supports scaling the intervention while retaining explicit uncertainty about each child intervention's independent contribution.

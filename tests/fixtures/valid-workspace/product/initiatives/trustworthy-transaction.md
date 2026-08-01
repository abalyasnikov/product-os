---
schema_version: 1
id: initiative_01JABCDE01
type: initiative
title: Trustworthy transaction journey
created_at: "2026-05-09T09:00:00Z"
updated_at: "2026-07-20T12:00:00Z"
authors: [product-lead]
relationships:
  opportunity: opportunity_01JABCDE01
  prds: [prd_01JABCDE01, prd_01JABCDE02]
  learning: learning_01JABCDE01
opportunity_id: opportunity_01JABCDE01
target_outcome: Funded users complete a first transaction with clear expectations and recover when it fails.
product_thesis: Solving route comprehension and failure recovery together will improve completion without degrading the expert path.
evidence_ids: [opportunity_01JABCDE01, pattern_01JABCDE01, signal_01JABCDE01, signal_01JABCDE02, signal_01JABCDE03, signal_01JABCDE04]
business_impact: More funded users reach the product's core transaction value; no revenue forecast is asserted.
gtm_hypothesis:
  status: applicable
  audience: Funded users who have not completed a transaction
  promise: Understand the route, confirm confidently, and recover without leaving the flow
  discovery_channel: In-product transaction entry point
  adoption_action: Complete a transaction or a guided recovery
  launch_measurement: Funded-user transaction completion within fourteen days of first exposure
outcome:
  definition:
    version: metric-v2
    method: behavioral_metric
    baseline: 0.22
    target: 0.30
    metric: funded users completing a first transaction
    window: 14 days after first eligible exposure
    slices: [new_users, returning_users]
    guardrails: [failed_transaction_rate, power_user_completion_time]
    decision_rule: Scale if completion is at least 0.30 in aggregate, neither slice declines, and guardrails do not regress materially.
  binding:
    status: executable
    provider: amplitude
    query_reference: amp-fixture-first-transaction-v2
    metric_definition_reference: metric-fixture-funded-completion
    definition_version: metric-v2
    verified_by: analytics-lead
    verified_at: "2026-07-01T10:00:00Z"
    owner: analytics-lead
    measurement_anchor:
      type: exposure_event
      reference: exposure-fixture-rollout-01
      occurred_at: "2026-07-01T09:00:00Z"
barriers: [Users cannot compare route expectations, Users cannot recover after a rejected transaction]
child_prd_ids: [prd_01JABCDE01, prd_01JABCDE02]
dependencies: [Eligible-exposure event is available to analytics]
sequencing: [Route comprehension and recovery can ship independently, Measure the shared outcome after both are exposed]
learnings: [learning_01JABCDE01]
---

## Bet boundary

This Initiative measures the shared completion outcome. Each child PRD measures removal of its own barrier.

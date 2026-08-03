---
schema_version: 1
id: learning_01TRADX001
type: learning
title: Trading continuity improved across the reference journey
created_at: "2025-05-30T11:00:00Z"
updated_at: "2025-05-30T12:00:00Z"
authors: [product-lead, analytics-lead]
relationships:
  initiative: initiative_01TRADX001
  prds: [prd_01TRADX001, prd_01TRADX003, prd_01TRADX004, prd_01TRADX005]
  update: update_01TRADX001
product_bet_id: initiative_01TRADX001
outcome_contract_ref:
  owner_artifact_id: initiative_01TRADX001
  definition_version: trading-initiative-metric-v1
measurement_anchor:
  type: exposure_event
  reference: exposure-synthetic-trading-rollout-01
  occurred_at: "2025-05-01T09:00:00Z"
evaluation_scope: Synthetic eligible sessions from 2025-05-01 through 2025-05-28; the snapshot demonstrates the workflow and is not production evidence.
results:
  baseline: "illustrative synthetic 42%"
  observed: "illustrative synthetic 64%"
  by_slice:
    cross_chain_swap: "illustrative synthetic 61%"
    native_asset_trade: "illustrative synthetic 72%"
    transaction_status: "illustrative synthetic 63%"
    bridge_settlement: "illustrative synthetic 60%"
  guardrails:
    failed_transaction_rate: "illustrative synthetic no material regression"
    signature_comprehension: "illustrative synthetic no material regression"
  provenance:
    method: analytics_query
    provider: amplitude
    reference: amp-synthetic-trading-initiative-v1
    definition_version: trading-initiative-metric-v1
    retrieved_at: "2025-05-30T10:00:00Z"
confidence: low
confounders: [All four interventions overlap in the illustrative evaluation window, Synthetic results cannot establish causal contribution]
data_limitations: [No production observations, No representative sampling, Provider and chain slices are omitted, Numerical results exist only to exercise the workflow]
thesis_change: The aggregate result supports keeping the four barriers separate while measuring one shared trading-continuity outcome.
decision_events:
  - id: decision_01TRADX002
    kind: outcome
    choice: iterate
    decided_by: product-lead
    decided_at: "2025-05-30T12:00:00Z"
    rationale: Preserve the four-barrier architecture and improve bridge settlement, the weakest illustrative slice; the aggregate alone is insufficient to attribute causality.
    based_on_version: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
---

## What changed

The shared result supports one trading-continuity Initiative while preserving four independently reviewable product barriers. Bridge settlement remains the weakest illustrative slice and is the next iteration target.

## Measurement interpretation

Every quantitative result above is synthetic and illustrative. It proves that Product OS can bind an Initiative outcome, retain child PRD outcomes, import a provider result, record limitations, and produce a decision. It does not claim a real post-launch result.

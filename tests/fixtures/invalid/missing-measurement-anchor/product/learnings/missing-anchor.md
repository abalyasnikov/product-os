---
schema_version: 1
id: learning_01JANCHR01
type: learning
title: Learning without an actual measurement anchor
created_at: "2026-01-20T00:00:00Z"
updated_at: "2026-01-20T00:00:00Z"
authors: [fixture-author]
relationships: {}
product_bet_id: prd_01JANCHR02
outcome_contract_ref:
  owner_artifact_id: prd_01JANCHR02
  definition_version: anchor-definition-v1
evaluation_scope: Synthetic evaluation scope.
results:
  baseline: 0.20
  observed: 0.30
  by_slice:
    segment_a: 0.29
    segment_b: 0.31
  provenance:
    method: manual_import
    reference: synthetic-manual-result
    definition_version: fixture-v1
    retrieved_at: "2026-01-20T00:00:00Z"
    imported_by: fixture-author
confidence: low
confounders: []
data_limitations: [The anchor is absent]
thesis_change: No supported change because the measurement window start is unknown.
decision_events:
  - id: decision_01JANCHR01
    kind: outcome
    choice: hold
    decided_by: fixture-author
    decided_at: "2026-01-20T00:00:00Z"
    rationale: Synthetic invalid decision.
    based_on_version: invalid-v1
---

Expected failure: Learning requires an actual measurement anchor.

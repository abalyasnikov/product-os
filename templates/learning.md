---
schema_version: 1
id: learning_<stable-id>
type: learning
title: <measured learning>
relationships:
  initiative: initiative_<id>
product_bet_id: initiative_<id>
outcome_contract_ref:
  owner_artifact_id: initiative_<id>
  definition_version: <definition-version>
measurement_anchor:
  type: <exposure_event|release|manual>
  reference: <verifiable event reference>
  occurred_at: <ISO-8601 timestamp>
evaluation_scope: <rollout or evaluation scope>
results:
  baseline: <baseline>
  observed: <observed result>
  by_slice:
    <slice one>: <result>
    <slice two>: <result>
  provenance:
    method: <analytics_query|manual_import|case_set|review>
    reference: <reproducible reference>
    definition_version: <version>
    retrieved_at: <ISO-8601 timestamp>
confidence: <low|medium|high>
confounders: []
data_limitations: []
thesis_change: <what changed or "No change">
decision_events:
  - id: decision_<stable-id>
    kind: outcome
    choice: <scale|iterate|hold|kill|complete>
    decided_by: <product lead>
    decided_at: <ISO-8601 timestamp>
    rationale: <human rationale>
    based_on_version: <Git commit>
---

## Interpretation

Explain what the observed result changes about the product thesis.

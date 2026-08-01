---
schema_version: 1
id: outcome_01JNVEREF1
type: outcome_contract
title: Executable binding without verification
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-01-01T00:00:00Z"
authors: [fixture-author]
relationships: {}
owner_artifact_ids: [prd_01JNVEREF1]
outcome:
  definition:
    version: synthetic-v1
    method: behavioral_metric
    baseline: 0.20
    target: 0.30
    metric: synthetic completion
    window: 14 days
    slices: [segment_a, segment_b]
    guardrails: [synthetic_failure_rate]
    decision_rule: Scale only if the target passes without guardrail regression.
  binding:
    status: executable
    provider: amplitude
    query_reference: synthetic-query
    definition_version: synthetic-v1
    owner: fixture-author
---

Expected failure: executable binding lacks `verified_by` and `verified_at`.

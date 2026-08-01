---
schema_version: 1
id: outcome_01JSTAED01
type: outcome_contract
title: Binding verified against an older definition
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-02-01T00:00:00Z"
authors: [fixture-author]
relationships:
  prd: prd_01JSTAED01
owner_artifact_ids: [prd_01JSTAED01]
outcome:
  definition:
    version: current-definition-v2
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
    query_reference: synthetic-query-v1
    definition_version: old-definition-v1
    verified_by: fixture-analyst
    verified_at: "2026-01-01T00:00:00Z"
    owner: fixture-analyst
---

Expected failure: executable binding was verified against an older definition version.

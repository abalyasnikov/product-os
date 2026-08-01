---
schema_version: 1
id: outcome_<stable-id>
type: outcome_contract
title: <reusable or extracted outcome contract>
relationships:
  initiative: initiative_<id>
owner_artifact_ids: [initiative_<id>]
outcome:
  definition:
    version: <definition-version>
    method: behavioral_metric
    baseline: <current state>
    target: <target state>
    metric: <observable definition>
    window: <window>
    slices: [<slice>]
    guardrails: [<guardrail>]
    decision_rule: <human decision rule>
  binding:
    status: planned
    owner: <owner>
    due_before: release
---

## Evaluation notes

Use a standalone file only for a large, reusable, or machine-executed contract.

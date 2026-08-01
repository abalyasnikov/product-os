---
schema_version: 1
id: initiative_<stable-id>
type: initiative
title: <shared user outcome>
created_at: <ISO-8601 timestamp>
updated_at: <ISO-8601 timestamp>
authors: [<product lead>]
relationships:
  opportunity: opportunity_<id>
  prds: [prd_<id>, prd_<id>]
opportunity_id: opportunity_<id>
target_outcome: <shared outcome>
product_thesis: <why these barriers should be solved together>
evidence_ids: [opportunity_<id>]
business_impact: <expected business impact>
gtm_hypothesis:
  status: applicable
  audience: <audience>
  promise: <promise>
  discovery_channel: <channel>
  adoption_action: <action>
  launch_measurement: <measurement>
outcome:
  definition:
    version: <definition-version>
    method: behavioral_metric
    baseline: <current value>
    target: <target value>
    metric: <observable metric>
    window: <window>
    slices: [<slice>]
    guardrails: [<guardrail>]
    decision_rule: <human decision rule>
  binding:
    status: planned
    owner: <owner>
    due_before: release
barriers: [<barrier one>, <barrier two>]
child_prd_ids: [prd_<id>, prd_<id>]
dependencies: []
learnings: []
---

## Bet boundary

Describe the shared outcome; leave child requirements in their PRDs.

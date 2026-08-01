---
schema_version: 1
id: prd_<stable-id>
type: prd
title: <coherent problem or barrier>
created_at: <ISO-8601 timestamp>
updated_at: <ISO-8601 timestamp>
authors: [<product lead>]
relationships:
  opportunity: opportunity_<id>
opportunity_id: opportunity_<id>
problem: <problem>
target_users: <target users>
evidence_ids: [signal_<id>]
current_journey: <current observable journey>
desired_journey: <desired observable journey>
target_outcome: <outcome>
requirements: [<requirement>]
non_goals: [<non-goal>]
outcome:
  definition:
    version: <definition-version>
    method: acceptance_journey
    baseline: <current state>
    target: <passing state>
    metric: <observable journey>
    window: <window or review timing>
    slices: [<slice>]
    guardrails: [<guardrail>]
    decision_rule: <human decision rule>
    cases:
      - id: passing-journey
        description: <representative passing journey>
        expected: pass
      - id: known-failing-journey
        description: <known failing journey>
        expected: fail
  binding:
    status: planned
    owner: <owner>
    due_before: release
risks: [<risk>]
dependencies: []
gtm_hypothesis:
  status: applicable
  audience: <audience>
  promise: <promise>
  discovery_channel: <channel>
  adoption_action: <action>
  launch_measurement: <measurement>
implementation_refs: []
delivery_refs: []
---

## Requirements

Clarify user-visible behavior and acceptance scenarios. Engineering owns implementation design.

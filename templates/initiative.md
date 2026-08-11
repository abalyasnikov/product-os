---
schema_version: 1
id: initiative_<stable-id>
type: initiative
title: <shared user outcome>
relationships:
  opportunity: opportunity_<id>
  prds: [prd_<id>, prd_<id>]
---

# <Title>

## Vision

Describe the coherent user experience this multi-PRD Product Bet should create.

## Why this matters

State the product thesis and business impact without repeating child requirements.

## Evidence and confidence

Link the Opportunity, Signals, or Patterns as relative Markdown links with their stable IDs as the
link text, for example `[opportunity_01ABCDEF](../opportunities/short-name.md)`. State contradictions
and coverage gaps explicitly.

## Shared outcome

Define the outcome that requires several distinct barriers to move together.

## Child PRDs

| Barrier | PRD |
|---|---|
| <distinct user barrier> | `product/prds/<file>.md` |

## Sequencing and dependencies

Describe only product-level constraints. Linear owns engineering estimates and delivery sequencing.

## GTM hypothesis

State the shared audience, promise, discovery path, adoption action, and measurement. Child PRDs add only material differences.

## Risks and open questions

- <risk or unresolved decision>

## Outcome Contract

Explain how the shared outcome differs from the child PRD contracts.

```yaml product-os:outcome
definition:
  version: "v1"   # a string, always quoted
  method: behavioral_metric
  baseline: <current value or "to establish">
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
```

---
schema_version: 1
id: prd_<stable-id>
type: prd
title: <coherent problem or barrier>
relationships:
  opportunity: opportunity_<id>
  initiative: initiative_<id> # omit for a standalone Product Bet
  signals: [signal_<id>]
---

# <Title>

## Problem

Who is blocked, what happens today, and why it matters.

## Evidence

Link the source Signals or Patterns and state the confidence and gaps. Do not paste transcripts.

## JTBD

When ..., I want ..., so that ...

## Current and desired journey

Describe the observable change without prescribing implementation.

## Scope

### Requirements

- <user-visible behavior or acceptance scenario>

### Non-goals

- <explicit boundary>

## Outcome Contract

Explain in one sentence what evidence would make the Product Lead call this better.

```yaml product-os:outcome
definition:
  version: <definition-version>
  method: acceptance_journey
  baseline: <current state or "to establish">
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
```

## GTM hypothesis

Audience, promise, discovery channel, adoption action, and how launch adoption will be measured. If GTM is not applicable, say why.

## Risks and dependencies

- <risk, open question, or external dependency>

## Delivery

Link the Linear project after handoff. Link an engineering-owned Implementation Plan only when one exists.

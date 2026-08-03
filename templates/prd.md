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

<Who is blocked, what happens today, and why it matters.>

**Why now / business reality:** <Concrete trigger or named timing gap in 1–3 sentences.>

## Evidence

<Link the source Signals or Patterns and state confidence, contradictions, and coverage gaps. Do not paste transcripts.>

## JTBD

<When ..., I want ..., so that ...>

## Current and desired journey

<Current observable journey → desired observable journey, without prescribing implementation.>

## Scope

### Requirements

- <user-visible behavior or acceptance scenario>

### Non-goals

- <explicit boundary>

## GTM hypothesis

<Audience, promise, discovery channel, adoption action, and launch measurement—or why GTM is not applicable.>

## Risks and dependencies

- <risk or external dependency>

## Open questions

- <question that could change the product decision, or "None">

## Outcome Contract

<One sentence explaining what evidence would make the Product Lead call this better.>

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

## Delivery

<Linear project link after handoff, plus an engineering-owned Implementation Plan only when one exists. Use "Not handed off" while pending.>

<!-- Optional decision context: add a separate References, Competitors and alternatives,
Customer context, or Revenue context section only when it changes the decision or helps a
reviewer verify it. For B2B work, Customer context may include the account/segment, request
source, commercial stage, timing, and permitted ARR or revenue band. Do not duplicate Evidence. -->

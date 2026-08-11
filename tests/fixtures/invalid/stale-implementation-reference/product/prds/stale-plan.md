---
schema_version: 1
id: prd_01JSTAE001
type: prd
title: PRD with stale Implementation Plan reference
created_at: '2026-01-01T00:00:00Z'
updated_at: '2026-02-01T00:00:00Z'
authors:
- fixture-author
relationships: {}
implementation_refs:
- repository: github.com/example/synthetic-app
  path: specs/stale-plan.md
  based_on_prd_id: prd_01JSTAE001
  based_on_prd_version: prd-old-v1
delivery_refs: []
---

# PRD with stale Implementation Plan reference

## Problem

Synthetic problem.

**Why now / business reality:** Recorded on the linked evidence above; this fixture carries no separate timing claim.

## Evidence

Linked evidence: `signal_01JSTAE001`.

## JTBD

**Who:** Synthetic users.

**When** the current journey below applies, **I want** to reach the desired journey below, **so that** synthetic outcome.

## Current and desired journey

**Current:** Current synthetic journey.

**Desired:** Desired synthetic journey.

## Scope

### Requirements

- One synthetic requirement

### Non-goals

- Engineering design

## GTM hypothesis

Not applicable: Synthetic internal fixture.

## Risks and dependencies

- Synthetic risk

## Open questions

None.

## Outcome Contract

Synthetic outcome.

```yaml product-os:outcome
definition:
  version: stale-plan-definition-v1
  method: acceptance_journey
  baseline: failing
  target: passing
  metric: synthetic journey
  window: before release
  slices:
  - segment_a
  guardrails:
  - synthetic_guardrail
  decision_rule: Ship only when the journey passes.
  cases:
  - id: synthetic-pass
    description: Synthetic user completes the journey.
    expected: pass
  - id: synthetic-fail
    description: Synthetic user cannot complete the journey.
    expected: fail
binding:
  status: planned
  owner: fixture-author
  due_before: release
```

## Delivery

Not handed off.

Expected failure: the plan is based on `prd-old-v1`, but the approved PRD version is `prd-current-v2`.

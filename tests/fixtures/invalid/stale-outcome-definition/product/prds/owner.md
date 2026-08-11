---
schema_version: 1
id: prd_01JSTAED01
type: prd
title: Owner PRD for stale binding fixture
created_at: '2026-01-01T00:00:00Z'
updated_at: '2026-01-01T00:00:00Z'
authors:
- fixture-author
relationships:
  opportunity: opportunity_01JSTAED01
  signal: signal_01JSTAED01
implementation_refs: []
delivery_refs: []
---

# Owner PRD for stale binding fixture

## Problem

Synthetic problem.

**Why now / business reality:** Recorded on the linked evidence above; this fixture carries no separate timing claim.

## Evidence

Linked evidence: `signal_01JSTAED01`.

## JTBD

**Who:** Synthetic users.

**When** the current journey below applies, **I want** to reach the desired journey below, **so that** synthetic owner outcome.

## Current and desired journey

**Current:** Synthetic current journey.

**Desired:** Synthetic desired journey.

## Scope

### Requirements

- Synthetic requirement

### Non-goals

- Engineering design

## GTM hypothesis

Not applicable: Synthetic validation fixture.

## Risks and dependencies

- Synthetic risk

## Open questions

None.

## Outcome Contract

Expected failure: the executable binding was verified against an older definition version.

```yaml product-os:outcome
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
```

## Delivery

Not handed off.

Synthetic owner artifact.

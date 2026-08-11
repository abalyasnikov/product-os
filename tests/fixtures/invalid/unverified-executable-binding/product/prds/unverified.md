---
schema_version: 1
id: prd_01JNVEREF1
type: prd
title: Executable binding without verification
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-01-01T00:00:00Z"
authors: [fixture-author]
relationships:
  opportunity: opportunity_01JNVEREF1
---

# Executable binding without verification

## Problem

Synthetic problem for a fixture whose only intended failure is an unverified executable binding.

**Why now / business reality:** Recorded for this fixture; no timing claim is made.

## Evidence

Synthetic fixture evidence; no Signal is linked because this fixture exercises binding verification.

## JTBD

**Who:** Synthetic fixture users.

**When** the current journey below applies, **I want** to reach the desired journey below, **so that** the synthetic completion rate improves.

## Current and desired journey

**Current:** Synthetic current journey.

**Desired:** Synthetic desired journey.

## Scope

### Requirements

- Synthetic requirement

### Non-goals

- Synthetic non-goal

## GTM hypothesis

Not applicable: synthetic fixture with no launch surface.

## Risks and dependencies

- Synthetic risk

## Open questions

None.

## Outcome Contract

Expected failure: the executable binding lacks `verified_by` and `verified_at`.

```yaml product-os:outcome
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
```

## Delivery

Not handed off.

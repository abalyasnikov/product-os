---
schema_version: 1
id: prd_01JABCDE02
type: prd
title: Guided transaction failure recovery
created_at: '2026-05-10T10:00:00Z'
updated_at: '2026-06-05T17:00:00Z'
authors:
- product-lead
relationships:
  opportunity: opportunity_01JABCDE01
  initiative: initiative_01JABCDE01
  signals:
  - signal_01JABCDE02
  - signal_01JABCDE04
implementation_refs: []
delivery_refs:
- provider: linear
  external_id: linear-project-recovery-fixture
  url: https://linear.example.invalid/project/recovery-fixture
  synced_from_version: '5555555555555555555555555555555555555555'
---

# Guided transaction failure recovery

## Problem

New and returning users cannot understand or recover from a rejected transaction without leaving the flow.

**Why now / business reality:** Recorded on the linked evidence above; this fixture carries no separate timing claim.

## Evidence

Linked evidence: `signal_01JABCDE02`, `signal_01JABCDE04`, `pattern_01JABCDE01`.

## JTBD

**Who:** New and returning users whose transaction is rejected before submission or fails after submission.

**When** the current journey below applies, **I want** to reach the desired journey below, **so that** users recover from a recoverable failure without external support.

## Current and desired journey

**Current:** A generic failure state sends users away from the transaction flow without a safe next action.

**Desired:** The failure state names the observable cause category and offers a safe retry, adjustment, or exit action.

## Scope

### Requirements

- Explain the failure category without claiming certainty the system lacks
- Offer a safe next action in the same flow
- Cover new and returning users

### Non-goals

- Eliminating upstream network failures
- Building a support ticket system
- Defining backend retry architecture

## GTM hypothesis

**Audience:** Users encountering a recoverable transaction failure

**Promise:** Understand what happened and take a safe next step

**Discovery channel:** In-flow failure state

**Adoption action:** Retry or adjust and complete the transaction

**Launch measurement:** Same-session completion after recoverable failure

## Risks and dependencies

- Incorrect guidance could cause repeated failures
- Failure categories may be incomplete
- Failure causes can be normalized into user-safe categories

## Open questions

None.

## Outcome Contract

Users recover from a recoverable failure without external support.

```yaml product-os:outcome
definition:
  version: recovery-metric-v2
  method: behavioral_metric
  baseline: 0.18
  target: 0.28
  metric: users completing a transaction within one session after a recoverable failure
  window: 14 days after first eligible exposure
  slices:
  - new_users
  - returning_users
  guardrails:
  - repeat_failure_rate
  decision_rule: Iterate unless recovery reaches 0.28 in aggregate with no slice decline or repeat-failure
    regression.
binding:
  status: manual
  provider: manual-import
  owner: analytics-lead
  measurement_anchor:
    type: exposure_event
    reference: exposure-fixture-rollout-01
    occurred_at: '2026-07-01T09:00:00Z'
```

## Delivery

- linear `linear-project-recovery-fixture` — https://linear.example.invalid/project/recovery-fixture

## Material update

The approved target-user scope now includes returning users because `signal_01JABCDE04` challenged the original assumption.

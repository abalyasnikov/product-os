---
schema_version: 1
id: prd_01TRADX004
type: prd
title: Non-blocking Transaction Status
created_at: '2025-02-13T10:00:00Z'
updated_at: '2025-02-23T15:00:00Z'
authors:
- product-manager
relationships:
  opportunity: opportunity_01TRADX001
  initiative: initiative_01TRADX001
  signals:
  - signal_01TRADX004
  pattern: pattern_01TRADX002
implementation_refs: []
delivery_refs:
- provider: linear
  external_id: TRA-204
  url: https://linear.example.invalid/issue/TRA-204
  synced_from_version: '6666666666666666666666666666666666666666'
---

# Non-blocking Transaction Status

## Problem

A pending transaction occupies a blocking surface and does not make clear whether processing continues after the user leaves.

**Why now / business reality:** Recorded on the linked evidence above; this fixture carries no separate timing claim.

## Evidence

Linked evidence: `signal_01TRADX004`, `pattern_01TRADX002`.

## JTBD

**Who:** Mobile and desktop users with a submitted transaction that has not reached a terminal state.

**When** the current journey below applies, **I want** to reach the desired journey below, **so that** users leave the progress surface without losing access to transaction state or interrupting processing.

## Current and desired journey

**Current:** Users wait on a modal progress screen or close it without a persistent way to return to status.

**Desired:** Submission becomes a persistent activity item; users can continue using the product and reopen accurate status at any time.

## Scope

### Requirements

- Persist submitted activity before dismissing progress
- Explain that processing continues
- Restore status after restart
- Surface terminal failure and safe next action

### Non-goals

- Accelerating chain confirmation
- Replacing chain explorers
- Defining bridge sub-steps

## GTM hypothesis

**Audience:** Users waiting for transaction confirmation

**Promise:** Keep using the wallet while your transaction continues

**Discovery channel:** Transaction progress surface and activity feed

**Adoption action:** Leave progress and later reopen the same activity item

**Launch measurement:** Synthetic restored-state service level and duplicate-submission guardrail

## Risks and dependencies

- Stale local state could imply false completion
- Users could accidentally resubmit while an item is pending
- Submitted transaction identity persists before navigation

## Open questions

None.

## Outcome Contract

Users leave the progress surface without losing access to transaction state or interrupting processing.

```yaml product-os:outcome
definition:
  version: nonblocking-status-slo-v1
  method: service_level
  baseline: illustrative synthetic 76% of submitted items restore after restart
  target: illustrative synthetic 99.5% of submitted items restore after restart
  metric: submitted activity items recoverable with correct latest state
  window: Rolling synthetic seven-day period
  slices:
  - mobile
  - desktop
  - app_restart
  - background_resume
  guardrails:
  - duplicate_submission_rate
  - stale_terminal_state
  decision_rule: Scale when the service threshold passes in every required platform slice and guardrails
    remain within threshold.
  service_threshold: illustrative synthetic 99.5%
  service_period: Rolling synthetic seven-day period
binding:
  status: executable
  provider: amplitude
  query_reference: amp-synthetic-nonblocking-status-v1
  definition_version: nonblocking-status-slo-v1
  verified_by: analytics-lead
  verified_at: '2025-02-22T14:00:00Z'
  owner: analytics-lead
```

## Delivery

- linear `TRA-204` — https://linear.example.invalid/issue/TRA-204

## Product boundary

This PRD owns navigation continuity and persistent status. Bridge-specific stages belong to Bridge Progress Tracking.

---
schema_version: 1
id: prd_01TRADX005
type: prd
title: Bridge Progress Tracking
created_at: '2025-02-14T09:00:00Z'
updated_at: '2025-02-24T15:00:00Z'
authors:
- product-manager
relationships:
  opportunity: opportunity_01TRADX001
  initiative: initiative_01TRADX001
  signals:
  - signal_01TRADX006
  pattern: pattern_01TRADX002
implementation_refs: []
delivery_refs:
- provider: jira
  external_id: TRD-105
  url: https://jira.example.invalid/browse/TRD-105
  synced_from_version: '7777777777777777777777777777777777777777'
---

# Bridge Progress Tracking

## Problem

A bridge can confirm on the source chain while destination delivery remains pending, but the product collapses the journey into an ambiguous single status.

**Why now / business reality:** Recorded on the linked evidence above; this fixture carries no separate timing claim.

## Evidence

Linked evidence: `signal_01TRADX006`, `pattern_01TRADX002`.

## JTBD

**Who:** Users whose supported send or swap includes one or more bridge settlement stages.

**When** the current journey below applies, **I want** to reach the desired journey below, **so that** bridge users can identify the current settlement stage and distinguish waiting from required action.

## Current and desired journey

**Current:** Users see a transaction hash or generic pending state and cannot tell which stage completed, what remains, or whether action is required.

**Desired:** Activity shows source submission, provider processing, and destination delivery as truthful stages with safe escalation when progress stalls.

## Scope

### Requirements

- Represent source and destination stages separately
- Link available provider and chain references
- Never infer destination completion from source confirmation
- Explain stalled and failed states without inventing an ETA

### Non-goals

- Guaranteeing provider settlement time
- Supporting every bridge provider at launch
- Turning Send into a generic bridge router

## GTM hypothesis

**Audience:** Users waiting for cross-chain settlement

**Promise:** See what has completed, what remains, and whether you need to act

**Discovery channel:** Activity feed and cross-chain transaction detail

**Adoption action:** Reopen a bridge activity item and correctly identify its stage

**Launch measurement:** Synthetic truthfulness and actionability rubric by provider state

## Risks and dependencies

- Provider state mappings may drift
- Stalled states may encourage unsafe retry
- Provider exposes stage-level status or a safe unknown state

## Open questions

None.

## Outcome Contract

Bridge users can identify the current settlement stage and distinguish waiting from required action.

```yaml product-os:outcome
definition:
  version: bridge-progress-rubric-v1
  method: qualitative_rubric
  baseline: illustrative synthetic reviewers cannot reliably identify the current stage
  target: illustrative synthetic all critical examples meet the rubric
  metric: bridge-state examples meeting truthfulness and actionability rubric
  window: Before release and after every provider-state mapping change
  slices:
  - source_pending
  - provider_processing
  - destination_pending
  - complete
  - stalled
  - failed
  guardrails:
  - false_completion
  - invented_eta
  - unsafe_retry
  decision_rule: Ship a provider mapping only when every critical example meets all rubric dimensions.
  rubric_dimensions:
  - state_truthfulness
  - remaining_work_clarity
  - next_action_safety
  rubric_examples:
  - Source confirmed while destination is pending
  - Provider processing exceeds its estimate
  - Destination delivery fails after source success
  reviewers:
  - product-manager
  - bridge-domain-reviewer
binding:
  status: executable
  provider: manual-eval
  case_set_reference: case-set-synthetic-bridge-progress-v1
  definition_version: bridge-progress-rubric-v1
  verified_by: product-ops
  verified_at: '2025-02-23T14:00:00Z'
  owner: product-ops
```

## Delivery

- jira `TRD-105` — https://jira.example.invalid/browse/TRD-105

## Separation from Send

This PRD preserves truth after an accepted route enters a multi-stage bridge lifecycle. Route selection remains owned by Cross-chain Swap.

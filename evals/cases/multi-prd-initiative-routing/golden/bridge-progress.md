---
schema_version: 1
id: prd_01EVALROUTE002
type: prd
title: Bridge Progress Tracking
relationships:
  opportunity: opportunity_01EVALROUTE001
  initiative: initiative_01EVALROUTE001
  signals: [signal_01EVALROUTE002]
---

# Bridge Progress Tracking

## Problem

A bridge-dependent trade can appear complete after source-chain confirmation even though destination settlement remains pending. Users cannot reliably tell the current stage or whether action is required.

**Why now / business reality:** Cross-chain routes are already part of the intended trading experience, while a single pending state cannot truthfully represent their settlement lifecycle.

## Evidence

`signal_01EVALROUTE002` records a directional journey where source confirmation was mistaken for completion. It does not provide a support-volume estimate or measured settlement-confidence baseline.

## JTBD

When my cross-chain trade is still settling, I want to know the truthful current stage and whether I need to act, so that I do not mistake source confirmation for completion.

## Current and desired journey

Today the product can collapse a multi-stage route into an ambiguous pending or completed state. The desired journey distinguishes source submission, bridge settlement, destination completion, stall, and failure using only states supported by available provider facts.

## Scope

### Requirements

- Progress distinguishes source confirmation from destination completion.
- The status remains recoverable after the user leaves the original flow.
- Stalled and failed states explain whether user action is available.

### Non-goals

- Guaranteeing bridge settlement time.
- Inventing an estimate when the provider has no reliable one.
- Selecting or composing the route before authorization.

## GTM hypothesis

The audience is users of bridge-dependent trades. The promise is progress that remains truthful until funds arrive. Discovery occurs after route authorization and in transaction activity; adoption is successful interpretation of the current state. Measurement follows the lifecycle interpretation contract.

## Risks and dependencies

- Providers may expose different or incomplete lifecycle states.
- A simplified vocabulary may conceal a provider-specific recovery condition.

## Open questions

- What evidence is sufficient to label destination settlement complete for each supported provider?

## Outcome Contract

Better means users identify the truthful current settlement stage and appropriate next action across supported lifecycle cases.

```yaml product-os:outcome
definition:
  version: bridge-stage-truth-v1
  method: case_based_eval
  baseline: to establish
  target: All critical lifecycle interpretation cases pass
  metric: bridge lifecycle stages and next actions correctly interpreted
  window: before release and the first post-release review
  slices: [source_submitted, bridging, destination_settled, stalled, failed]
  guardrails: [false_completion, invented_estimate, unsafe_retry]
  decision_rule: Ship only when every critical lifecycle case is truthful and no safety guardrail fails.
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## Delivery

Linear owns estimates and sequencing. Event reconciliation, provider mapping, and persistence belong in an engineering-owned Implementation Plan.

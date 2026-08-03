---
schema_version: 1
id: prd_01EVALROUTE001
type: prd
title: Cross-chain Swap
relationships:
  opportunity: opportunity_01EVALROUTE001
  initiative: initiative_01EVALROUTE001
  signals: [signal_01EVALROUTE001]
---

# Cross-chain Swap

## Problem

A trader with a destination-asset intent must reason about bridge and swap as separate product operations. The user cannot compare the composed result as one trade before authorization.

**Why now / business reality:** The current trading entry point already exposes cross-chain demand, but route composition is still delegated to the user's mental model.

## Evidence

`signal_01EVALROUTE001` records a directional journey where the user had to assemble bridge and swap. It supports the barrier but does not establish prevalence or a behavioral baseline.

## JTBD

When I want an asset on another supported chain, I want to review one composed trade, so that I can decide using the total route rather than manually coordinating separate actions.

## Current and desired journey

Today the user discovers the chain mismatch, leaves the trade, bridges, and returns to swap. The desired journey presents one supported route with its material assets, networks, cost, and expected result before authorization.

## Scope

### Requirements

- The user can select a supported destination asset without first completing a separate bridge journey.
- The product presents material route composition before authorization.
- A material route change requires renewed review.

### Non-goals

- Building a bridge protocol.
- Supporting every chain pair.
- Owning destination-settlement status after route acceptance.

## GTM hypothesis

The audience is multi-chain traders. The promise is one reviewed trade instead of a manually assembled bridge and swap. Discovery remains in the existing trading entry point; adoption is authorization of a supported composed route. Measurement follows the route-comprehension contract.

## Risks and dependencies

- Provider quotes may expire or change materially.
- Unsupported routes must fail clearly rather than degrade into an unsafe partial journey.

## Open questions

- Which route changes are material enough to require renewed review?

## Outcome Contract

Better means users can correctly understand and authorize a supported composed route without manually planning bridge and swap.

```yaml product-os:outcome
definition:
  version: cross-chain-route-comprehension-v1
  method: case_based_eval
  baseline: to establish
  target: All critical route-comprehension cases pass
  metric: supported composed routes correctly understood before authorization
  window: before release
  slices: [direct_swap, bridge_then_swap, route_change, unavailable_route]
  guardrails: [hidden_cost, wrong_destination_asset, unreviewed_route_change]
  decision_rule: Ship only the route slices whose critical comprehension and safety cases pass.
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## Delivery

Linear owns estimates and sequencing. Provider selection, quote orchestration, and transaction construction belong in an engineering-owned Implementation Plan.

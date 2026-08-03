---
schema_version: 1
id: initiative_01EVALROUTE001
type: initiative
title: Continuous cross-chain trading
relationships:
  opportunity: opportunity_01EVALROUTE001
  signals: [signal_01EVALROUTE001, signal_01EVALROUTE002]
  prds: [prd_01EVALROUTE001, prd_01EVALROUTE002]
---

# Continuous cross-chain trading

## Vision

A supported cross-chain trade feels like one understandable product journey from asset intent through destination settlement, without hiding materially different execution states.

## Why this matters

Route composition and settlement truth block the same user outcome, but they require different product contracts. The Initiative owns continuity across the journey; each child PRD owns one barrier and its own observable result.

## Evidence and confidence

`signal_01EVALROUTE001` shows disconnected bridge and swap reasoning. `signal_01EVALROUTE002` shows ambiguity after source confirmation. Both sources are directional. They support the barrier split but do not establish frequency, retention impact, or a measured completion baseline.

## Shared outcome

Eligible users can start a supported cross-chain trade, understand the route before authorizing it, and follow truthful progress until destination settlement.

## Child PRDs

| Barrier | PRD |
|---|---|
| Route composition forces users to assemble bridge and swap | `prd_01EVALROUTE001` — Cross-chain Swap |
| Settlement progress becomes ambiguous after source confirmation | `prd_01EVALROUTE002` — Bridge Progress Tracking |

## Sequencing and dependencies

The route contract must define the accepted journey before shared progress can represent it. Engineering estimates and delivery sequence remain in Linear. The Initiative does not duplicate either child's requirements.

## Outcome Contract

The shared contract measures continuity across both barriers; child contracts separately measure route comprehension and settlement-state truth.

```yaml product-os:outcome
definition:
  version: continuous-cross-chain-trading-v1
  method: acceptance_journey
  baseline: to establish
  target: All critical end-to-end journey cases pass
  metric: supported cross-chain journeys understood and followed through destination settlement
  window: before coordinated release and the first outcome review
  slices: [route_selection, source_confirmation, destination_settlement]
  guardrails: [unsupported_route, false_completion, hidden_route_change]
  decision_rule: Continue the Initiative only if both child contracts pass and the shared journey adds no cross-boundary failure.
binding:
  status: planned
  owner: product-lead
  due_before: coordinated-release
```

## GTM hypothesis

The audience is active multi-chain traders. The promise is one understandable cross-chain trade with progress that remains truthful. Discovery begins in the existing trading entry point; adoption is completion of a supported journey. Launch measurement uses the shared contract and retains child slices.

## Risks and open questions

- Provider differences may prevent one consistent progress vocabulary.
- Aggregate completion could hide a weak child barrier.
- Open question: which route classes are coherent enough to include in the shared launch?

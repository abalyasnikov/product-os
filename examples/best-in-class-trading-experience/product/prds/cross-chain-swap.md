---
schema_version: 1
id: prd_01TRADX001
type: prd
title: Cross-chain Swap
relationships:
  initiative: initiative_01TRADX001
---

# Cross-chain Swap

## Problem

Users cannot express a simple trade intent when the asset they own and the asset they want are on different networks. They must discover a bridge, move funds, wait, return to Swap, and reconstruct the original trade.

This is product friction, not an inherently separate user job. The user wants the destination asset; manually coordinating bridge and swap is incidental work.

**Why now / business reality:** Cross-chain swap had become a visible market baseline while the observed Zerion journey still required manual bridging; the frequency and completion impact had not yet been measured. This barrier came from the competitive position recorded in [strategy context](../../context/strategy.md) rather than from user requests — nobody asked for it, and staying behind the baseline would have cost the prosumer positioning anyway.

## Evidence

In a first-use walkthrough, a user wanted to buy HYPE on HyperEVM with funds on Ethereum. HyperEVM did not appear in the network list because the user had no balance there, mobile receive-token search was implicitly filtered by the current network, and switching networks lost the original context. The only viable path was a manual bridge.

Phantom already exposed cross-chain swap as one product flow. This indicated a changing market baseline, but competitor behavior alone was not treated as proof of user demand.

Evidence quality was directional: the journey failure was concrete, while its population frequency and completion impact still required measurement.

| Source | Observation | Date/window | Confidence |
|---|---|---|---|
| First-use walkthrough; private recording withheld | The user could not preserve one intent across Ethereum and HyperEVM and required a manual bridge | February 5, 2026 | High for this journey; low for frequency |
| Product-flow inspection | Network filtering and context loss were reproducible in the captured mobile flow | Q1 2026 snapshot | High for current behavior |
| Public competitor review | Phantom exposed cross-chain swap as one flow | Q1 2026 snapshot | Directional market evidence only |

## JTBD

> When the asset I want is on another supported chain, I want to trade the assets I already own for it in one journey, so that I do not have to understand and coordinate bridging first.

## Current and desired journey

**Current:** choose a network, fail to find the asset, manually bridge, wait without a unified status, return to Swap, and search again.

**Desired:** choose the pay and receive assets across supported networks, review the material route and timing, confirm one intent, and follow both execution stages without reconstructing the trade.

## Scope

### Requirements

- Show an **All networks** view plus individual network tabs in pay and receive asset selection.
- Let the routing layer choose swap or bridge-plus-swap; do not require the user to choose the mechanism first.
- Show the complete route, material fees, and estimated delivery time before confirmation.
- Preserve stage-level transaction references after submission.
- Require renewed consent when an expired or changed route materially changes the accepted trade.
- Provide one consistent product flow across iOS, Android, and browser extension.
- Limit V1 to supported EVM-to-EVM routes.

### Non-goals

- Building a proprietary bridge.
- Guaranteeing settlement time.
- Hiding provider, route, or chain risk.
- Cross-ecosystem routing such as Solana-to-EVM before the required account model exists.

## GTM hypothesis

The initial audience is existing users who already hold and trade assets on multiple EVM chains. The promise is one cross-chain trade without manually coordinating a bridge. Discovery belongs in the current Swap asset and network selectors; the adoption action is completing an eligible cross-chain swap.

## Risks and dependencies

- The route provider must expose both execution stages, estimates, and material changes.
- A unified presentation can accidentally hide multi-stage failure.
- Quote expiry can invalidate the accepted trade between review and signature.
- Cross-ecosystem expansion depends on the account model and is explicitly separate.

## Open questions

- Which route changes are material enough to require renewed consent?
- How should the product explain partial completion when the bridge succeeds but the destination trade fails?
- Which baseline event defines a genuine eligible cross-chain intent rather than casual asset browsing?

## Outcome Contract

The release must first pass the critical journeys honestly; post-release behavior can then test whether one intent improves completion.

```yaml product-os:outcome
definition:
  version: cross-chain-swap-v1
  method: acceptance_journey
  baseline: manual bridge and swap are separate; behavioral completion baseline to establish
  target: every critical supported journey passes before release, followed by improved eligible completion versus baseline
  metric: critical cross-chain journeys passing and eligible cross-chain swap completion
  window: before release and 14 days after measurable exposure
  slices:
    - supported_route
    - route_change
    - route_unavailable
    - destination_delay
  guardrails:
    - wrong_asset_received
    - unpriced_material_route_change
    - continuation_without_valid_consent
  decision_rule: Ship only when all safety-critical journeys pass; scale only if eligible completion improves without guardrail regression.
  cases:
    - id: floor-supported-evm-route
      description: A supported EVM route completes with both stages and transaction references visible.
      expected: pass
      slice: supported_route
    - id: ceiling-route-invalidates
      description: A material route change continues without renewed user consent.
      expected: fail
      slice: route_change
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## Delivery

The underlying unified API already supported swap routing and provided a foundation for additional chain parameters. Client and design work was tracked in Linear. Route algorithms and the implementation state machine belong in an engineering-owned Implementation Plan, not in this PRD.

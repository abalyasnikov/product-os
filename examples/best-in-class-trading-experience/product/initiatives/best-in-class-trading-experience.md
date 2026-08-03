---
schema_version: 1
id: initiative_01TRADX001
type: initiative
title: Best-in-class trading experience
relationships:
  prds:
    - prd_01TRADX001
    - prd_01TRADX002
    - prd_01TRADX003
    - prd_01TRADX004
    - prd_01TRADX005
---

# Best-in-class trading experience

## Vision

Trading should feel like one continuous, trustworthy journey. A user should be able to express an intent, understand material trade-offs, confirm it once, keep using the wallet while it executes, and know what is happening until settlement.

## Why this matters

The core trading flow was losing coherence at five different moments: asset selection across chains, execution reliability, final confirmation, pending transaction state, and cross-chain settlement. Each problem could be shipped independently, but solving only one would still leave the overall journey fragmented.

The product thesis is that removing these barriers together creates a meaningfully better experience for active multi-chain users. The Initiative owns that shared outcome; each child PRD owns one barrier and its own narrower Outcome Contract.

## Evidence and confidence

The Initiative was grounded in:

- a first-use walkthrough in which a user tried to buy an asset on another EVM network and could not discover a direct route;
- support reports and telemetry indicating slippage-related failures in volatile or thin-liquidity conditions, without a verified population baseline;
- direct inspection of existing native transaction flows, including repeated confirmation and blocking pending/success screens;
- observed bridge-status gaps and unresolved recovery behavior;
- public competitor patterns from Phantom, Rainbow, and Rabby.

Confidence was uneven. The journey problems were directly observable, but their frequency and aggregate business impact were not established by representative research. No post-release result was available in the source documents, so this example does not invent one.

## Shared outcome

Eligible users complete supported trading journeys with fewer avoidable interruptions and can understand transaction state until settlement.

For measurement, an **eligible journey** begins when a supported user selects a valid trading intent and receives at least one executable route. An **avoidable product interruption** is one of five product-caused barriers: cross-chain discovery cannot preserve the intent, the product selects an inadequate slippage tolerance for an eligible route, a clean native flow repeats confirmation, post-submission UI blocks the next independent action, or bridge state cannot communicate the current stage. Provider rejection, insufficient balance, and user cancellation after truthful review are reported separately rather than counted as product interruptions.

The product principles below are not restated here for convenience; they are quoted from [strategy context](../../context/strategy.md), which is where their order is set. That order is what makes them usable in a review: the principles, in order, are:

1. **Reliable:** never trade safety or truthful state for fewer screens.
2. **Fast:** remove steps that add no new information and never block the rest of the product unnecessarily.
3. **Power without noise:** expose route and provider detail when it changes a decision, not as permanent ceremony.

## Child PRDs

| Barrier | PRD | Boundary |
|---|---|---|
| Cross-chain intent is split into disconnected bridge and swap operations | [Cross-chain Swap](../prds/cross-chain-swap.md) | One trade intent and route across supported EVM chains |
| Static slippage settings cause avoidable failures or expose users to poor execution | [Auto-slippage for Native Swaps and Bridges](../prds/auto-slippage.md) | Adapt tolerance while protecting execution quality and explicit consent |
| Native transactions repeat information the user already accepted | [Skip Signing Screen for Native Transactions](../prds/skip-signing-screen-for-native-transactions.md) | Skip only when simulation and security checks are clean |
| Pending and success pages block the rest of the wallet | [Transaction Toasters](../prds/transaction-toasters.md) | Non-blocking status for all supported transaction types |
| Cross-chain settlement is an ambiguous wait | [Bridge Progress Tracking](../prds/bridge-progress-tracking.md) | Truthful stages, estimates, failure, and recovery states |

## Sequencing and dependencies

Cross-chain Swap can define the unified intent before every post-confirmation state is polished, but its rollout depends on truthful bridge status. Auto-slippage must share route, quote-expiry, and renewed-consent rules with that flow. Transaction Toasters and Bridge Progress Tracking should share one transaction-state model rather than inventing separate status semantics. Skipping the signing screen must remain gated by simulation and security coverage.

Engineering estimates and delivery sequencing belong in Linear. This document records only product dependencies and the reason the five PRDs belong to one bet.

## GTM hypothesis

The first audience is existing multi-chain wallet users who already trade or bridge. The promise is not “more routes”; it is one reliable journey that preserves control and progress across chains. Discovery should happen inside the existing Swap entry point and transaction status surfaces. Adoption is an eligible user completing the journey and continuing to use the wallet while settlement proceeds.

A separate GTM workflow should own launch execution. The Initiative keeps this hypothesis so product design and launch positioning do not diverge.

## Risks and open questions

- Removing visible steps can reduce comprehension if warning and route-change rules are incomplete.
- Improving transaction success can conceal worse execution unless price-quality guardrails are evaluated alongside failure rate.
- Provider estimates may be unavailable or too unreliable to display as precise ETAs.
- One aggregate metric may hide a severe failure in a smaller chain or route slice.
- The baseline and exposure definition must be established before an outcome claim is possible.

## Outcome Contract

The Initiative succeeds only if the shared trading journey improves. Passing every child PRD contract is necessary evidence, but is not by itself proof of the aggregate outcome.

```yaml product-os:outcome
definition:
  version: best-in-class-trading-v1
  method: behavioral_metric
  baseline: to establish before rollout
  target: improve eligible journey completion versus baseline without guardrail regression
  metric: eligible trading journeys completed without an avoidable product interruption
  window: 28 days after all included journeys have measurable exposure
  slices:
    - cross_chain_swap
    - execution_reliability
    - native_transaction_confirmation
    - transaction_status
    - bridge_settlement
  guardrails:
    - transaction_failure_rate
    - median_execution_delta
    - high_effective_slippage_share
    - material_warning_coverage
    - false_completion_or_wrong_asset_incidents
    - support_contact_rate
  decision_rule: Scale only when the aggregate improves, no required slice materially regresses, and every safety guardrail remains acceptable; otherwise iterate on the failing slice.
binding:
  status: planned
  owner: product-lead
  due_before: release
```

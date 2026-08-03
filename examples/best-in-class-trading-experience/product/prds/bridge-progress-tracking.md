---
schema_version: 1
id: prd_01TRADX005
type: prd
title: Bridge Progress Tracking
relationships:
  initiative: initiative_01TRADX001
---

# Bridge Progress Tracking

## Problem

After confirming a bridge-dependent transaction, users could not tell what was happening, when funds might arrive, or whether intervention was required. Cross-chain settlement ranges from seconds to minutes, yet the product exposed an undifferentiated wait.

Source-chain confirmation is not the same as destination completion. Treating it as success would create false confidence precisely when the user needs the wallet to be reliable.

**Why now / business reality:** Cross-chain Swap depended on bridge routing, so launching it without truthful settlement progress would leave the core journey incomplete; support and retention impact had not yet been baselined.

## Evidence

Bridge delivery times varied substantially by route and chain. Users often had to open block explorers or provider interfaces to determine whether a transaction was still progressing. Cross-chain Swap depended on bridging under the hood, so shipping it without truthful progress left the core journey incomplete.

The source work proposed reducing “where are my funds?” support tickets and improving estimate accuracy. Neither baseline was available in the document and both remain proposed measures.

| Source | Observation | Date/window | Confidence |
|---|---|---|---|
| Product-flow inspection | Bridge-dependent transactions exposed an undifferentiated pending state | March 2, 2026 source snapshot | High for current behavior |
| Provider and chain behavior | Settlement time varied materially by route and chain | Historical product context | High for variability; provider-level distribution unverified |
| Cross-chain Swap dependency review | The unified trade journey required truthful post-confirmation bridge state | Q1 2026 planning | High for dependency; outcome impact unmeasured |

## JTBD

> When a cross-chain transaction takes time to settle, I want to know the expected wait, current stage, and next action, so that I can trust it is progressing and respond correctly if it stalls.

## Current and desired journey

**Current:** confirm, see a generic pending state, leave the product to investigate, and infer completion from balances or external tools.

**Desired:** review an honest estimate before confirmation, follow submitted → bridging → completing → done after submission, and receive a clear stalled or failed state with a safe next action.

## Scope

### Requirements

- Show an estimated delivery range before confirmation when the source is reliable enough; otherwise say that no reliable estimate is available.
- Track explicit stages: submitted, bridging, completing, and done.
- Keep progress accessible from the durable transaction activity entry.
- Expose provider and route information when it helps the user verify or recover the transaction.
- Distinguish delayed, stalled, failed, and completed states.
- Provide safe next-step guidance without implying a retry is harmless.
- Reuse the same progress model across Cross-chain Swap and future bridge-dependent flows.
- Never mark destination completion from source-chain confirmation alone.

### Non-goals

- Guaranteeing a provider ETA.
- Inventing precision when the provider has insufficient data.
- Automatically retrying a stalled bridge without understanding execution state.
- Replacing the bridge provider's recovery or support process.

## GTM hypothesis

This is a trust layer for users of Cross-chain Swap and other bridge-dependent flows. The promise is clear, truthful progress rather than instant settlement. Discovery occurs in confirmation and transaction activity; adoption is users returning to the in-product status instead of requiring external investigation.

## Risks and dependencies

- Providers may expose inconsistent status semantics or no reliable ETA.
- Route aggregation can make provider-specific recovery difficult to explain.
- Push or background updates may differ by platform.
- Transaction Toasters and activity must share the same durable source of truth.

## Open questions

- Which providers expose a trustworthy delivery estimate and stage model?
- What recovery action is safe for a genuinely stalled transaction?
- When should completion trigger an out-of-app notification?

## Outcome Contract

The user must be able to understand the stage and correct next action. Estimate accuracy is valuable, but truthful uncertainty is preferable to a precise fiction.

The original draft proposed three measures: actual delivery within `2×` the estimate for `90%` of transactions, `50%` fewer bridge-related “where are my funds?” tickets, and `80%` of users remaining in-app during the wait. All three were unvalidated proposals. Estimate accuracy and support demand can become success measures after baselines exist; remaining in-app is diagnostic because leaving the app is not itself a product failure.

```yaml product-os:outcome
definition:
  version: bridge-progress-v1
  method: acceptance_journey
  baseline: generic pending state with no verified stage comprehension baseline
  target: every critical progress, stall, failure, and completion journey communicates the truthful state and next action
  metric: critical bridge-status journeys passing product and comprehension review
  window: before release and 28 days after measurable exposure
  slices:
    - submitted
    - bridging
    - completing
    - stalled
    - failed
    - done
  guardrails:
    - false_destination_completion
    - invented_eta
    - unsafe_retry_guidance
  decision_rule: Ship only if every critical state is truthful and actionable; iterate if estimate accuracy or support demand misses target without violating safety.
  cases:
    - id: floor-stage-progression
      description: A supported bridge advances through observable stages and finishes with destination evidence.
      expected: pass
      slice: done
    - id: ceiling-false-completion
      description: The product reports done after source confirmation while destination settlement is incomplete.
      expected: fail
      slice: completing
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## Delivery

Delivery was tracked in Linear as a reusable capability for bridge-dependent flows. Provider adapters, polling or event strategy, and state-machine ownership belong in an engineering-owned Implementation Plan.

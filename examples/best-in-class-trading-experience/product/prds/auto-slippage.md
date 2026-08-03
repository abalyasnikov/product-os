---
schema_version: 1
id: prd_01TRADX002
type: prd
title: Auto-slippage for Native Swaps and Bridges
relationships:
  initiative: initiative_01TRADX001
---

# Auto-slippage for Native Swaps and Bridges

## Problem

Static slippage settings cannot account for different route, liquidity, and volatility conditions. A tolerance that is too narrow causes an otherwise executable swap or bridge to fail after the user has confirmed it. A tolerance that is too wide may improve the success rate by accepting a materially worse price.

The product problem is therefore not simply to reduce failures. It is to improve execution reliability without degrading execution quality or weakening the user's consent.

**Why now / business reality:** Support reports identified failed transactions as a recurring trust problem, and telemetry indicated concentration around volatile or thin-liquidity conditions. Per [strategy context](../../context/strategy.md), trading is the largest revenue line and **Reliable** is the highest-order product principle — so a failed swap is a revenue loss and a principle violation at the same time, which is what moved this above other reliability work. Figures in this example are approximate and reconstructed from the original private analysis.

## Evidence

Support specialists consolidated recurring reports in Linear, with raw Intercom conversations available when the aggregate signal needed clarification. Investigating the pattern took two sources rather than one: Mixpanel for what users did in the product, and Metabase for onchain settlement, because a transaction that the wallet accepts can still fail after it reaches the node. Product analytics alone cannot see that outcome, which is exactly the gap users were reporting.

The order of investigation mattered more than any single source. As an aggregate the failure rate read as noise, and the defensible conclusion would have been that no product problem existed. It became visible only after the funnel was decomposed by stage and failures segmented by cause, network, and asset market cap.

| Source | Observation | Date/window | Confidence |
|---|---|---|---|
| Consolidated support reports; private links withheld | Users reported swaps or bridges failing after they had accepted a quote | Q1 2026 snapshot | High for problem existence; unknown frequency |
| Aggregate product telemetry | Failure rate indistinguishable from noise at this scale | Q1 2026 snapshot | High — and actively misleading as a headline number |
| Segmented telemetry by market-cap band | Roughly 15% of initiated trades failing in the low-market-cap segment | Q1 2026 snapshot | High for the direction and order of magnitude; exact segment boundary not recovered |
| PR review history | Review added execution-quality guardrails and iterated on fallback and calculation logic | Q1 2026 snapshot | High for decision history |

## JTBD

> When I swap or bridge in changing market conditions, I want the product to choose a safe tolerance automatically, so that the transaction is more likely to execute without me accepting an unexpectedly bad price.

## Current and desired journey

**Current:** accept a quote with a static tolerance, submit the transaction, encounter an avoidable slippage-related failure, and retry manually with a wider value or abandon the flow.

**Desired:** receive an appropriate default for the current route, see a warning when the tolerance becomes material, renew consent when the accepted trade changes, and either execute within the guardrails or fail honestly.

## Scope

### Requirements

- Make Auto the default for eligible native swaps and bridges, with no onboarding flow. A default that needs explaining is not a default.
- Adapt the tolerance to current execution conditions and route characteristics rather than applying one preset everywhere.
- Cap Auto at 10% and manual override at 25%. Beyond the Auto cap the product does not quietly go further; the user must switch to manual and accept that trade explicitly.
- Treat any token the product cannot confidently recognize as its riskiest case.
- Reset a custom tolerance to Auto when the user leaves the swap form, so nobody stays on a wide value they set once and forgot.
- Surface the tolerance once it is material for the asset being traded, and warn distinctly where a manual value is wide enough to make the trade worth sandwiching. Materiality is relative: a tolerance that is unremarkable on a volatile token is alarming on a stablecoin pair.
- Require renewed consent when a quote or route changes beyond the trade the user accepted.
- Fall back conservatively when inputs are missing, and log every fallback.
- Measure Auto and manual separately, including failure reason, quoted output, and executed output.

The caps are absolute limits on what the product will ever do on someone's behalf, so they belong here. The visibility and warning points do not: what counts as material depends on the asset class, and calibrating it is engineering's work rather than a promise the product makes.

### Non-goals

- Guaranteeing that every transaction executes.
- Treating provider, balance, signing, or unrelated onchain failures as slippage failures.
- Hiding material price impact or route risk from the user.
- Fixing the final classification rules, coefficients, or calculation formula in the PRD.

## GTM hypothesis

This is a default reliability improvement, not a standalone product launch. Discovery should happen in the existing swap and bridge flow through the Auto setting and contextual warnings. Adoption is an eligible transaction using Auto; success is measured by the Outcome Contract rather than feature awareness.

## Competitors and alternatives

Jupiter's dynamic slippage set the bar for how an Auto mode should feel: the product picks a tolerance and the user does not think about it. It did not set the bar for the guardrails, which is the part this PRD adds rather than copies.

The rejected alternative was simply raising the static default. It would have improved the failure rate immediately by shifting the cost onto users as worse prices — the exact outcome the Outcome Contract now forbids.

## Risks and dependencies

- A wider tolerance can conceal poor routing or expose users to worse prices.
- Missing or delayed market inputs can make an adaptive calculation less reliable than a conservative fallback.
- Cross-chain settlement increases the time between quote and execution and may require different bounds.
- Analytics must distinguish slippage-related failures from unrelated provider and onchain failures.

## Open questions

- What were the guardrail results? This is a measurement gap rather than an open product decision, and it is the reason the recorded outcome is `iterate` rather than `scale`.

## Outcome Contract

Transaction success and execution quality must be reviewed together. Failures can be driven to zero by widening the tolerance far enough, at which point every trade succeeds and every user overpays. So the target is one number going down while two are held flat: the price users actually get, and the revenue each trade produces.

```yaml product-os:outcome
definition:
  version: auto-slippage-v1
  method: behavioral_metric
  baseline: approximately 15% of initiated trades failing in the low-market-cap segment; the aggregate rate reads as noise and must not be used as the baseline
  target: reduce eligible slippage-related failures versus baseline without execution-quality regression
  metric: eligible native swaps and bridges failing because the accepted slippage tolerance was exceeded
  window: 14 days after measurable controlled exposure
  slices:
    - auto_vs_manual
    - swap_vs_bridge
    - liquidity_and_volatility_band
  guardrails:
    - median_execution_delta_from_quote
    - trading_revenue_per_eligible_transaction
  decision_rule: Scale only when eligible failure rate improves and neither guardrail materially regresses; otherwise revise the technical hypothesis or stop.
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## Delivery

The classification rules, data sources, coefficients, fallback algorithm, and rollout mechanics belong in an engineering-owned Implementation Plan. The PRD remains stable around the product contract: fewer avoidable failures without worse execution quality.

The measured result and the decision that followed are recorded in [Learning: Segmentation found the failure the aggregate metric hid](../learnings/auto-slippage-failure-rate.md).

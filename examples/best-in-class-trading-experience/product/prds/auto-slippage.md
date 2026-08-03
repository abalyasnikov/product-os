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

Support specialists consolidated recurring reports in Linear, while raw Intercom conversations could be inspected when the aggregate signal needed clarification. Mixpanel was then used to investigate the failure pattern and its concentration by transaction context.

The order of investigation mattered more than any single source. Checked as an aggregate, the failure rate read as noise, and the defensible conclusion would have been that no product problem existed. The problem only became visible after the transaction funnel was decomposed by stage and failures were segmented by cause, network, and asset market cap.

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

- Make Auto the default slippage mode for eligible native swaps and bridges, with no onboarding flow, feature introduction, or red dot. A default that needs explaining is not a default.
- Adapt the tolerance using current execution conditions and route characteristics rather than one preset for every transaction.
- Cap Auto at 10%. When conditions would require more, the product does not silently go further — the user must switch to manual and accept that trade explicitly.
- Cap manual override at 25%.
- Classify any token the product cannot confidently recognize into the most conservative tier rather than an optimistic default.
- Reset a custom slippage value to Auto when the user leaves the swap form, so nobody stays on a wide tolerance they set once for one trade and forgot.
- Show the tolerance only when it becomes material: hidden while Auto stays low, visible above a low threshold, warned in yellow above a moderate one, and warned in red for manual values high enough to invite front-running.
- Require renewed consent when a quote or route changes beyond the trade the user accepted.
- Define conservative fallback behavior when required inputs are missing, and log every fallback for monitoring.
- Measure Auto and manual transactions separately, including failure reason, quoted output, executed output, and support contacts.

The exact percentages above are product safety bounds and consent thresholds, so they belong in this contract. The rules that decide where a given trade lands inside those bounds do not.

### Non-goals

- Guaranteeing that every transaction executes.
- Treating provider, balance, signing, or unrelated onchain failures as slippage failures.
- Hiding material price impact or route risk from the user.
- Fixing the final classification rules, coefficients, or calculation formula in the PRD.

## Outcome Contract

Transaction success and execution quality must be reviewed together. A lower failure rate is not a successful outcome if users receive materially worse execution.

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
    - trades_with_effective_slippage_above_material_threshold
    - price_or_slippage_support_contact_rate
    - trading_revenue_per_eligible_transaction
  decision_rule: Scale only when eligible failure rate improves and no execution-quality, trust, or revenue guardrail materially regresses; otherwise revise the technical hypothesis or stop.
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## GTM hypothesis

This is a default reliability improvement, not a standalone product launch. Discovery should happen in the existing swap and bridge flow through the Auto setting and contextual warnings. Adoption is an eligible transaction using Auto; success is measured by the Outcome Contract rather than feature awareness.

## Competitors and alternatives

Jupiter's dynamic slippage was the reference point for what an Auto mode should feel like: the product picks a tolerance and the user does not think about it. That set the bar for the default, but not for the guardrails — the execution-quality contract below is the part this PRD adds rather than copies.

The alternative considered and rejected was raising the static default. It would have improved the failure rate immediately and would have shifted the cost onto users as worse prices, which is the exact outcome the Outcome Contract now forbids.

## Risks and dependencies

- A wider tolerance can conceal poor routing or expose users to worse prices.
- Missing or delayed market inputs can make an adaptive calculation less reliable than a conservative fallback.
- Cross-chain settlement increases the time between quote and execution and may require different bounds.
- Analytics must distinguish slippage-related failures from unrelated provider and onchain failures.

## Open questions

- What were the execution-quality guardrail results? Without them the decision rule cannot be fully evaluated, which is why the recorded outcome decision is `iterate` rather than `scale`.
- Where exactly does the affected market-cap band begin?
- What warning and renewed-consent thresholds are material to users?

## Delivery

The classification rules, data sources, coefficients, fallback algorithm, and rollout mechanics belong in an engineering-owned Implementation Plan. The PRD remains stable around the product contract: fewer avoidable failures without worse execution quality.

The measured result and the decision that followed are recorded in [Learning: Segmentation found the failure the aggregate metric hid](../learnings/auto-slippage-failure-rate.md).

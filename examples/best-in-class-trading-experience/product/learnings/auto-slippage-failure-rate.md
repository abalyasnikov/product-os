---
schema_version: 1
id: learning_01TRADX001
type: learning
title: Segmentation found the failure the aggregate metric hid
relationships:
  initiative: initiative_01TRADX001
  prds: [prd_01TRADX002]
product_bet_id: prd_01TRADX002
outcome_contract_ref:
  owner_artifact_id: prd_01TRADX002
  definition_version: auto-slippage-v1
measurement_anchor:
  type: release
  reference: Auto slippage enabled as the default mode for eligible native swaps and bridges
  occurred_at: "2026-04-26T00:00:00Z"
evaluation_scope: Eligible native swaps and bridges, compared before and after the adaptive slippage default. Figures are approximate and reconstructed from the original private analysis; the exact segment boundary and query definition were not recovered for this public example.
results:
  baseline: "~15% of initiated trades failed in the low-market-cap segment"
  observed: "~2% in the same segment"
  by_slice:
    low_market_cap_assets: "~15% to ~2%"
    aggregate_all_assets: "No material movement; at this scale the aggregate failure rate looked like noise both before and after"
  guardrails:
    median_execution_delta_from_quote: null
    trades_with_effective_slippage_above_material_threshold: null
    price_or_slippage_support_contact_rate: null
    trading_revenue_per_eligible_transaction: null
  provenance:
    method: analytics_query
    provider: mixpanel
    reference: Transaction funnel decomposed by stage, then failures segmented by cause, network, and asset market-cap band
    definition_version: auto-slippage-v1
    retrieved_at: "2026-05-04T00:00:00Z"
confidence: medium
confounders:
  - The same funnel decomposition produced two unrelated fixes in the same period — transaction-builder errors and gas sponsorship for users holding stablecoins but no native token — which also moved overall transaction success
  - No controlled experiment result was recovered for this example; the comparison is before and after the default change
data_limitations:
  - Figures are approximate
  - The exact market-cap boundary defining the affected segment was not recovered
  - Execution-quality guardrail results were not recovered, so the full decision rule cannot be evaluated from this record
thesis_change: The aggregate failure rate was the wrong instrument. It was low enough to read as noise while one segment failed roughly seven times more often, so a headline reliability metric is not evidence that reliability is fine.
decision_events:
  - id: decision_01TRADX010
    kind: outcome
    choice: iterate
    decided_by: product-lead
    decided_at: "2026-05-04T00:00:00Z"
    rationale: The primary metric improved decisively in the affected segment, but the contract requires that no execution-quality guardrail materially regress, and those results are not in hand for this record. Continue with the adaptive default and close the guardrail evidence before claiming the barrier is fully settled.
    based_on_version: "376230a5ab4b5d68845e75369553b5ba15755578"
---

## What changed

The signal arrived from users, not from a dashboard. People wrote in saying their trades were failing: they signed the transaction, the wallet accepted it, and it never landed onchain.

Checked at the aggregate level, the failure rate looked like noise. Stopping there would have produced a defensible and wrong conclusion — that there was no problem, only a handful of vocal users.

Decomposing the transaction funnel by stage, and then segmenting failures by cause, network, and asset market cap, moved the answer. In the low-market-cap band roughly 15% of initiated trades were failing, because a largely static slippage tolerance was applied to assets whose price moves far more between quote and inclusion than majors do. Replacing that with a tolerance adapted to asset characteristics, liquidity, and volatility took the segment to roughly 2%.

## Measurement interpretation

One aggregate number was concealing three separate problems. Alongside slippage, the same decomposition surfaced technical errors in the transaction builder and a distinct failure where users held the stablecoin they wanted to trade but no native token for gas, which was addressed by gas sponsorship for eligible cases. Three segments, three different interventions, none of them visible in the headline metric.

The order that produced this is worth keeping: qualitative signal indicated where to look, segmentation established who was actually affected, and only then was an intervention worth designing.

This Learning settles the Auto-slippage barrier only. The Initiative's shared outcome across all five barriers remains unmeasured, and passing one child contract is not evidence for the aggregate claim.

`based_on_version` references the original private product repository where the decision was reviewed, not this public example.

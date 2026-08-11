---
schema_version: 1
id: signal_01TRADX007
type: signal
title: Slippage-related trade failures concentrate in one asset band
created_at: "2025-03-04T10:00:00Z"
updated_at: "2025-03-04T10:00:00Z"
authors: [product-lead]
relationships:
  patterns: [pattern_01TRADX001]
summary: Consolidated support reports named failed trades as a recurring trust problem, and
  segmenting the failure rate by asset market-cap band showed the failures concentrated in the
  low-market-cap segment while the aggregate rate stayed flat.
sources:
  - provider: local
    external_id: local_reconstructed-support-and-telemetry-review
    occurred_at: 2025-03-04T00:00:00Z
    retrieved_at: 2025-03-04T00:00:00Z
    storage: reference_only
segments: [traders-in-low-market-cap-assets]
revenue_band: strategic
business_weight: Trading is the largest revenue line, so a failed trade is lost revenue and a
  trust problem in the same event.
interpretation_confidence: medium
---

## Context

This is the evidence behind the one bet in this example that closes its loop, and it is included
because it shows a shape the other four do not: the problem was invisible until the metric was
cut. At the aggregate level the failure rate read as noise, and only segmentation by asset
market-cap band surfaced a band failing several times more often.

That is why the Outcome Contract on [prd_01TRADX002](../prds/auto-slippage.md) names the segment as its baseline and says
outright that the aggregate rate must not be used as one. A team measuring the headline number
would have concluded there was nothing to fix, shipped nothing, and been wrong.

Provenance and limits: this Signal is reconstructed for the public example from a private
support-report consolidation and a segmented telemetry review. Figures are approximate; the exact
market-cap boundary was not recovered, and no controlled experiment was run. It evidences a
quality gap in the product's own execution, not stated user demand.

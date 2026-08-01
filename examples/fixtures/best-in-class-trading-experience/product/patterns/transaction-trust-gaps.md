---
schema_version: 1
id: pattern_01TRADX002
type: pattern
title: Trust gaps during and after transactions
created_at: "2025-02-08T11:00:00Z"
updated_at: "2025-02-08T11:00:00Z"
authors: [product-research, product-lead]
relationships:
  signals: [signal_01TRADX002, signal_01TRADX004, signal_01TRADX005, signal_01TRADX006]
  opportunity: opportunity_01TRADX001
interpretation: Destination constraints, token permissions, non-blocking navigation, and multi-step settlement remain insufficiently explicit for users to trust the transaction lifecycle.
supporting_signal_ids: [signal_01TRADX002, signal_01TRADX004, signal_01TRADX005, signal_01TRADX006]
contradictory_signal_ids: []
affected_segments: [external_address_senders, bridge_users, mobile_traders, erc20_traders]
frequency_summary: Four synthetic directional observations cover distinct trust barriers; they demonstrate synthesis and do not estimate real frequency.
business_weight_summary: The barriers may cause unsafe intent, uncertainty, or lost control, but the fixture asserts no production incident or revenue impact.
recency_summary: Synthetic source events occurred between 2025-02-01 and 2025-02-06.
coverage_gaps: [No production safety-incident baseline, No representative sample, No provider-level settlement analysis]
---

## Synthesis

The strongest planning learning occurred before delivery: embedding a generic bridge inside Send was rejected because CEX deposit constraints made that abstraction unsafe. The replacement split destination-aware Send Flow Redesign from Bridge Progress Tracking.

---
schema_version: 1
id: pattern_01TRADX001
type: pattern
title: Core trade flow friction
created_at: '2025-02-08T10:00:00Z'
updated_at: '2025-02-08T10:00:00Z'
authors:
- product-research
- product-lead
relationships:
  signals:
  - signal_01TRADX001
  - signal_01TRADX003
  opportunity: opportunity_01TRADX001
supporting_signal_ids:
- signal_01TRADX001
- signal_01TRADX003
contradictory_signal_ids: []
---

# Core trade flow friction

## Interpretation

The product turns a single trade intent into disconnected routing steps and repeats confirmation even when the authoritative wallet signature is sufficient.

## Frequency and recency

**Frequency:** Two synthetic directional observations cover route composition and confirmation; they demonstrate pattern construction and do not estimate real frequency.

**Recency:** Synthetic source events occurred between 2025-01-29 and 2025-01-31.

**Business weight:** Either barrier can interrupt a core trade, but this fixture makes no revenue or retention claim.

**Affected segments:** multi-chain_traders, repeat_traders, native_asset_traders

## Coverage gaps

- No representative sample
- No production funnel evidence at decision time
- No chain-level failure-rate estimate

## Synthesis

Supporting and contradicting Signals are listed in frontmatter; mention count is not representativeness.

## Synthesis

The barriers share one trade-completion outcome but require separate PRDs so route composition and confirmation remain independently reviewable.

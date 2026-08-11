---
schema_version: 1
id: signal_01TRADX003
type: signal
title: Native-asset trades include a redundant confirmation
created_at: "2025-02-05T10:00:00Z"
updated_at: "2025-02-05T10:00:00Z"
authors: [product-research]
relationships:
  pattern: pattern_01TRADX001
  opportunity: opportunity_01TRADX001
summary: Synthetic usability notes showed an extra application-level confirmation before the wallet signature even when no token approval was required.
sources:
  - provider: granola
    external_id: granola-fixture-trading-02
    url: https://example.invalid/granola/trading-02
    occurred_at: "2025-01-31T11:00:00Z"
    retrieved_at: "2025-02-05T09:30:00Z"
    content_fingerprint: sha256:synthetic-trading-02
    storage: reference_only
segments: [repeat_traders, native_asset_traders]
interpretation_confidence: medium
excerpt:
  text: "I already chose the route; the second confirmation felt like the same decision again."
  approved_by: research-lead
  anonymized: true
---

## Context

The finding applies only where the wallet signature remains the authoritative confirmation and no approval transaction is needed.

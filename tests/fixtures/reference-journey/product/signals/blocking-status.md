---
schema_version: 1
id: signal_01TRADX004
type: signal
title: Pending transactions trap users in a blocking screen
created_at: "2025-02-06T10:00:00Z"
updated_at: "2025-02-06T10:00:00Z"
authors: [product-research]
relationships:
  pattern: pattern_01TRADX002
  opportunity: opportunity_01TRADX001
summary: A synthetic meeting participant left the product uncertain whether a pending transaction would continue after closing the blocking progress surface.
sources:
  - provider: granola
    external_id: granola-fixture-trading-03
    url: https://example.invalid/granola/trading-03
    occurred_at: "2025-02-01T16:00:00Z"
    retrieved_at: "2025-02-06T09:20:00Z"
    content_fingerprint: sha256:synthetic-trading-03
    storage: reference_only
segments: [mobile_traders, bridge_users]
interpretation_confidence: high
excerpt:
  text: "I wanted to keep using the wallet, but I did not know whether leaving would cancel the transaction."
  approved_by: research-lead
  anonymized: true
---

## Context

This signal covers both non-blocking navigation and the need for persistent multi-step bridge progress.

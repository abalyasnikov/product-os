---
schema_version: 1
id: signal_01TRADX002
type: signal
title: Cross-chain send can hide destination constraints
created_at: "2025-02-04T10:00:00Z"
updated_at: "2025-02-04T10:00:00Z"
authors: [product-research]
relationships:
  pattern: pattern_01TRADX002
  opportunity: opportunity_01TRADX001
summary: A synthetic review showed that treating every destination as a generic cross-chain send could route assets to a CEX deposit address that does not support the resulting path.
sources:
  - provider: pasted_note
    external_id: pasted-fixture-destination-risk
    occurred_at: "2025-02-03T14:00:00Z"
    retrieved_at: "2025-02-04T09:45:00Z"
    content_fingerprint: sha256:synthetic-destination-risk
    storage: reference_only
segments: [users_sending_to_external_addresses]
interpretation_confidence: high
---

## Product implication

The original “Cross-chain Send” solution was rejected. The accepted problem framing is destination-aware Send Flow Redesign; bridge progress is handled separately.

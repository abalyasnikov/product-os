---
schema_version: 1
id: signal_01TRADX006
type: signal
title: Bridge completion is ambiguous after the source transaction
created_at: "2025-02-07T11:00:00Z"
updated_at: "2025-02-07T11:00:00Z"
authors: [product-research]
relationships:
  pattern: pattern_01TRADX002
  opportunity: opportunity_01TRADX001
summary: A synthetic journey review showed that a source-chain confirmation could look complete while the bridge still had destination-chain work remaining.
sources:
  - provider: pasted_note
    external_id: pasted-fixture-bridge-progress
    occurred_at: "2025-02-06T15:00:00Z"
    retrieved_at: "2025-02-07T10:40:00Z"
    content_fingerprint: sha256:synthetic-bridge-progress
    storage: reference_only
segments: [bridge_users, cross_chain_senders]
interpretation_confidence: high
---

## Context

This is separate from the blocking-screen observation: a non-blocking UI can still fail if it collapses a multi-step bridge into one ambiguous status.

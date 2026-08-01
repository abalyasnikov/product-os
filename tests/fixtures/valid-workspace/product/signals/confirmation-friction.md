---
schema_version: 1
id: signal_01JABCDE02
type: signal
title: Confirmation does not explain the next state
created_at: "2026-05-05T11:00:00Z"
updated_at: "2026-05-05T11:00:00Z"
authors: [researcher]
relationships:
  pattern: pattern_01JABCDE01
  opportunity: opportunity_01JABCDE01
summary: A returning user delayed confirmation because the interface did not explain the pending state or expected completion time.
sources:
  - provider: granola
    external_id: meeting-fixture-b
    url: https://example.invalid/meetings/meeting-fixture-b
    occurred_at: "2026-05-03T16:00:00Z"
    retrieved_at: "2026-05-05T10:30:00Z"
    content_fingerprint: sha256:fixture-b-v1
    storage: reference_only
segments: [returning_users]
interpretation_confidence: high
---

## Context

The observed barrier concerned confidence in the transaction lifecycle, not asset discovery.

---
schema_version: 1
id: signal_01JABCDE01
type: signal
title: New users cannot compare routes confidently
created_at: "2026-05-04T10:00:00Z"
updated_at: "2026-05-04T10:00:00Z"
authors: [researcher]
relationships:
  pattern: pattern_01JABCDE01
  opportunity: opportunity_01JABCDE01
summary: A newly funded user abandoned a first transaction because route costs and timing were not comparable before confirmation.
sources:
  - provider: granola
    external_id: meeting-fixture-a
    url: https://example.invalid/meetings/meeting-fixture-a
    occurred_at: "2026-05-02T15:00:00Z"
    retrieved_at: "2026-05-04T09:30:00Z"
    content_fingerprint: sha256:fixture-a-v1
    storage: reference_only
segments: [new_users]
interpretation_confidence: high
excerpt:
  text: "I could not tell which route would finish reliably, so I stopped before confirming."
  approved_by: research-lead
  anonymized: true
---

## Context

The user had sufficient funds and intent; uncertainty at route selection blocked completion.

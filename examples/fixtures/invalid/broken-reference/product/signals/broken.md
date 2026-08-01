---
schema_version: 1
id: signal_01JBRKEN01
type: signal
title: Broken relationship reference
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-01-01T00:00:00Z"
authors: [fixture-author]
relationships:
  opportunity: opportunity_01JMSNG001
summary: The relationship points to an artifact that is absent from this workspace.
sources:
  - provider: pasted_note
    external_id: broken-reference
    occurred_at: "2026-01-01T00:00:00Z"
    retrieved_at: "2026-01-01T00:00:00Z"
    storage: reference_only
segments: [fixture]
interpretation_confidence: high
---

Expected failure: unknown relationship ID.

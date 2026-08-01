---
schema_version: 1
id: prd_01JMSMATC1
type: signal
title: Prefix and type disagree
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-01-01T00:00:00Z"
authors: [fixture-author]
relationships: {}
summary: The artifact declares signal but uses a PRD-prefixed ID.
sources:
  - provider: pasted_note
    external_id: type-mismatch
    occurred_at: "2026-01-01T00:00:00Z"
    retrieved_at: "2026-01-01T00:00:00Z"
    storage: reference_only
segments: [fixture]
interpretation_confidence: high
---

Expected failure: type and ID prefix mismatch.

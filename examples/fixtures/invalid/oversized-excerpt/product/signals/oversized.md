---
schema_version: 1
id: signal_01JEXCERPT1
type: signal
title: Oversized excerpt
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-01-01T00:00:00Z"
authors: [fixture-author]
relationships: {}
summary: This synthetic excerpt intentionally exceeds the default five-hundred-character policy limit.
sources:
  - provider: pasted_note
    external_id: oversized-excerpt
    occurred_at: "2026-01-01T00:00:00Z"
    retrieved_at: "2026-01-01T00:00:00Z"
    storage: reference_only
segments: [fixture]
interpretation_confidence: high
excerpt:
  text: "Synthetic anonymized fixture text repeats only to exceed the configured excerpt boundary. Synthetic anonymized fixture text repeats only to exceed the configured excerpt boundary. Synthetic anonymized fixture text repeats only to exceed the configured excerpt boundary. Synthetic anonymized fixture text repeats only to exceed the configured excerpt boundary. Synthetic anonymized fixture text repeats only to exceed the configured excerpt boundary. Synthetic anonymized fixture text repeats only to exceed the configured excerpt boundary. Synthetic anonymized fixture text repeats only to exceed the configured excerpt boundary."
  approved_by: fixture-author
  anonymized: true
---

Expected failure: excerpt exceeds 500 characters.

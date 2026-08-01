---
schema_version: 1
id: pattern_<stable-id>
type: pattern
title: <repeated or conflicting behavior>
created_at: <ISO-8601 timestamp>
updated_at: <ISO-8601 timestamp>
authors: [<owner>]
relationships:
  signals: [signal_<id>]
interpretation: <agent interpretation, distinct from source facts>
supporting_signal_ids: [signal_<id>]
contradictory_signal_ids: []
affected_segments: [<segment>]
frequency_summary: <bounded count and sample context>
recency_summary: <evidence time range>
coverage_gaps: [<known gap>]
---

## Synthesis

Explain the pattern without claiming representativeness the evidence does not support.

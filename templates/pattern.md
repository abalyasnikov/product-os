---
schema_version: 1
id: pattern_<stable-id>
type: pattern
title: <repeated or conflicting behavior>
relationships:
  signals: [signal_<id>]
supporting_signal_ids: [signal_<id>]
contradictory_signal_ids: []
---

# <Title>

<!--
Persist a Pattern only when at least two Opportunities will reference the same synthesis, or when
evidence needs to be parked before any decision exists. One bet with one Opportunity does not need
a Pattern — the Opportunity already records contradictions and coverage gaps. Delete this comment.
-->

## Interpretation

<The agent's interpretation, stated as interpretation and kept distinct from the source facts.
Link the Signals you name: `[signal_01ABCDEF](../signals/short-name.md)`.>

## Frequency and recency

**Frequency:** <bounded count and the sample it came from; a mention count is not representativeness>

**Recency:** <the time range this evidence covers>

**Affected segments:** <segments, and the ones absent from the evidence>

## Coverage gaps

- <what this evidence cannot tell you>

## Synthesis

<Explain the pattern without claiming representativeness the evidence does not support. Say what
the contradicting Signals mean rather than averaging them away.>

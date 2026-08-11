---
schema_version: 1
id: opportunity_<stable-id>
type: opportunity
title: <blocked user value>
relationships:
  signals: [signal_<id>]
evidence_ids: [signal_<id>]
evidence_quality:
  contradictions: []
  coverage_gaps: []
decision_events: []
---

# <Title>

<!--
Frontmatter carries the evidence graph, the two evidence facts a check can count, and the
append-only human decision. Everything a human reads to make that decision lives below.
Delete this comment.
-->

## Blocked value

<What users cannot realize today.>

## Affected users

<Who is affected, and who is not. Name the segment you have not heard from. When you name a
Signal here, link it: `[signal_01ABCDEF](../signals/short-name.md)`.>

## Impact and urgency

**Impact:** <user and business impact, with the number's source>

**Urgency:** <why now, or an honest statement that nothing makes this urgent this period>

## Strategic fit

<Quote the specific goal, priority band, and principle from `context/strategy.md` that this rests
on, and name the principle it puts under pressure. "Aligned with strategy" is not an argument.>

## Evidence quality

**Source diversity:** <how many independent kinds of source, not how many mentions>

**Segment concentration:** <where the evidence clusters>

**Recency:** <the time range the evidence covers>

<!-- Contradictions and coverage gaps are recorded in frontmatter so a check can count them. -->

## Assumptions and risks

**Assumptions**

- <assumption this bet rests on>

**Risks**

- <risk, including the risk that the honest version of the fix is weaker than what was asked for>

## Decision question

Should a Product Bet be pursued, held, or rejected?

<The specific judgment this Product Lead has to make, in one paragraph.>

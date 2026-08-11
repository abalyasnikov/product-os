---
schema_version: 1
id: opportunity_01TRADX001
type: opportunity
title: Make trading continuous across chains and transaction states
created_at: '2025-02-09T10:00:00Z'
updated_at: '2025-02-10T16:00:00Z'
authors:
- product-lead
relationships:
  signals:
  - signal_01TRADX001
  - signal_01TRADX003
  - signal_01TRADX004
  - signal_01TRADX006
  patterns:
  - pattern_01TRADX001
  - pattern_01TRADX002
  initiative: initiative_01TRADX001
evidence_ids:
- signal_01TRADX001
- signal_01TRADX003
- signal_01TRADX004
- signal_01TRADX006
- pattern_01TRADX001
- pattern_01TRADX002
evidence_quality:
  contradictions: []
  coverage_gaps:
  - No representative behavioral baseline
  - No real support-volume weighting
  - No production chain or region slices
decision_events:
- id: decision_01TRADX001
  kind: opportunity
  choice: pursue
  decided_by: product-lead
  decided_at: '2025-02-10T16:00:00Z'
  rationale: The barriers block one strategic user outcome but are separable enough to pursue as a four-PRD
    Initiative with explicit guardrails.
  based_on_version: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
---

# Make trading continuous across chains and transaction states

## Blocked value

Users cannot reliably move from trade intent through confirmation and cross-chain settlement in one understandable product journey.

## Affected users

Users swapping across chains, repeat native-asset traders, and bridge users.

## Impact and urgency

**Impact:** Friction can block core asset movement or leave users uncertain about safety and completion.

**Urgency:** The gaps span the primary transaction journey and compound as multi-chain use grows.

## Strategic fit

A best-in-class wallet should make complex onchain execution understandable without requiring users to assemble multiple tools and mental models.

## Evidence quality

**Source diversity:** Three synthetic Granola meeting snapshots and one synthetic pasted research note.

**Segment concentration:** Each barrier has only one directional source; evidence is intentionally insufficient for prevalence claims.

**Recency:** All illustrative sources fall within ten days of the pursue decision.

Recorded contradictions and coverage gaps are in frontmatter, where a check can count them.

## Assumptions and risks

**Assumptions**

- A coherent journey can be delivered through multiple independently measurable interventions
- Provider and chain differences can be abstracted without hiding material risk

**Risks**

- A unified flow could obscure route constraints
- Faster confirmation could weaken informed consent
- Aggregate measurement may hide a weak child intervention

## Decision question

Should a Product Bet be pursued, held, or rejected?

## Decision

Pursue as an Initiative, with separate PRDs for route composition, confirmation, non-blocking status, and bridge progress.

---
schema_version: 1
id: opportunity_01TRADX001
type: opportunity
title: Make trading continuous across chains and transaction states
created_at: "2025-02-09T10:00:00Z"
updated_at: "2025-02-10T16:00:00Z"
authors: [product-lead]
relationships:
  signals: [signal_01TRADX001, signal_01TRADX002, signal_01TRADX003, signal_01TRADX004, signal_01TRADX005, signal_01TRADX006]
  patterns: [pattern_01TRADX001, pattern_01TRADX002]
  initiative: initiative_01TRADX001
blocked_value: Users cannot reliably move from trade or send intent through permissions, confirmation, and cross-chain settlement in one understandable product journey.
evidence_ids: [signal_01TRADX001, signal_01TRADX002, signal_01TRADX003, signal_01TRADX004, signal_01TRADX005, signal_01TRADX006, pattern_01TRADX001, pattern_01TRADX002]
affected_users: Users swapping or sending across chains, repeat native-asset traders, bridge users, and users managing ERC-20 allowances.
impact: Friction can block core asset movement or leave users uncertain about safety and completion.
urgency: The gaps span the primary transaction journey and compound as multi-chain use grows.
strategic_fit: A best-in-class wallet should make complex onchain execution understandable without requiring users to assemble multiple tools and mental models.
assumptions: [A coherent journey can be delivered through multiple independently measurable interventions, Provider and chain differences can be abstracted without hiding material risk]
risks: [A unified flow could obscure destination constraints, Faster confirmation could weaken informed consent, Aggregate measurement may hide a weak child intervention]
evidence_quality:
  source_diversity: Three synthetic Granola meeting snapshots and three synthetic pasted research notes.
  segment_concentration: Each barrier has only one directional source; evidence is intentionally insufficient for prevalence claims.
  recency: All illustrative sources fall within ten days of the pursue decision.
  contradictions: [The first Cross-chain Send solution was rejected because generic routing could be unsafe for some CEX deposit destinations]
  coverage_gaps: [No representative behavioral baseline, No real support-volume weighting, No production chain or region slices]
decision_events:
  - id: decision_01TRADX001
    kind: opportunity
    choice: pursue
    decided_by: product-lead
    decided_at: "2025-02-10T16:00:00Z"
    rationale: The barriers block one strategic user outcome but are separable enough to pursue as a six-PRD Initiative with explicit safety guardrails.
    based_on_version: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
---

## Decision

Pursue as an Initiative. Do not implement the rejected generic Cross-chain Send concept; validate destination-aware send behavior and bridge progress separately.

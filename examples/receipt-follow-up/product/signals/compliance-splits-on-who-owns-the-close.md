---
schema_version: 1
id: signal_01RCPT003
type: signal
title: Receipt compliance splits on whether anyone owns the month-end close
created_at: "2026-08-07T10:00:00Z"
updated_at: "2026-08-07T10:00:00Z"
authors: [product-lead]
relationships: {}
summary: Across 214 workspaces with ten or more active cardholders, median seven-day receipt
  compliance is 74% where more than one admin seat exists and 55% where a single admin runs the
  workspace.
sources:
  - provider: local
    external_id: local_illustrative-self-serve-analytics-pull
    occurred_at: 2026-08-07T00:00:00Z
    retrieved_at: 2026-08-11T00:00:00Z
    storage: reference_only
segments: [single-admin-workspaces, 10plus-cardholders]
revenue_band: unknown
business_weight: The single-admin workspace is the segment named in this year's positioning, and
  it is the weaker half of this split.
interpretation_confidence: low
---

## Context

The aggregate number — 62% median compliance — is close to useless for a decision. The split is
the finding, and it points away from the loudest evidence: the account complaining hardest has a
finance function and sits in the stronger half.

Two facts blunt the urgency. 71% of missing receipts are attached within 30 days, and the median
late attachment lands on day nine. The cost is therefore the admin's chasing time, not an
unrecoverable ledger gap, and any target should be argued in those terms.

Confidence is low deliberately. The query is self-serve and unreviewed; the multi-admin-seat proxy
for "has a finance function" is untested; exempt transactions such as cash, refunds, and personal
spend are not excluded; roughly 30% of workspaces never changed the default threshold; and there
is no cut by cardholder seniority, which is the cut the interviewed admin cared about most.

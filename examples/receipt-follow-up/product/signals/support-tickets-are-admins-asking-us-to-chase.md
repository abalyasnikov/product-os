---
schema_version: 1
id: signal_01RCPT002
type: signal
title: Most receipt-policy support tickets are admins asking support to do the chasing
created_at: "2026-07-31T10:00:00Z"
updated_at: "2026-07-31T10:00:00Z"
authors: [support-lead]
relationships: {}
summary: Receipt and policy was 21% of Q3 inbound support (88 of 412 tickets, up 14% month over
  month), and 51 of those 88 are admins asking the support team to bulk-remind or bulk-export on
  their behalf.
sources:
  - provider: local
    external_id: local_illustrative-support-report-q3
    occurred_at: 2026-07-31T00:00:00Z
    retrieved_at: 2026-08-11T00:00:00Z
    storage: reference_only
segments: [workspace-admins, all-plans]
revenue_band: unknown
business_weight: Three accounts escalated this to their account manager in Q3, and one churned
  account named receipt chasing in its exit call.
interpretation_confidence: high
---

## Context

A ticket tag is a support artifact, not a user statement, so the count matters less than the
read-through: the modal ticket is an admin trying to outsource the chase, sometimes literally
asking support to send the emails. That is a workflow gap, not a documentation gap.

A second cluster is different in kind and easy to merge away by mistake. Twenty-two tickets are
cardholders confused about a flag, and in fourteen of those the receipt existed but was attached
to the wrong transaction. That is a matching failure, not a compliance failure, and no product
analytics event exists for it, so its true size is unknown.

Gaps: one quarter of one support queue; tags are assigned by the support team; the churn
attribution rests on a single exit call.

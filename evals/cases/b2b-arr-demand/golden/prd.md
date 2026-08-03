---
schema_version: 1
id: prd_01EVALB2B001
type: prd
title: Audit-log export for compliance review
relationships:
  opportunity: opportunity_01EVALB2B001
  signals: [signal_01EVALB2B001, signal_01EVALB2B002]
---

# Audit-log export for compliance review

## Problem

B2B administrators cannot hand reviewers a bounded record of workspace activity. This creates manual evidence work and can block a compliance review, but the available account requests do not prove market-wide demand.

**Why now / business reality:** Two active account conversations are blocked on the same review workflow, with timing and commercial consequence preserved in their source records.

## Evidence

`signal_01EVALB2B001` records Northstar's request and its source-backed $120k ARR. `signal_01EVALB2B002` records Harbor's request and its source-backed $60k ARR. Together the linked demand represents $180k ARR. ARR is a business-weight input, not an automatic product priority; effort, strategic fit, risk, and demand beyond these accounts remain unresolved.

### References

- `signal_01EVALB2B001` — Northstar request and account context
- `signal_01EVALB2B002` — Harbor request and account context

## JTBD

When an external reviewer asks for activity evidence, I want to export a bounded and understandable audit record, so that I can complete the review without assembling events manually.

## Current and desired journey

Today an administrator gathers activity from separate views and explains missing context. The desired journey lets the administrator choose a review boundary, generate a complete record, and understand what is and is not included.

## Scope

### Requirements

- The administrator can choose the workspace and review period represented by the export.
- The export identifies actor, action, object, and event time where those facts exist.
- The product states any known coverage limitation before export.
- Repeating the same export criteria produces a consistently interpretable record.

### Non-goals

- Certifying the customer's compliance program.
- Replacing the customer's governance system.
- Treating linked ARR as the delivery sequence.

## Outcome Contract

Better means a design-partner administrator can answer the agreed compliance-review questions using the export without reconstructing activity manually.

```yaml product-os:outcome
definition:
  version: audit-export-review-v1
  method: acceptance_journey
  baseline: to establish
  target: Every agreed review question is answerable from the export or an explicit coverage limitation
  metric: compliance review questions answerable without manual event reconstruction
  window: before design-partner release and at the first review
  slices: [standard_admin, restricted_admin]
  guardrails: [unauthorized_data_exposure, missing_coverage_disclosure, ambiguous_actor]
  decision_rule: Release only when critical reviewer questions pass and access-control guardrails hold.
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## GTM hypothesis

The initial audience is B2B administrators preparing external reviews. The promise is a review-ready activity record with explicit coverage. Distribution begins through the linked account conversations; adoption is a completed review using the export. Broader positioning and demand measurement remain to establish.

## Risks and dependencies

- Historical event coverage may differ by activity type.
- Export permissions must match the administrator's current access.

## Open questions

- Which reviewer questions are common across the linked accounts and which are customer-specific?

## Delivery

Linear owns delivery priority and engineering estimates. Data contracts, export generation, and storage choices belong in an engineering-owned Implementation Plan, not this PRD.

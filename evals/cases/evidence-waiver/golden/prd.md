---
schema_version: 1
id: prd_01EVALWAIVER001
type: prd
title: Guided empty state for a new workspace
relationships:
  opportunity: opportunity_01EVALWAIVER001
  signals: []
---

# Guided empty state for a new workspace

## Problem

A newly created workspace has no content and offers no clear first useful action. The team believes this delays activation, but no approved user evidence or behavioral baseline is available yet.

**Why now / business reality:** The empty state will ship with the imminent workspace launch, so the team must choose a reversible default before sufficient evidence exists.

## Evidence

No qualifying Signal is available. This PRD proceeds under the explicit waiver below and must not describe the activation problem as validated demand.

### References

- No user-evidence reference available at this decision point.

## Evidence waiver

- **Assumption:** a clear first action will help a new administrator reach initial value.
- **Rationale:** the current empty state is unavoidable in the imminent workspace launch and a reversible intervention is needed.
- **Risk:** the guidance may optimize an internal mental model instead of the user's actual first job.
- **Review date:** 2026-09-01.
- **Owner:** product-lead.
- **Exit condition:** replace the waiver with observed onboarding evidence and a measured baseline, or remove the intervention.

## JTBD

When I enter a workspace with no content, I want to understand the first useful action, so that I can begin without learning the whole system upfront.

## Current and desired journey

Today the administrator sees an empty surface and must infer what creates value. The desired journey presents one reversible starting action, explains its result, and leaves alternative navigation available.

## Scope

### Requirements

- The empty state identifies a first useful action and the outcome it creates.
- The user can decline the guidance and navigate elsewhere.
- The product does not imply that setup is complete before the resulting state exists.

### Non-goals

- A full onboarding curriculum.
- Personalization without evidence.
- Claiming an activation improvement before measurement.

## Outcome Contract

Better means the team can observe whether new administrators reach an agreed first-value event without introducing a trapped setup flow.

```yaml product-os:outcome
definition:
  version: empty-state-first-value-v1
  method: behavioral_metric
  baseline: to establish
  target: proposed movement toward the agreed first-value event
  metric: new administrators reaching the first-value event
  window: first evidence-waiver review
  slices: [new_workspace_admin]
  guardrails: [dismissal_blocked, false_completion, support_contact]
  decision_rule: Keep only if a baseline is established and observed evidence supports the assumed job; otherwise revise or remove.
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## GTM hypothesis

The audience is a new workspace administrator. The promise is a clear path to first value. Discovery is the empty workspace itself; adoption is the first-value event. Positioning remains provisional until the waiver is replaced by evidence.

## Risks and dependencies

- The first-value event is not yet validated.
- Guidance may hide other legitimate entry paths.

## Open questions

- What user-observed outcome should define first value?

## Delivery

Linear owns delivery planning. Any state machine, instrumentation design, or component behavior belongs in an engineering-owned Implementation Plan; this PRD records the reversible product decision and its waiver.

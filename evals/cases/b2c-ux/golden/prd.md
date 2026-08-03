---
schema_version: 1
id: prd_01EVALB2C001
type: prd
title: Non-blocking transaction status
relationships:
  opportunity: opportunity_01EVALB2C001
  signals: [signal_01EVALB2C001, signal_01EVALB2C002]
---

# Non-blocking transaction status

## Problem

Wallet users can become trapped in a pending-transaction surface and cannot tell whether leaving it will interrupt execution. The observed value blockage is loss of control and confidence after submission; the evidence does not establish how common the problem is.

**Why now / business reality:** Transaction status is part of the current core journey, while the team lacks a trustworthy baseline for how often the blocking state prevents another task.

## Evidence

The moderated journey in `signal_01EVALB2C001` observed blocked navigation. The support note in `signal_01EVALB2C002` independently records uncertainty about leaving the screen. Both are directional sources; neither provides a behavioral baseline or representative frequency.

### References

- `signal_01EVALB2C001` — moderated journey
- `signal_01EVALB2C002` — support note

## JTBD

When a submitted transaction is still pending, I want to continue using my wallet and recover its status later, so that I stay in control without guessing whether I cancelled it.

## Current and desired journey

Today the user submits, enters a blocking status surface, and must choose between waiting or leaving without confidence. The desired journey returns control immediately after submission while preserving a truthful, recoverable status until the transaction reaches a terminal state.

## Scope

### Requirements

- Pending status does not block navigation to the rest of the wallet.
- The same transaction remains discoverable after the user leaves the status surface.
- Terminal success or failure remains explicit and links to transaction details.

### Non-goals

- Changing chain settlement speed.
- Predicting completion when the provider cannot supply a reliable estimate.
- Redesigning transaction submission.

## Outcome Contract

Better means an eligible user can leave a pending transaction, continue another wallet task, and later recover the correct state without a false completion signal.

```yaml product-os:outcome
definition:
  version: non-blocking-status-v1
  method: acceptance_journey
  baseline: to establish
  target: All defined navigation and state-recovery cases pass
  metric: successful continuation and later transaction-state recovery
  window: before release and the first post-release review
  slices: [pending, success, failed]
  guardrails: [duplicate_submission, lost_transaction, false_terminal_state]
  decision_rule: Ship only when every critical state-recovery case passes and no guardrail fails.
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## GTM hypothesis

The audience is active wallet users submitting transactions. The promise is that a pending transaction no longer stops the rest of the wallet. Discovery happens in the existing transaction flow; adoption is continuing another task while status remains recoverable. Measurement uses the same continuation and recovery definition, with a baseline to establish.

## Risks and dependencies

- State events may arrive late or out of order.
- A compact status could hide a material failure if terminal states are not prominent.

## Open questions

- Which wallet destinations must remain available while a transaction is pending?

## Delivery

Linear owns engineering estimates and sequencing. Technical behavior belongs in an engineering-owned Implementation Plan if one is needed; this PRD owns the user-visible states and Outcome Contract.

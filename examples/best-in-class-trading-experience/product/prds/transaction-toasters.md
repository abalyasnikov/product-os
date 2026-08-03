---
schema_version: 1
id: prd_01TRADX004
type: prd
title: Transaction Toasters
relationships:
  initiative: initiative_01TRADX001
---

# Transaction Toasters

## Problem

After confirming a transaction, the user was taken through full-screen pending and success pages that blocked the entire wallet. They could not start another swap, inspect the portfolio, or browse while waiting. The cost was especially visible for bridge transactions that can take minutes.

**Why now / business reality:** Blocking status affected every supported transaction type and was most costly during long bridge waits; the proposed effect on transaction frequency had not yet been measured.

## Evidence

The existing flow visibly blocked all further work after submission. Ethereum confirmation could take seconds and bridge settlement much longer. Power users performing several transactions had to wait through the same blocking sequence repeatedly. Phantom and Rainbow used non-blocking status patterns.

The source document proposed that blocking pages reduce transaction frequency, but it did not contain a causal measurement. That relationship remains a hypothesis to test.

| Source | Observation | Date/window | Confidence |
|---|---|---|---|
| Product-flow inspection | Pending and success pages blocked the rest of the wallet after submission | March 2, 2026 source snapshot | High for current behavior |
| Transaction timing constraints | Confirmation and bridge settlement can outlast a useful blocking interaction | Historical product context | High for duration variability; impact unmeasured |
| Public competitor review | Phantom and Rainbow used non-blocking transaction status | Q1 2026 snapshot | Directional market evidence only |

## JTBD

> When I submit a transaction, I want to see its status without losing my current context, so that I can continue using the wallet and start my next action immediately.

## Current and desired journey

**Current:** submit a transaction, wait on a full-screen pending page, acknowledge a full-screen success page, then return to the wallet.

**Desired:** submit a transaction, remain in context, see a compact status notification transition from pending to success or failure, and open transaction details only when needed.

## Scope

### Requirements

- Show a compact, non-blocking notification after submission with action, description, and status.
- Support explicit states: pending, success, and failed.
- Open the transaction activity entry when the notification is selected.
- Reset the originating form and make the wallet interactive immediately after submission.
- Track multiple concurrent transactions independently and provide a comprehensible collapsed state when necessary.
- Use the same status pattern for swap, send, approve, revoke, bridge, and cross-chain swap.
- Preserve a durable activity record after the temporary notification disappears.

### Non-goals

- Replacing transaction activity with transient notifications.
- Treating submission as settlement.
- Defining bridge-specific progress stages; those belong to Bridge Progress Tracking.

## Outcome Contract

The original work proposed reducing the time before another action from roughly 15 seconds to under 3 seconds. That baseline must be remeasured before it is used as a claim.

A second original measure—transactions per active session—remains useful as a diagnostic. An increase would be consistent with the hypothesis, but would not by itself prove that Transaction Toasters caused it.

```yaml product-os:outcome
definition:
  version: transaction-toasters-v1
  method: behavioral_metric
  baseline: approximately 15 seconds proposed in the source document; verify before rollout
  target: next action is available within 3 seconds of submission for eligible flows
  metric: time from transaction submission to the wallet accepting the next independent user action
  window: 14 days after exposure
  slices:
    - swap
    - send
    - approve
    - bridge
    - concurrent_transactions
  guardrails:
    - duplicate_submission_rate
    - missing_activity_entry
    - stale_terminal_status
    - transaction_failure_rate
  decision_rule: Scale if the next-action time reaches the target without losing durable status, duplicating submissions, or increasing failures.
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## GTM hypothesis

The audience is active users who perform several wallet actions per session. The promise is simple: keep using the wallet while transactions complete. Discovery is intrinsic to the first eligible transaction; adoption can be observed through continued in-session activity and repeat transactions.

## Risks and dependencies

- A transient notification can make failure easier to miss unless activity remains durable.
- Concurrent notifications can create noise or hide the most important state.
- All clients need a consistent transaction identity and state model.

## Open questions

- How long should terminal success remain visible?
- Should failure persist until acknowledged?
- At what concurrency should individual notifications collapse into a summary?

## Delivery

Delivery was tracked in Linear. Component architecture, queueing, persistence, and platform-specific presentation belong in the implementation plan.

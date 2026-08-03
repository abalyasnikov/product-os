---
schema_version: 1
id: prd_01TRADX003
type: prd
title: Skip Signing Screen for Native Transactions
relationships:
  initiative: initiative_01TRADX001
---

# Skip Signing Screen for Native Transactions

## Problem

Native swap, approve, and bridge flows showed a signing screen after the user had already reviewed the same amounts, route, and fees on the product form. When simulation and security checks were clean, the extra screen added no new decision and made every trade slower.

The screen remained valuable when something material changed or a warning existed. The product problem was not the presence of confirmation; it was showing the same confirmation unconditionally.

**Why now / business reality:** Competitors and Zerion Perps already used the shorter interaction pattern while native wallet flows still repeated a clean review; the abandonment impact had not yet been measured. This is where the principle order in [strategy context](../../context/strategy.md) did visible work: **Fast** argued for removing the screen outright, **Reliable** outranks it, so the removal is conditional on clean simulation and security checks instead of unconditional.

## Evidence

The duplicate step was directly observable in the current journey. Phantom, Rainbow, and Rabby already skipped an equivalent screen for eligible native flows, and Zerion used the same interaction pattern in Perps.

The source work did not establish a measured abandonment baseline. Security confidence and simulation cost were open questions, so fewer screens could not be treated as an unconditional good.

| Source | Observation | Date/window | Confidence |
|---|---|---|---|
| Product-flow inspection | Clean native transactions repeated amounts, route, and fees on a second screen | February–March 2026 snapshot | High for current behavior |
| Existing Perps flow | A native product flow already used direct authorization after review | Q1 2026 snapshot | High for internal feasibility; not outcome evidence |
| Public competitor review | Phantom, Rainbow, and Rabby used equivalent reduced-confirmation patterns | Q1 2026 snapshot | Directional market evidence only |

## JTBD

> When I have reviewed a native transaction and nothing material is wrong, I want it to proceed after device authorization, so that I do not repeat the same decision on another screen.

## Current and desired journey

**Current:** review the native form, tap the action, review a second screen containing substantially the same information, then authorize the transaction.

**Desired:** review the native form, tap the action, authorize with the wallet or device, and submit. If simulation, security checks, or quote changes produce a material warning, show the signing screen with the new context.

## Scope

### Requirements

- Apply only to eligible app-initiated flows using the native transaction builder: swap, approve, and bridge.
- Continue to run transaction simulation and security checks before every eligible submission.
- Skip the signing screen only when checks are clean and the signed intent still matches what the user reviewed.
- Show the signing screen whenever simulation or security checks produce a material warning.
- Require renewed review when amounts, destination, permissions, route, or fees change materially.
- Preserve wallet and device authorization; this PRD removes duplicate product review, not signature security.
- Keep dApp-initiated WalletConnect and browser transactions on the explicit signing screen because the user has not reviewed them in a native form.

### Non-goals

- Removing simulation or security checks.
- Auto-signing without wallet or device authorization.
- Hiding material warnings to reach a lower signing-screen rate.
- Changing the Send flow, which did not use the same transaction-builder path.

## Outcome Contract

The product should remove redundant interaction while preserving or improving completion and warning coverage. Signing-screen frequency is diagnostic, not a target: optimizing it directly would create an unsafe incentive.

```yaml product-os:outcome
definition:
  version: native-confirmation-v1
  method: behavioral_metric
  baseline: interaction count and completion baseline to establish
  target: fewer user actions from accepted quote to submitted transaction while completion is no worse than baseline
  metric: median user actions and elapsed time from accepted native quote to submitted transaction
  window: 14 days after eligible exposure
  slices:
    - swap
    - approve
    - bridge
    - warning_present
  guardrails:
    - material_warning_coverage
    - transaction_failure_rate
    - user_cancellation_rate
    - signed_intent_mismatch
  decision_rule: Scale only when redundant interaction falls, completion does not regress, and every material warning remains surfaced.
binding:
  status: planned
  owner: product-lead
  due_before: release
```

## GTM hypothesis

This is primarily an experience improvement for active traders rather than a standalone acquisition message. The promise is a faster native transaction flow with the same safety checks. Discovery happens by using Swap, Approve, or Bridge; adoption is repeated eligible use without increased cancellation or support contacts.

## Risks and dependencies

- Missed simulation or security coverage becomes more consequential when the explicit review screen is absent.
- Simulating every provider quote may create cost or rate-limit pressure.
- Cross-platform differences can produce inconsistent warning behavior.

## Open questions

- Should rollout begin with swaps before approvals and bridges?
- Which selected quote should be simulated, and at what point in the journey?
- What exact changes invalidate the previously reviewed intent?

## Delivery

Delivery was tracked in Linear across mobile and extension clients. The implementation must define a single eligibility rule for clean native flows; that technical design belongs outside this PRD.

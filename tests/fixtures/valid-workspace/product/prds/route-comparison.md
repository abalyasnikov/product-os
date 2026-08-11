---
schema_version: 1
id: prd_01JABCDE01
type: prd
title: Comparable transaction routes
created_at: '2026-05-10T09:00:00Z'
updated_at: '2026-05-20T15:00:00Z'
authors:
- product-lead
relationships:
  opportunity: opportunity_01JABCDE01
  initiative: initiative_01JABCDE01
  signals:
  - signal_01JABCDE01
  - signal_01JABCDE03
implementation_refs:
- repository: github.com/example/transaction-app
  path: specs/route-comparison/implementation-plan.md
  based_on_prd_id: prd_01JABCDE01
  based_on_prd_version: '3333333333333333333333333333333333333333'
  adr_references:
  - adr/0042-route-estimate-presentation.md
delivery_refs:
- provider: linear
  external_id: linear-project-route-fixture
  url: https://linear.example.invalid/project/route-fixture
  synced_from_version: '3333333333333333333333333333333333333333'
---

# Comparable transaction routes

## Problem

Users cannot compare route cost, expected time, and failure risk before confirmation.

**Why now / business reality:** Recorded on the linked evidence above; this fixture carries no separate timing claim.

## Evidence

Linked evidence: `signal_01JABCDE01`, `signal_01JABCDE03`, `pattern_01JABCDE01`.

## JTBD

**Who:** Funded users selecting a route, with a compact default for experienced users.

**When** the current journey below applies, **I want** to reach the desired journey below, **so that** eligible users select and confirm a route without an uncertainty-driven abandonment.

## Current and desired journey

**Current:** The user sees route names and cost but cannot inspect expected timing or the failure explanation before confirming.

**Desired:** The user sees a concise recommended route and can progressively reveal comparable cost, time, and reliability cues.

## Scope

### Requirements

- Show one recommended route with cost and expected-time rationale
- Allow comparison without leaving the transaction flow
- Preserve a compact one-action path for experienced users

### Non-goals

- Designing a new routing algorithm
- Guaranteeing network settlement time
- Engineering task decomposition

## GTM hypothesis

**Audience:** Funded users evaluating their first route

**Promise:** Know why a route is recommended before confirming

**Discovery channel:** Transaction route selector

**Adoption action:** Open comparison and confirm a route

**Launch measurement:** Route-selection completion and power-user confirmation time

## Risks and dependencies

- Reliability language may overstate provider certainty
- Additional details may slow the expert path
- Route provider exposes comparable estimates

## Open questions

None.

## Outcome Contract

Eligible users select and confirm a route without an uncertainty-driven abandonment.

```yaml product-os:outcome
definition:
  version: route-cases-v2
  method: acceptance_journey
  baseline: Users cannot compare time and reliability before confirmation.
  target: A user can compare the recommended and alternate route and explain the trade-off before confirming.
  metric: representative route-selection acceptance journeys passing
  window: Evaluate before release and at seven days after exposure
  slices:
  - new_users
  - power_users
  guardrails:
  - power_user_time_to_confirm
  decision_rule: Ship if all critical journeys pass and median power-user confirmation time does not regress
    by more than ten percent.
  cases:
  - id: new-user-comparison
    description: New user opens route comparison and explains the recommendation.
    expected: pass
    slice: new_users
  - id: unavailable-route
    description: An unavailable route is presented without a reason or safe alternative.
    expected: fail
    slice: new_users
  - id: compact-power-user-path
    description: Power user confirms from the compact path without opening comparison.
    expected: pass
    slice: power_users
binding:
  status: executable
  provider: manual-eval
  case_set_reference: case-set-fixture-route-v2
  definition_version: route-cases-v2
  verified_by: product-ops
  verified_at: '2026-05-19T14:00:00Z'
  owner: product-ops
  measurement_anchor:
    type: manual
    reference: route-evaluation-fixture-v2
    occurred_at: '2026-05-19T15:00:00Z'
```

## Delivery

- linear `linear-project-route-fixture` — https://linear.example.invalid/project/route-fixture
- Implementation Plan (engineering-owned): `github.com/example/transaction-app/specs/route-comparison/implementation-plan.md`, based on PRD version `333333333333`

## Acceptance scenarios

The route recommendation is understandable, alternate routes are comparable, and experienced users retain a compact path.

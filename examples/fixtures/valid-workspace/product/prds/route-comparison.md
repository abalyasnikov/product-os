---
schema_version: 1
id: prd_01JABCDE01
type: prd
title: Comparable transaction routes
created_at: "2026-05-10T09:00:00Z"
updated_at: "2026-05-20T15:00:00Z"
authors: [product-lead]
relationships:
  opportunity: opportunity_01JABCDE01
  initiative: initiative_01JABCDE01
  signals: [signal_01JABCDE01, signal_01JABCDE03]
opportunity_id: opportunity_01JABCDE01
initiative_id: initiative_01JABCDE01
problem: Users cannot compare route cost, expected time, and failure risk before confirmation.
target_users: Funded users selecting a route, with a compact default for experienced users.
evidence_ids: [signal_01JABCDE01, signal_01JABCDE03, pattern_01JABCDE01]
current_journey: The user sees route names and cost but cannot inspect expected timing or the failure explanation before confirming.
desired_journey: The user sees a concise recommended route and can progressively reveal comparable cost, time, and reliability cues.
target_outcome: Eligible users select and confirm a route without an uncertainty-driven abandonment.
requirements: [Show one recommended route with cost and expected-time rationale, Allow comparison without leaving the transaction flow, Preserve a compact one-action path for experienced users]
non_goals: [Designing a new routing algorithm, Guaranteeing network settlement time, Engineering task decomposition]
outcome:
  definition:
    version: route-cases-v2
    method: acceptance_journey
    baseline: Users cannot compare time and reliability before confirmation.
    target: A user can compare the recommended and alternate route and explain the trade-off before confirming.
    metric: representative route-selection acceptance journeys passing
    window: Evaluate before release and at seven days after exposure
    slices: [new_users, power_users]
    guardrails: [power_user_time_to_confirm]
    decision_rule: Ship if all critical journeys pass and median power-user confirmation time does not regress by more than ten percent.
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
    verified_at: "2026-05-19T14:00:00Z"
    owner: product-ops
    measurement_anchor:
      type: manual
      reference: route-evaluation-fixture-v2
      occurred_at: "2026-05-19T15:00:00Z"
risks: [Reliability language may overstate provider certainty, Additional details may slow the expert path]
dependencies: [Route provider exposes comparable estimates]
gtm_hypothesis:
  status: applicable
  audience: Funded users evaluating their first route
  promise: Know why a route is recommended before confirming
  discovery_channel: Transaction route selector
  adoption_action: Open comparison and confirm a route
  launch_measurement: Route-selection completion and power-user confirmation time
implementation_refs:
  - repository: github.com/example/transaction-app
    path: specs/route-comparison/implementation-plan.md
    based_on_prd_id: prd_01JABCDE01
    based_on_prd_version: "3333333333333333333333333333333333333333"
    adr_references: [adr/0042-route-estimate-presentation.md]
delivery_refs:
  - provider: linear
    external_id: linear-project-route-fixture
    url: https://linear.example.invalid/project/route-fixture
    synced_from_version: "3333333333333333333333333333333333333333"
---

## Acceptance scenarios

The route recommendation is understandable, alternate routes are comparable, and experienced users retain a compact path.

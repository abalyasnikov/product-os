---
schema_version: 1
id: prd_01TRADX001
type: prd
title: Cross-chain Swap
created_at: "2025-02-12T09:00:00Z"
updated_at: "2025-02-20T15:00:00Z"
authors: [product-manager]
relationships:
  opportunity: opportunity_01TRADX001
  initiative: initiative_01TRADX001
  signals: [signal_01TRADX001]
  pattern: pattern_01TRADX001
opportunity_id: opportunity_01TRADX001
initiative_id: initiative_01TRADX001
problem: Users with a cross-chain trade intent must understand and execute bridge and swap steps as disconnected operations.
target_users: Eligible users swapping from an asset on one supported chain into an asset on another.
evidence_ids: [signal_01TRADX001, pattern_01TRADX001]
current_journey: The user separately chooses a bridge, waits, then discovers and executes a swap with no unified quote or progress context.
desired_journey: The user expresses one trade intent, sees the material route trade-offs, and follows one product journey across both execution stages.
target_outcome: Users complete a supported cross-chain swap without abandoning between bridge and swap stages.
requirements: [Present the full route before signature, Separate estimated provider cost from network cost, Preserve stage-level transaction references, Fail safely when a route becomes unavailable]
non_goals: [Guaranteeing settlement time, Building a proprietary bridge, Hiding provider or chain risk]
outcome:
  definition:
    version: cross-chain-swap-journeys-v1
    method: acceptance_journey
    baseline: "illustrative synthetic 3 of 8 journeys pass"
    target: "illustrative synthetic 8 of 8 critical journeys pass"
    metric: critical supported cross-chain swap journeys passing
    window: Before release and seven synthetic days after exposure
    slices: [same_wallet_destination, route_change, source_failure, destination_delay]
    guardrails: [unexpected_asset_received, unpriced_route_change]
    decision_rule: Ship only if all critical journeys pass and no safety guardrail fails.
    cases:
      - id: floor-supported-route
        description: A supported route completes with both stages and references visible.
        expected: pass
        slice: same_wallet_destination
      - id: ceiling-route-invalidates
        description: A provider route invalidates after quote and the flow continues without renewed consent.
        expected: fail
        slice: route_change
  binding:
    status: executable
    provider: manual-eval
    case_set_reference: case-set-synthetic-cross-chain-swap-v1
    definition_version: cross-chain-swap-journeys-v1
    verified_by: product-ops
    verified_at: "2025-02-19T14:00:00Z"
    owner: product-ops
risks: [Quote expiry could change the accepted trade, Unified presentation could hide multi-stage failure]
dependencies: [Route provider exposes both execution stages and estimates]
gtm_hypothesis:
  status: applicable
  audience: Existing users who already trade on more than one chain
  promise: Make one cross-chain trade without manually coordinating bridge and swap
  discovery_channel: Swap asset and network selectors
  adoption_action: Complete an eligible cross-chain swap
  launch_measurement: Illustrative critical-journey pass rate and eligible completion
implementation_refs:
  - repository: github.com/example/trading-wallet
    path: specs/cross-chain-swap/implementation-plan.md
    based_on_prd_id: prd_01TRADX001
    based_on_prd_version: "3333333333333333333333333333333333333333"
    adr_references: [docs/adr/route-state-machine.md]
delivery_refs:
  - provider: jira
    external_id: TRD-101
    url: https://jira.example.invalid/browse/TRD-101
    synced_from_version: "3333333333333333333333333333333333333333"
---

## Product boundary

The PRD defines the user journey and safety properties. Route selection algorithms and implementation decomposition belong in the code repository.

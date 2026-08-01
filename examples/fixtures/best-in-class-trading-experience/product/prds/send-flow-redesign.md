---
schema_version: 1
id: prd_01TRADX002
type: prd
title: Send Flow Redesign
created_at: "2025-02-12T10:00:00Z"
updated_at: "2025-02-21T15:00:00Z"
authors: [product-manager]
relationships:
  opportunity: opportunity_01TRADX001
  initiative: initiative_01TRADX001
  signals: [signal_01TRADX002]
  pattern: pattern_01TRADX002
opportunity_id: opportunity_01TRADX001
initiative_id: initiative_01TRADX001
problem: A generic send flow cannot safely assume that every destination address supports cross-chain delivery or an asset transformation.
target_users: Users sending to self-custody, another person, or an exchange deposit address.
evidence_ids: [signal_01TRADX002, pattern_01TRADX002]
current_journey: Network, asset, and destination decisions are disconnected, and the product cannot clearly distinguish safe routes from unsupported destination behavior.
desired_journey: The flow understands the user's destination and intent, explains material constraints, and fails closed when safe delivery cannot be established.
target_outcome: Users choose a supported send path without creating an avoidable destination mismatch.
requirements: [Classify destination context when reliable, Never infer CEX support from address validity alone, Show exact destination network and received asset before signature, Offer a plain transfer fallback when transformation safety is uncertain]
non_goals: [Universal exchange-deposit detection, Automatic bridging to every valid address, Guaranteeing recovery from an incorrect external deposit]
outcome:
  definition:
    version: send-safety-cases-v1
    method: case_based_eval
    baseline: "illustrative synthetic 5 of 12 safety cases pass"
    target: "illustrative synthetic 12 of 12 critical safety cases pass"
    metric: destination-aware send safety cases passing
    window: Before enabling each destination class
    slices: [self_custody, known_cex_deposit, unknown_destination, unsupported_network]
    guardrails: [unsafe_route_offered, destination_asset_mismatch]
    decision_rule: Do not ship a destination slice unless every critical case in that slice passes.
    cases:
      - id: floor-self-custody-same-network
        description: A same-network self-custody transfer shows the exact asset and destination network.
        expected: pass
        slice: self_custody
      - id: ceiling-unknown-cex-bridge
        description: An unknown deposit address is offered a bridge route without verified destination support.
        expected: fail
        slice: unknown_destination
  binding:
    status: executable
    provider: manual-eval
    case_set_reference: case-set-synthetic-send-safety-v1
    definition_version: send-safety-cases-v1
    verified_by: product-ops
    verified_at: "2025-02-20T14:00:00Z"
    owner: product-ops
risks: [Destination classification may be unavailable or stale, Additional warnings may reduce completion for safe transfers]
dependencies: [Destination policy can fail closed, Asset and network shown before signature]
gtm_hypothesis:
  status: applicable
  audience: Users sending assets to external addresses
  promise: Know exactly what will arrive and where before sending
  discovery_channel: Existing Send entry point
  adoption_action: Complete a supported destination-aware transfer
  launch_measurement: Synthetic send safety case coverage and completion by destination class
implementation_refs: []
delivery_refs:
  - provider: linear
    external_id: TRA-202
    url: https://linear.example.invalid/issue/TRA-202
    synced_from_version: "4444444444444444444444444444444444444444"
---

## Replaces

This PRD replaces the rejected generic **Cross-chain Send** solution. The critical learning was that bridging inside Send can be unsafe for CEX deposit destinations when the destination's supported network and asset cannot be verified.

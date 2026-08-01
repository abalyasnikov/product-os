---
schema_version: 1
id: initiative_01TRADX001
type: initiative
title: Best-in-class trading experience
created_at: "2025-02-11T09:00:00Z"
updated_at: "2025-05-30T12:00:00Z"
authors: [product-lead]
relationships:
  opportunity: opportunity_01TRADX001
  prds: [prd_01TRADX001, prd_01TRADX002, prd_01TRADX003, prd_01TRADX004, prd_01TRADX005, prd_01TRADX006]
  learning: learning_01TRADX001
opportunity_id: opportunity_01TRADX001
target_outcome: Eligible users complete a supported trade or send journey with fewer avoidable interruptions and can understand its state until settlement.
product_thesis: Six focused interventions can create one continuous trading experience while keeping destination safety, permission clarity, and transaction-state integrity explicit.
evidence_ids: [opportunity_01TRADX001, pattern_01TRADX001, pattern_01TRADX002, signal_01TRADX001, signal_01TRADX002, signal_01TRADX003, signal_01TRADX004, signal_01TRADX005, signal_01TRADX006]
business_impact: More users can reach the core value of moving assets confidently; no production or revenue forecast is asserted in this fixture.
gtm_hypothesis:
  status: applicable
  audience: Active wallet users trading or sending assets across supported chains
  promise: Trade and move assets across chains without losing context, control, or progress
  discovery_channel: Existing swap and send entry points plus in-product release education
  adoption_action: Complete an eligible trade or send and return to the wallet while settlement continues
  launch_measurement: Illustrative completion and comprehension measures, sliced by journey and chain class
outcome:
  definition:
    version: trading-initiative-metric-v1
    method: behavioral_metric
    baseline: "illustrative synthetic 42%"
    target: "illustrative synthetic 60%"
    metric: eligible sessions completing the intended trade or send journey without an avoidable product interruption
    window: 28 synthetic days after first eligible exposure
    slices: [cross_chain_swap, external_send, native_asset_trade, bridge_settlement, token_approval]
    guardrails: [destination_safety_incidents, failed_transaction_rate, signature_comprehension, support_contact_rate]
    decision_rule: Scale only if the illustrative aggregate reaches 60%, no required slice declines, and every safety guardrail remains within its synthetic threshold.
  binding:
    status: executable
    provider: amplitude
    query_reference: amp-synthetic-trading-initiative-v1
    metric_definition_reference: metric-synthetic-trading-completion-v1
    definition_version: trading-initiative-metric-v1
    verified_by: analytics-lead
    verified_at: "2025-04-30T10:00:00Z"
    owner: analytics-lead
    measurement_anchor:
      type: exposure_event
      reference: exposure-synthetic-trading-rollout-01
      occurred_at: "2025-05-01T09:00:00Z"
barriers: [Cross-chain swap is split into bridge and trade steps, Send intent lacks destination-aware safety, Native-asset trading repeats the same confirmation decision, Transaction status blocks continued wallet use, Bridge settlement progress is not persistent, Token approvals are hard to understand and manage]
child_prd_ids: [prd_01TRADX001, prd_01TRADX002, prd_01TRADX003, prd_01TRADX004, prd_01TRADX005, prd_01TRADX006]
dependencies: [Supported route providers expose safe estimates, Destination classification can fail closed, Transaction state events are observable, Analytics exposure event is versioned]
sequencing: [Ship safety-critical send behavior before expanding destination coverage, Make transaction status non-blocking before relying on persistent bridge progress, Measure the shared outcome only after all six child exposures are identifiable]
learnings: [learning_01TRADX001]
---

## Bet boundary

This Initiative owns the shared outcome. Each child PRD owns a narrower barrier and Outcome Contract.

## Rejected alternative

**Cross-chain Send** as a generic route-first experience was rejected during review. It could treat a CEX deposit address as a normal self-custody destination even when the destination cannot safely receive the routed result. The replacement is **Send Flow Redesign**, with destination classification and a fail-closed path. **Bridge Progress Tracking** is a separate child PRD because progress continuity remains necessary even when send routing is safe.

## Historical note

Delivery references preserve Jira- and Linear-style shapes as anonymized examples. They do not point to a real workspace.

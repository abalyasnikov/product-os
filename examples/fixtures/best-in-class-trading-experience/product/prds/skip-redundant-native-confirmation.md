---
schema_version: 1
id: prd_01TRADX003
type: prd
title: Skip Redundant Native Confirmation
created_at: "2025-02-13T09:00:00Z"
updated_at: "2025-02-22T15:00:00Z"
authors: [product-manager]
relationships:
  opportunity: opportunity_01TRADX001
  initiative: initiative_01TRADX001
  signals: [signal_01TRADX003]
  pattern: pattern_01TRADX001
opportunity_id: opportunity_01TRADX001
initiative_id: initiative_01TRADX001
problem: Native-asset trades repeat an application confirmation immediately before the authoritative wallet signature, despite requiring no approval transaction.
target_users: Returning users executing eligible native-asset trades after reviewing the quote.
evidence_ids: [signal_01TRADX003, pattern_01TRADX001]
current_journey: The user accepts a quote, confirms again in the application, and then confirms the same intent in the wallet signature surface.
desired_journey: Eligible users move from reviewed quote directly to the wallet signature, while materially changed quotes require renewed review.
target_outcome: Eligible native-asset traders reach the signature with one fewer redundant product action and unchanged comprehension.
requirements: [Apply only when no token approval is required, Require renewed review after a material quote change, Keep amount asset network recipient and minimum received visible at signature handoff, Preserve explicit cancellation]
non_goals: [Skipping wallet signatures, Removing confirmation for token approvals, Optimizing provider latency]
outcome:
  definition:
    version: native-confirmation-experiment-v1
    method: experiment
    baseline: "illustrative synthetic median 3 product actions"
    target: "illustrative synthetic median 2 product actions with no comprehension decline"
    metric: product actions from accepted quote to submitted transaction
    window: Fourteen synthetic days after exposure
    slices: [repeat_users, first_time_native_traders]
    guardrails: [signature_cancellation_rate, comprehension_check, quote_change_reconfirmation]
    decision_rule: Scale only if actions decline and no guardrail regresses beyond its illustrative threshold.
    hypothesis: Removing the duplicate application confirmation reduces friction without reducing informed consent.
    control: Quote review plus application confirmation plus wallet signature.
    treatment: Quote review followed directly by wallet signature for eligible native-asset trades.
    primary_metric: product actions from accepted quote to submitted transaction
  binding:
    status: executable
    provider: amplitude
    query_reference: amp-synthetic-native-confirmation-v1
    definition_version: native-confirmation-experiment-v1
    verified_by: analytics-lead
    verified_at: "2025-02-21T14:00:00Z"
    owner: analytics-lead
risks: [Users may interpret speed as reduced review, Quote changes may bypass renewed consent]
dependencies: [Eligibility and material quote changes are deterministic]
gtm_hypothesis:
  status: applicable
  audience: Repeat native-asset traders
  promise: Confirm the trade once in the surface that actually authorizes it
  discovery_channel: Native-asset trade flow
  adoption_action: Submit an eligible trade from the reviewed quote
  launch_measurement: Illustrative action count with comprehension and cancellation guardrails
implementation_refs: []
delivery_refs:
  - provider: jira
    external_id: TRD-103
    url: https://jira.example.invalid/browse/TRD-103
    synced_from_version: "5555555555555555555555555555555555555555"
---

## Safety boundary

This removes duplicated product ceremony, not the signature that authorizes the transaction.

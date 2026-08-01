---
schema_version: 1
id: prd_01TRADX006
type: prd
title: Token Approval Management
created_at: "2025-02-14T10:00:00Z"
updated_at: "2025-02-25T15:00:00Z"
authors: [product-manager]
relationships:
  opportunity: opportunity_01TRADX001
  initiative: initiative_01TRADX001
  signals: [signal_01TRADX005]
  pattern: pattern_01TRADX002
opportunity_id: opportunity_01TRADX001
initiative_id: initiative_01TRADX001
problem: Users cannot clearly distinguish token approval from trade execution or inspect and revoke the allowance after trading.
target_users: ERC-20 traders who must grant an allowance and users reviewing active token permissions.
evidence_ids: [signal_01TRADX005, pattern_01TRADX002]
current_journey: Approval appears as unexplained transaction overhead, and active allowances are difficult to find after the trade.
desired_journey: The product explains spender, asset, amount, and purpose before approval and provides a discoverable path to review and revoke active allowances.
target_outcome: Users understand the permission they grant and can later find an appropriate control for it.
requirements: [Separate approval and execution states, Identify spender asset and allowance scope, Prefer bounded allowance when supported, Make active allowances discoverable with revoke cost and consequence]
non_goals: [Claiming every approval is malicious, Free revocation, Replacing transaction simulation]
outcome:
  definition:
    version: approval-comprehension-v1
    method: case_based_eval
    baseline: "illustrative synthetic 4 of 10 comprehension cases pass"
    target: "illustrative synthetic at least 8 of 10 pass and all safety cases pass"
    metric: approval comprehension and control cases passing
    window: Before release and fourteen synthetic days after exposure
    slices: [first_approval, repeat_approval, unlimited_allowance, revoke]
    guardrails: [trade_failure_after_bounded_approval, misleading_spender_label]
    decision_rule: Scale when at least 80% pass overall, all safety-critical cases pass, and guardrails do not regress.
    cases:
      - id: floor-spender-purpose
        description: User can identify the spender and why approval is required.
        expected: pass
        slice: first_approval
      - id: ceiling-hidden-unlimited
        description: An unlimited allowance is granted without showing scope or a later revoke path.
        expected: fail
        slice: unlimited_allowance
  binding:
    status: executable
    provider: manual-eval
    case_set_reference: case-set-synthetic-token-approval-v1
    definition_version: approval-comprehension-v1
    verified_by: product-ops
    verified_at: "2025-02-24T14:00:00Z"
    owner: product-ops
risks: [Security language may create unnecessary alarm, Bounded allowances may add repeat approvals]
dependencies: [Spender metadata and current allowance are available or clearly unknown]
gtm_hypothesis:
  status: applicable
  audience: ERC-20 traders and security-conscious users
  promise: Understand and stay in control of token permissions
  discovery_channel: Trade approval step and wallet security controls
  adoption_action: Complete an informed approval or inspect an active allowance
  launch_measurement: Synthetic comprehension eval and revoke-control discovery
implementation_refs: []
delivery_refs:
  - provider: linear
    external_id: TRA-206
    url: https://linear.example.invalid/issue/TRA-206
    synced_from_version: "8888888888888888888888888888888888888888"
---

## Product boundary

The PRD makes permissions legible and manageable. It does not make an unverifiable security guarantee.

---
schema_version: 1
id: signal_01TRADX005
type: signal
title: Token approvals are invisible before and after trading
created_at: "2025-02-07T10:00:00Z"
updated_at: "2025-02-07T10:00:00Z"
authors: [product-research]
relationships:
  pattern: pattern_01TRADX002
  opportunity: opportunity_01TRADX001
summary: Synthetic support synthesis showed that users could not distinguish approval from trade execution or find a clear way to inspect and revoke an allowance later.
sources:
  - provider: pasted_note
    external_id: pasted-fixture-token-approval
    occurred_at: "2025-02-06T13:00:00Z"
    retrieved_at: "2025-02-07T09:40:00Z"
    content_fingerprint: sha256:synthetic-token-approval
    storage: reference_only
segments: [erc20_traders, security_conscious_users]
interpretation_confidence: medium
---

## Context

The fixture does not quantify approval-related loss. It frames comprehensibility and post-trade control as product barriers.

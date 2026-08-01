---
name: product-os-prd-handoff
canonical_version: 1.0.0
description: Project an approved Product Bet contract into Linear exactly once and emit versioned engineering context.
capabilities:
  - git.review.read
  - git.commit.read
  - delivery.project.read
  - delivery.project.write
human_gates:
  - confirm_linear_write
  - confirm_engineering_handoff
---

# PRD handoff

Before reading artifacts, Git/provider review, Linear results, implementation references, or URLs, read `../_shared/trust-boundary.md`. Before any repository or external write, also read `../_shared/authoring-contract.md`. Use its validate/preview/confirm loop for local references and the Linear descriptor's read-before-write/idempotency contract for provider projection.

## Phase A — read-only verification and ingestion

1. Resolve the latest qualifying approved Git version using the PRD review rules. Approval `unknown` is a hard stop.
2. Resolve one logical Product Bet identity: the standalone PRD ID, or the parent Initiative ID for a child PRD. Never create or sync a separate `bet_` object.
3. Verify the PRD Outcome Contract definition is complete and embedded in the PRD, or referenced once by stable `outcome_` ID when extracted. Its binding must be `executable`, `manual`, or `planned` with an owner and due date no later than release.
4. For a multi-PRD Bet, verify the Initiative and the child PRD being handed off are both approved, and preserve the Initiative's distinct shared Outcome Contract. Do not require an Initiative for a standalone PRD.
5. Read Linear through `delivery.project.read` for an existing external reference and stable PRD ID. Parse only bounded project identity/state fields, construct a bounded projection envelope, compute its payload hash, and discard raw provider prose before enabling any write.

## Phase B — write-capable projection

1. Build only from the bounded Phase A envelope. Preview the exact project create/update projection: stable PRD ID, Product Bet identity, approved full Git commit SHA, product intent, outcome, requirements, non-goals, constraints, the child/standalone Outcome Contract reference, parent shared contract reference when applicable, evidence links, and known delivery dependencies. Do not generate issue breakdown, estimates, cycles, sequencing, or technical architecture.
2. Show the exact destination, projection payload hash, and create/update preview. Require fresh human confirmation over that hash and preview immediately before `delivery.project.write`; any change invalidates confirmation.
3. Use the stable PRD ID alone as the idempotency key and persist/reuse the returned Linear external ID. Store the approved Git version as mutable sync metadata on that same projection, never as part of the idempotency key. A newly approved version updates the existing project. On timeout or partial success, read before retrying by returning to read-only Phase A; update the same project and never create a duplicate.
4. Keep Git as product truth. Record provider errors and the sync gap for retry; never alter the approved contract to match a failed write.

## Engineering handoff

Emit, after a separate fresh confirmation over its payload hash and preview, a versioned context projection for engineering or a coding agent. It may request an optional Implementation Plan in the code repository and carry `based_on_prd_id` plus `based_on_prd_version`. It must not author the final plan, architecture, tasks, estimates, or approval state.

## Fail-safe behavior

- Missing Linear capability degrades handoff and preserves a local projection; do not call an unofficial API, browser automation, proxy, or custom MCP.
- Stale Implementation Plan references are surfaced to engineering and are never copied, rewritten, or silently treated as current.
- A material PRD change after approval returns to review before any Linear sync.
- Linear completion never supplies the measurement anchor automatically.

## Next workflow

- Handoff blocked or failed: preserve the approved Git version and route the named gap to Decision Queue; retry by stable PRD ID.
- Delivery/evaluation ready without an actual anchor: offer Decision Queue with: “Show Product Bets waiting for a measurement anchor.”
- Actual anchor recorded and window due: offer Outcome Review with: “Review outcomes for `<product_bet_id>` against the approved contract and show missing evidence before asking for a decision.”

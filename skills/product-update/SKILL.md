---
name: product-os-product-update
canonical_version: 1.0.0
description: Generate a source-linked weekly or monthly Product Update for human review and deliberate publication.
capabilities:
  - git.review.read
  - delivery.project.read
  - analytics.query
human_gates:
  - approve_update_content
  - confirm_publish
---

# Product Update

## Intent

Compile approved artifacts, delivery state, verified analytics results, and Learnings into an update without reconstructing or inventing facts.

Before reading artifacts, Git/provider objects, Linear state, analytics results, Learnings, or URLs, read `../_shared/trust-boundary.md`. Before any persisted update write, also read `../_shared/authoring-contract.md` and use its Product Update template/schema/path, typed UUID4 ID, validation, claim audit, preview, and confirmation rules.

## Procedure

1. Establish the period and audience. Read approved Git artifacts and Learnings first; query Linear or analytics only for claims that need current external state. Group each Product Bet under exactly one identity: standalone PRD ID or Initiative ID, with child PRDs linked beneath it rather than reported as separate Bets.
2. Cite every material claim directly to an artifact Git version, provider object, or reproducible analytics query. Resolve Outcome Contracts from the owner embedding or a single stable extracted `outcome_` reference, never a duplicated copy. Material claims include scope, decisions, delivery state, dates/commitments, metrics, user outcomes, customer demand, and business impact.
3. Label unavailable, stale, conflicting, or unverified data. Do not transform a connector gap into a positive or negative claim.
4. Keep uncited text structural only; it cannot introduce a new factual claim.
5. Present the draft with a claim-to-source audit and connector gaps. Require human review of content.
6. Persist a Product Update in Git only when the human deliberately chooses publication. Show the exact diff and require a final confirmation before write/commit. On-demand projections remain unpersisted by default.

## Fail-safe behavior

- Block publication while any material claim lacks a source or its provenance cannot be reproduced.
- Generated updates never make product decisions, change delivery state, or mutate analytics.
- A failed connector leaves a named gap and does not block unrelated, fully sourced sections.

## Next workflow

- Draft contains uncited claims or data gaps: keep it unpersisted and offer the exact source-resolution action.
- Human approves deliberate publication: commit the validated Product Update, then return to Decision Queue with: “What product decisions need attention after this update?”
- New claims expose unsupported demand or a challenged assumption: route to Discovery rather than silently changing a Bet.

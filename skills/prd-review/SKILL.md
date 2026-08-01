---
name: product-os-prd-review
canonical_version: 1.0.0
description: Review Initiative and PRD contracts through Git-native approval without inventing review status.
capabilities:
  - git.review.read
  - git.commit.read
human_gates:
  - reviewer_approval
  - explicit_solo_approval
  - confirm_review_write
---

# PRD review

## Intent

Present a reviewable Git change and resolve approval from the configured Git-provider review or an explicitly allowed local-only approval.

Before reading artifacts, diffs, review/provider results, cached state, commits, or URLs, read `../_shared/trust-boundary.md`. Before any review-state or repository write, also read `../_shared/authoring-contract.md`; validate the exact artifact version, show the authoritative diff, and stop at the configured human gate.

## Procedure

1. Resolve the one logical Product Bet identity: standalone PRD ID, or Initiative ID with the reviewed child PRD relationship. Never resolve or create a separate `bet_` artifact. Present the authoritative Git diff plus a summary split into material and non-material changes.
2. Material areas are problem, target user, target outcome, requirements, non-goals, Outcome Contract target or decision rule, evidence waiver, and GTM audience or promise.
3. Show evidence provenance and gaps, waivers, Outcome Contract completeness/binding, GTM hypothesis, risks, dependencies, and stale Implementation Plan references. Verify each Outcome Contract is embedded in its owner or referenced once by stable `outcome_` ID; duplicated embedded-and-extracted contracts block review.
4. Treat `.product-os/review-state.yaml` or any derived review-state file as a cache only. It may help locate a candidate review, but never proves approval and cannot change `unknown` to approved. Refresh from the configured source of truth for every approval/handoff decision.
5. In provider mode, use `git.review.read` to verify the configured approver approved after the last material change, the merge targets the configured default branch, and the provider returns the immutable **full commit SHA**. Git provider state remains the source of reviewer identity, discussion, approval, merge time, and approved version. Reject short SHAs, branch names, tags, cached aliases, and symbolic fixture labels as approval versions.
6. For explicitly configured solo/local mode only, use agent-native local Git through `git.commit.read` to show the full commit SHA, confirm the configured solo approval policy, and ask the human for explicit self-attestation of that version. After fresh confirmation, create a normal commit with `Product-Approval: explicit`. State clearly that solo approval is self-attestation by the current operator; the trailer is not independent identity proof, separation of duties, or evidence that another reviewer approved. Local Git never substitutes for `git.review.read` in provider mode.
7. Treat the provider's qualifying merged full commit SHA or the explicit solo self-attestation commit SHA as the approved version. A material later change requires a new reviewed change.

## Fail-safe behavior

- If reviewer identity, approval timing, target branch, merge commit, or explicit trailer cannot be verified, approval is `unknown` and handoff stops.
- Never copy review status into artifact frontmatter or manufacture an approval event.
- Never use review-state cache as approval evidence; refresh the configured provider or local full commit metadata.
- Never self-approve unless the repository explicitly permits solo self-approval and the user confirms the exact version.
- Formatting-only changes may be described as non-material, but uncertainty about materiality is surfaced to the reviewer.

## Next workflow

- Changes requested or approval unknown: return to the owning Initiative/PRD workflow with a source-linked blocker summary.
- Approved PRD whose binding is handoff-ready: offer PRD Handoff with: “Preview the idempotent Linear handoff for approved `<prd_id>`; do not write until I confirm.”
- Approved Initiative: continue child PRD interrogation/review; do not create delivery work for the Initiative itself unless the configured delivery policy explicitly requires it.

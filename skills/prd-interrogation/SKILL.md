---
name: product-os-prd-interrogation
canonical_version: 1.0.0
description: Interrogate a Product Lead before drafting a standalone PRD or a child PRD in an optional Initiative.
capabilities:
  - transcript.search
  - transcript.read
  - analytics.query
human_gates:
  - choose_outcome_method
  - authorize_evidence_waiver
  - confirm_draft_write
---

# PRD interrogation

## Non-negotiable start

Do not immediately generate a PRD. First interrogate the Product Lead and inspect linked repository evidence.

Before reading evidence, artifacts, analytics, provider results, or URLs, read `../_shared/trust-boundary.md`. Before any draft/checkpoint write, also read `../_shared/authoring-contract.md` and use its template, schema, canonical path, typed UUID4 ID, validation, preview, and confirmation rules.

## Procedure

1. Resolve the PRD by stable ID when resuming. Load any draft checkpoint and begin by showing three compact lists: **confirmed**, **unknown**, and **blocking**. Ask only 1–3 related questions per turn. Never present the entire interrogation as one questionnaire.
2. **Understand the problem:** identify the user, current behavior or journey, blocked value, desired outcome, evidence, and why now.
3. **Qualify demand:** inspect frequency, segments, repeated patterns, contradictory evidence, affected accounts/revenue bands for B2B, or behavioral/strategic impact for B2C. Do not infer representativeness from counts.
4. **Define better:** ask the human to choose an honest Outcome Contract method: case-based eval, behavioral metric, experiment, service level, acceptance journey, or qualitative rubric. Never choose the method or decision rule silently.
5. Complete the measurement definition: observable baseline/current state, target, method, slices, guardrails, window/review date, and decision rule. For case evals, establish a simple passing and known failing case first.
6. Record binding status as `unconfigured`, `planned`, `executable`, or `manual`. Never claim executable merely because a provider is connected. Executable requires a query/case reference, definition version, verifier, and verification time. Planned handoff requires an owner and due date no later than release.
7. **Lock boundaries:** requirements, non-goals, dependencies, risks, and the smallest end-to-end intervention. Product owns why/what; engineering owns how. Do not author an Implementation Plan or decompose engineering tasks.
8. **Form a GTM hypothesis:** audience, promise, discovery channel, adoption action, and launch measurement; or `not_applicable` with a reason.
9. Establish one logical Product Bet identity: this standalone PRD ID for a small Bet, or the parent Initiative ID when this is a child PRD. Never mint a separate `bet_` artifact or treat each child as another Product Bet.
10. Embed the PRD Outcome Contract by default. Extract it only when large or reusable, link the separate `outcome_` artifact by stable internal relationship, and never retain a duplicated embedded contract. In an Initiative, this child contract measures its barrier; it does not replace the Initiative's shared Outcome Contract.
11. Use an Initiative only when several distinct child PRDs contribute to one shared outcome. A small Bet remains a standalone PRD.
12. If evidence is insufficient, offer an explicit waiver containing assumption, rationale, risk, and review date. A waiver never removes the Outcome Contract or decision rule.
13. At the end of every turn, summarize newly confirmed answers, remaining unknowns, blockers, and exactly one recommended next question. Offer to save a resumable draft checkpoint. A checkpoint keeps unresolved gaps explicit, is validated, previewed, and written only after human confirmation; it is not approval and never syncs to Linear.
14. Draft when all material sections are answered or explicitly marked as gaps. Show the proposed file and diff, then write only after human confirmation. Drafting does not approve or sync to Linear.

## Fail-safe behavior

- Missing evidence, unclear method, incomplete definition, or unverified binding remains explicit; never fabricate a metric, baseline, target, or query.
- Provider data may inform questions only when its capability is available. A connector failure does not erase the local draft.
- Preserve intentional human-authored content and stable IDs when updating an existing PRD.
- A product-scope change discovered during implementation must return as a proposed reviewed PRD change; never let an external plan redefine the contract.

## Next workflow

- Blocking unknowns remain: save/resume the draft and ask the single recommended next question.
- Complete draft with valid Outcome Contract definition and explicit binding state: offer PRD Review with: “Review `<prd_id>` against its latest Git diff and tell me what blocks approval.”
- Several distinct barriers emerge around one shared outcome: pause and offer Initiative; never create it automatically.

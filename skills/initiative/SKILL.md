---
name: product-os-initiative
canonical_version: 1.0.0
description: Create or update the optional Initiative that represents one multi-PRD Product Bet and its shared outcome.
capabilities:
  - transcript.search
  - transcript.read
  - analytics.query
  - git.review.read
  - git.commit.read
human_gates:
  - confirm_initiative_structure
  - choose_shared_outcome_method
  - reviewer_approval
  - confirm_initiative_write
---

# Initiative

## When to use it

Create an Initiative only when several distinct barriers and child PRDs must contribute to one shared user outcome. The Initiative ID is the single logical Product Bet identity. A small Product Bet uses its standalone PRD ID and must not be forced through an empty Initiative.

Before reading evidence, artifacts, analytics, or URLs, read `../_shared/trust-boundary.md`. Before any repository write, also read `../_shared/authoring-contract.md` and use its Initiative template/schema/path, typed UUID4 ID, validation, preview, and confirmation rules.

## Create or update

1. Resolve a pursued Opportunity and existing artifacts by stable ID. For an update, preserve intentional human-authored content, the Initiative ID, child PRD IDs, decision events, and approved history.
2. Interrogate the Product Lead for the shared product thesis, target users and outcome, initiative-level evidence and business impact, GTM hypothesis, distinct barriers, dependencies, sequencing constraints, and accumulated Learnings.
3. Map one coherent barrier to each child PRD. Keep child relationships bidirectional and stable. Do not duplicate child requirements in the Initiative or create placeholder PRDs merely to fill a hierarchy.
4. Embed the shared Outcome Contract in the Initiative by default. Extract it only when a large/reusable contract needs its own stable `outcome_` artifact; then store a stable internal relationship and never duplicate the contract body.
5. Define the shared contract's baseline/current state, target, method, slices, guardrails, window, decision rule, binding, and actual anchor rules. Each child PRD owns a separate embedded Outcome Contract for whether that intervention removes its barrier.
6. Make the measurement boundary explicit: child results measure barrier removal; the Initiative result measures the shared user outcome. Passing all child contracts never automatically proves the Initiative contract. Outcome Review must evaluate both levels when both exist.
7. Accumulate source-linked Learnings without rewriting their observations or decisions. State how each Learning strengthens, weakens, or leaves the shared thesis unresolved, and propose reviewed changes rather than mutating approved assumptions automatically.
8. Present the proposed Initiative, child graph, shared-versus-child measurement map, evidence gaps, and Git diff. Write only after explicit human confirmation.
9. Send the Initiative and embedded shared Outcome Contract through the configured PRD review path. The configured reviewer must approve the exact Git version after the last material change; approval `unknown` stops child handoff.

## Fail-safe behavior

- Never create a second Product Bet identity, a `bet_` artifact, or multiple Initiative IDs for one shared investment decision.
- Never infer that several related PRDs share one outcome; ask the human to confirm the thesis, barriers, and boundary.
- Missing child links, contradictory evidence, incomplete shared measurement, or an unavailable connector remains an explicit gap.
- Do not auto-approve an Initiative, auto-decide from accumulated Learning, or sync child PRDs before their own review gates pass.

## Next workflow

- Boundary incomplete: keep the resumable Initiative draft and ask the next blocking question.
- Initiative draft complete but unapproved: offer PRD Review with: “Review Initiative `<initiative_id>` and its shared Outcome Contract against the latest Git diff.”
- Approved Initiative with an uncontracted barrier: offer PRD Interrogation with: “Interrogate me for the child PRD covering `<barrier>`, 1–3 questions at a time.”
- No genuine multi-PRD shared outcome: return to a standalone PRD; do not preserve an empty Initiative.

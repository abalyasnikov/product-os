# Verification model

Product OS separates deterministic repository proof from live provider proof.
Passing a fixture never implies that an external account, mutation, or model judgment was
verified.

## Deterministic end-to-end proof

Run from a provenance-verified source checkout:

```bash
uv run --directory <checkout> python scripts/run_reference_journey.py --client codex
uv run --directory <checkout> python scripts/run_reference_journey.py --client claude-code
```

CI executes the same journey for Codex, Claude Code, and OpenClaw. Each run starts with an
empty directory and proves:

1. release-manifest verification;
2. preview-first installation with a confirmed plan hash;
3. active skill projection for the selected client;
4. a real Git commit containing pre-authored normalized evidence and an undecided Opportunity;
5. a second commit containing the human-owned `pursue` event bound to the first commit;
6. an Initiative with four child PRDs and synthetic review records bound to reachable commits;
7. delivery and optional Implementation Plan references bound to the same reachable approval version;
8. an explicit measurement anchor and synthetic analytics result;
9. pre-authored Outcome Review, Learning decision, and sourced Product Update artifacts materialized through real version boundaries;
10. a final `product-os check` pass.

For every decision or implementation handoff, the validator checks more than SHA
reachability: the referenced commit must contain the exact artifact. Solo review additionally
requires the configured approval trailer in that commit; a review-state cache cannot invent it.

The technical fixture uses synthetic measurement where source history contains no trustworthy
result. That is deliberate: it tests the operating contract without inventing Zerion production
facts.

The human-readable historical example is held to the opposite rule: it contains no fabricated
result at all. One barrier, Auto-slippage, carries a real baseline and a real observed outcome
because those figures were recovered from the original analysis. Its guardrail results were
not, which is why its recorded decision is `iterate` rather than `scale` — the contract's own
decision rule cannot be satisfied on incomplete evidence, and the example is more useful
showing that than hiding it. Every other measure in the example remains explicitly proposed.
The runner does not judge source material, execute agent skills, interrogate a PM, or generate
the artifacts; those behaviors require an agent-quality eval and are not inferred from this
deterministic journey.

## Executable acceptance matrix

The automated suite must prove:

- the compact valid workspace and the explicit evidence-waiver workspace pass;
- invalid fixtures fail for duplicate IDs, broken or mistyped references, oversized excerpts,
  transcript-sized or credential-like content, stale adapters, stale outcome definitions,
  stale implementation references, missing measurement anchors, unverified executable
  bindings, and incomplete evidence waivers;
- decision events remain append-only against their Git baseline;
- installation is preview-first, refuses overwrites and symlink escapes, and preserves exact
  release provenance;
- adapter generation is deterministic and idempotent for Codex, Claude Code, and OpenClaw;
- handoff retries preserve external idempotency keys rather than creating duplicate objects;
- no fixture contains production customer data, credentials, or an unlabeled synthetic result.

### Where this coverage stops

The validator defines around 120 distinct failure codes, and roughly half are not asserted by
name in any test. Most of those sit in the installation and adapter-integrity layer, which the
clean-install reference journeys exercise indirectly: the journeys pass because those checks
stay silent, not because a test proved each one fires when it should.

This is stated rather than quietly carried, because it bounds what a passing suite means. The
checks that carry the product's central claim — decision events append-only, decisions bound to
a reachable commit that contains the artifact, decision IDs unique, an Outcome Contract holding
both a definition and a binding — are asserted directly. Confidence beyond that group rests on
the journeys, not on individual assertions.

Writing those assertions found a real gap: deleting every artifact left the product tree empty,
and the append-only comparison was skipped for empty trees, so erasing the entire decision
history raised no error. The comparison now runs regardless. Untested checks are not evidence
of absent bugs.

Run the full matrix with:

```bash
python -m pytest
```

The fixture suite proves repository behavior only. Live MCP authorization, provider mutations,
analytics execution, human identity, and model output quality remain separate checks below.

## PRD output-quality contract

`evals/` contains four versioned golden cases for B2C UX, B2B ARR-weighted demand,
evidence waiver, and multi-PRD Initiative routing. The executable layer checks required
sections, the compact `Why now / business reality` statement, evidence traceability,
unsupported numeric claims, a separate Open questions section, Outcome Contracts, waiver
completeness, Initiative/child links, and the boundary between product decisions and an
engineering-owned Implementation Plan.

Run it with:

```bash
python evals/check_prd_quality.py
python -m pytest tests/evals
```

This is a deterministic contract over pre-authored artifacts, not an LLM eval. It does not
prove interrogation quality, problem selection, semantic correctness, or writing quality.
The adjacent model rubric is explicitly uncalibrated and requires a fixed external runtime,
blinded generation, retained judge evidence, and human adjudication before any score can be
used as a release claim.

## Live provider proof

Live verification is environment-specific and requires the user's configured provider MCPs.
It must be reported capability by capability:

| Capability | Passing condition |
|---|---|
| Granola retrieval | The agent can search and read a user-approved meeting without exporting the full transcript into Git. |
| Delivery handoff (Linear in reference V1) | A previewed create/update uses the PRD stable ID as its idempotency key and a retry reuses the same object. |
| Analytics measurement | The configured query runs against the declared definition version and returns provenance plus slice and guardrail results. |
| Git review | The provider review or explicit solo commit is verifiable at a reachable immutable commit, including provider identity rather than fixture metadata. |
| Agent quality | A separately versioned case set evaluates evidence fidelity, interrogation quality, PRD completeness, and unsupported-claim rate. |

Unavailable capabilities must be named as degraded. They may save drafts but cannot fabricate
provider output or cross the dependent human gate.

## Claim language

- Say **“deterministic reference journey passed”** after the automated runner succeeds.
- Say **“live provider flow passed”** only for capabilities actually exercised in that environment.
- Say **“full production loop verified”** only when all configured provider checks and the agent-quality eval pass together.

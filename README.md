# Product Decision OS

**Product decision infrastructure for agentic teams.**

Product Decision OS helps Product Leads and PMs turn customer evidence into approved product bets, delivery context, and measured learning without introducing another product-management UI.

[![Status: V1 reference implementation](https://img.shields.io/badge/status-V1_reference_implementation-2563eb)](docs/spec/product-decision-os.md)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-0f766e)](LICENSE)

[![Product Decision OS loop](docs/assets/product-loop.png)](docs/assets/product-loop.png)

## Why this exists

Spec-driven tools usually begin with an idea or feature request. They rarely preserve where the problem came from, whether the evidence is representative, or what happened after release. Product Decision OS keeps the complete decision chain inspectable:

```text
evidence → opportunity → product bet → PRD → delivery → measurement → learning
```

The primary interface is an agent such as Codex, Claude Code, or OpenClaw. Git stores the product truth. Existing MCP providers connect transcripts, delivery, and analytics.

## What it owns

- Traceable Signals, Opportunities, optional Initiatives, PRDs, Outcome Contracts, and Learnings.
- Human review and immutable product decisions.
- PRD interrogation that asks questions before drafting.
- Outcome definitions and evals before delivery.
- Context projections for Linear, engineering agents, leaders, and team updates.
- A computed Decision Queue for judgments that need human attention.

It does not replace Linear, analytics tools, transcript providers, code repositories, or engineering planning. It ships no custom MCP server and no additional UI.

## Repository map

```text
schemas/                 Validated artifact contracts
templates/               Human-readable Markdown templates
skills/                  Canonical agent-neutral workflows
adapters/                Generated client instructions and metadata
integrations/            Capability mappings for existing provider MCPs
src/product_decision_os/ Deterministic validation CLI
examples/                Human-readable worked product documents
docs/spec/               Normative product specification
docs/architecture/       Durable implementation decisions
tests/fixtures/           Reproducible technical and failure journeys
tests/                    Validator, skill, and end-to-end coverage
```

## Try the reference implementation

Requirements: Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
product-os validate tests/fixtures/valid-workspace
product-os smoke-test tests/fixtures/valid-workspace
python -m pytest
```

All smoke tests are read-only. They do not create Linear projects or mutate analytics data.

To prove the complete repository-controlled path in a brand-new Git workspace, run:

```bash
python scripts/run_reference_journey.py --client codex
```

The runner verifies the release manifest, binds apply to the exact saved install-plan hash,
creates real Git commits for evidence and synthetic decision boundaries, materializes a
four-PRD Product Bet, records delivery and synthetic measurement evidence, then validates the
final Learning and Product Update. The same journey runs in CI for Codex, Claude Code, and
OpenClaw.

The Python package contains the deterministic validator only. Canonical schemas, templates, skills, adapters, and integration mappings are installed from an immutable Git release so their provenance remains inspectable; a Python wheel is not a substitute for the Product Decision OS distribution.

## Install with an agent

For local development, send your agent the absolute path to [INSTALL.md](INSTALL.md) and explicitly confirm the local repository path and commit. After the first public release, use the commit-pinned public URL published in the release notes. Do not use a branch or mutable tag URL.

The agent will:

1. show the source commit and files it plans to install;
2. ask for a private target repository;
3. install the canonical schemas, templates, skills, and client adapter;
4. configure only the provider MCPs you choose;
5. run read-only smoke tests;
6. show the proposed Git commit before writing it.

The public one-link flow is intentionally unavailable while `manifest.json` reports `canonical_origin: unpublished`; this prevents a mutable or invented URL from becoming trusted installation guidance.

## Start with a product question

After setup, talk to the agent naturally:

```text
Find the Granola calls about failed first swaps, show contradictory evidence,
and help me decide whether this deserves a Product Bet.
```

```text
Interrogate me before drafting the PRD. Do not hand off to Linear until the
Outcome Contract is complete and the configured reviewer has approved it.
```

```text
What product decisions need my attention, and what evidence changed since
the last approved version?
```

No Granola connection is required for the first loop:

```text
Use this pasted note as local evidence. Preserve only a fingerprint and normalized
Signal, show me the exact Git payload, then help me decide whether to pursue it.
```

Additional workflows:

```text
This outcome has two independent barriers. Help me decide whether it needs an
Initiative, then define the shared Outcome Contract before drafting child PRDs.
```

```text
The rollout is exposed. Run Outcome Review from the configured measurement anchor,
show results by slice and guardrail, and ask me for the next decision.
```

```text
Prepare this month's Product Update. Block any material claim that lacks a structured
artifact, Linear, or analytics source reference.
```

See the [five-minute solo walkthrough](docs/getting-started.md) for the complete first loop and recovery paths.

## Worked example: Best-in-class trading experience

The [worked historical example](examples/best-in-class-trading-experience/README.md)
shows how one broad outcome becomes four problem-specific PRDs without turning the PRD into
an implementation document. These are normal, readable product documents derived from real
Zerion work—not a tutorial or serialized test dataset:

```text
Initiative: Best-in-class trading experience
  → Cross-chain Swap
  → Skip Signing Screen for Native Transactions
  → Transaction Toasters
  → Bridge Progress Tracking
```

The product problems, evidence limits, JTBDs, journeys, requirements, decisions, risks, and
open questions are real. Personal names, private workspace links, and unsupported outcome
claims are omitted. Proposed metrics remain visibly proposed when no verified baseline or
post-release result existed.

Deterministic tests use a separate machine fixture under `tests/fixtures/reference-journey`.
That fixture proves repository mechanics; the worked example demonstrates product-document
quality. Neither is presented as proof of Zerion production performance.

## What the tests prove

| Boundary | Automated proof |
|---|---|
| Release provenance and deterministic installation | Yes |
| Clean install for Codex, Claude Code, and OpenClaw | Yes |
| Signal-to-Learning artifact graph and Git decision history | Yes |
| Schema, relationship, review-state, adapter, and manifest integrity | Yes |
| Live Granola authorization and transcript retrieval | No — requires a configured provider account |
| Live Linear/Jira writes and analytics queries | No — smoke tests are deliberately read-only |
| LLM judgment quality across model providers | No — requires a separate eval suite |

The repository never turns a fixture pass into a claim that a live provider workflow was
verified. See the [verification model](docs/verification.md) for the exact boundary. The runner materializes pre-authored artifacts; it does not
prove agent interrogation, source interpretation, or document-generation quality.

## Product model

- **Signal:** one decision-relevant observation with source provenance.
- **Opportunity:** a problem worth an explicit pursue, hold, or reject decision.
- **Product Bet:** the logical investment and learning unit, not another file. A small Bet uses its PRD ID; a multi-PRD Bet uses its Initiative ID.
- **Initiative:** optional grouping for one outcome that requires multiple PRDs.
- **PRD:** the approved product contract for one coherent problem or barrier.
- **Implementation Plan:** optional engineering-owned plan stored in a code repository and linked by PRD version.
- **Outcome Contract:** what better means, how it will be observed, and which result triggers which decision.
- **Learning:** the observed result and human `scale`, `iterate`, `hold`, `kill`, or `complete` decision.

Read the [full product specification](docs/spec/product-decision-os.md) for lifecycle, evidence, privacy, review, measurement, and integration rules.

## Project status

This repository is a V1 reference implementation. The release bar is an inspectable evidence-to-learning journey, not feature count. See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for current acceptance criteria.

## License

Apache License 2.0. See [LICENSE](LICENSE).

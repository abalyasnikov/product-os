# Product OS

**Product decision infrastructure for agentic teams.**

Product OS helps Product Leads and PMs turn customer evidence into product bets, readable PRDs, delivery context, and measured learning—without adding another product-management UI.

[![Status: V1 reference implementation](https://img.shields.io/badge/status-V1_reference_implementation-2563eb)](docs/spec/product-decision-os.md)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-0f766e)](LICENSE)

[![Product OS loop](docs/assets/product-loop.png)](docs/assets/product-loop.png)

## Who it is for

Product Leads and PMs in software teams where:

- AI coding agents have made implementation faster;
- customer interviews, meeting notes, analytics, and delivery context live in different tools;
- the constraint has moved from writing documents to making sound, traceable product decisions;
- engineering, leadership, and agents need the same product intent without repeated handoffs.

The agent is the interface. Git stores the product artifacts and decision trail. Granola, Linear, Amplitude, Mixpanel, Metabase, and other existing providers keep owning their source data.

## The jobs it does

1. **Find where user value is blocked.** Turn interviews and notes into inspectable evidence without losing provenance, contradictions, segment coverage, or business weight.
2. **Decide what deserves investment.** Make the pursue, hold, or reject decision explicit before a feature request silently becomes a commitment.
3. **Create a product contract.** Interrogate the PM until the problem, journey, scope, Outcome Contract, risks, and GTM hypothesis are clear enough to review.
4. **Carry intent into delivery.** Give Linear, engineering, and coding agents the approved context—not only a ticket title.
5. **Learn after release.** Compare actual behavior with the baseline and decision rule, then record whether to scale, iterate, hold, kill, or complete the bet.
6. **Communicate without reconstruction.** Produce team and leadership updates from linked decisions, delivery state, and measured outcomes.

## Why it is different

Most spec-driven systems begin with an idea or feature request. Product OS begins earlier: where the problem came from, how representative the evidence is, and why the team chose to act.

Most delivery systems end at implementation, merge, or release. Product OS continues until the team observes the user outcome and updates its product thesis.

The goal is not more documents. The goal is more completed **evidence-backed learning loops**.

## The product loop

```text
evidence
  → opportunity
  → product bet
  → PRD + Outcome Contract
  → delivery
  → measurement
  → learning and next decision
```

A small Product Bet is represented by one PRD. When one outcome requires several independent interventions, an optional Initiative groups the child PRDs and owns the shared Outcome Contract. Product Bet is a decision and learning unit, not another mandatory file.

Three judgments remain human-owned:

- pursue, hold, or reject an Opportunity;
- approve the Product Bet contract before delivery handoff;
- scale, iterate, hold, kill, or complete after Outcome Review.

Agents can investigate, question, draft, link, measure, and recommend between those decisions.

## Worked example: Best-in-class trading experience

The [historical Zerion example](examples/best-in-class-trading-experience/README.md) shows one Initiative decomposed into four focused, readable PRDs:

```text
Initiative: Best-in-class trading experience
  → Cross-chain Swap
  → Skip Signing Screen for Native Transactions
  → Transaction Toasters
  → Bridge Progress Tracking
```

The documents preserve real problems, evidence limits, JTBDs, journeys, requirements, decisions, risks, and proposed measures. Personal names, private workspace links, and unsupported post-release claims are omitted. Where the original work lacked a verified baseline or outcome, the gap stays visible instead of being filled with synthetic certainty.

Start with the [Initiative](examples/best-in-class-trading-experience/product/initiatives/best-in-class-trading-experience.md), then open any child PRD to see how product reasoning remains readable while the Outcome Contract stays machine-checkable.

## What a PRD contains

A Product OS PRD is a concise product contract, not an implementation specification. It keeps the reasoning needed to review the bet and preserve intent through delivery:

- the **problem**, why it matters now, and the business reality;
- **evidence and confidence**, including gaps and contradictions;
- the **JTBD** and current → desired user journey;
- **requirements and non-goals**;
- an **Outcome Contract** defining what better means, how it will be observed, and what decision follows each result;
- the **GTM hypothesis** considered while shaping the product;
- **risks, open questions, and references**;
- links to the configured delivery system (Linear in the reference V1).

When implementation design needs durable detail, engineering owns a separate **Implementation Plan** in the relevant code repository. It may define architecture, APIs, rollout, observability, and technical trade-offs, but it does not replace or silently redefine the approved PRD.

## What Product OS owns

- Traceable Signals, Opportunities, optional Initiatives, PRDs, Outcome Contracts, and Learnings.
- PRD interrogation and evidence-quality checks before drafting.
- Human review tied to an immutable product version.
- Product context for delivery systems, engineering agents, and team updates.
- A computed Decision Queue showing product judgments that need attention.

It does not replace Linear or Jira, analytics tools, transcript providers, code repositories, engineering planning, or GTM execution. It ships no additional UI and no custom MCP server.

## Start with your agent

Give Codex, Claude Code, OpenClaw, or another capable agent the installation instructions and an existing private Git repository. If needed, create the empty repository first. The agent previews the source, target, configuration, and every write before setup; optional provider connections degrade gracefully when unavailable.

This repository is not publicly released yet, so the safe installation source is a user-confirmed local checkout and exact commit. After a release, the same flow can begin from a commit-pinned public `INSTALL.md` URL.

Send your agent one request:

> Set up Product OS from this local checkout at the exact commit I confirm, following `INSTALL.md`. Use the existing private Git repository I provide, preview every change, run the read-only checks, and then ask me for the first customer signal. Help me inspect the evidence and decide whether it deserves a Product Bet; continue toward a PRD, delivery, measurement, and Learning only as real inputs and approvals become available.

See [INSTALL.md](INSTALL.md) for the installation contract.

## Verification boundaries

The reference journey is a suite of unit and contract tests for the operating model. It verifies repository invariants, artifact relationships, immutable decisions, version boundaries, installation integrity, and measurement-contract structure. Its job is to catch artifacts that read convincingly but do not hold together — a decision event rewritten after the fact, an approval pointing at a version that never existed, a Learning bound to an outcome definition its owner no longer uses.

It is not a model-quality evaluation and not proof of live provider behavior. Passing it says the operating model is internally sound. It says nothing about whether a Product Lead made a good call, whether discovery was thorough, or whether a connector returns what it claims — none of which can be established without exercising those capabilities in the configured environment.

Synthetic technical proof is never presented as a real customer outcome. The historical example contains no fabricated production result. See the [verification model](docs/verification.md) for the exact claim boundary.

## Project status

This is a V1 reference implementation. Its release bar is an inspectable evidence-to-learning journey, not feature count.

- [Product specification](docs/spec/product-decision-os.md)
- [Security model](docs/security-model.md)
- [Contributing and local verification](docs/contributing.md)
- [Apache 2.0 license](LICENSE)

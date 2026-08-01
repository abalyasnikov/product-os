# V1 implementation contract

This file freezes the shared boundaries used by parallel implementers. It is subordinate to `docs/spec/product-decision-os.md`.

## Deliverable

A runnable open-source reference repository that proves two verticals:

1. Evidence → Opportunity → standalone PRD or optional Initiative → review metadata → Linear handoff projection.
2. Delivery or evaluation readiness → measurement anchor → result → Learning → Product Update.

No production provider is mutated by tests. Provider integrations are capability mappings for existing MCPs.

## Artifact contract

Artifact Markdown lives below `product/<type>/` and starts with YAML frontmatter. Required common fields:

```yaml
schema_version: 1
id: signal_01JEXAMPLE
type: signal
title: Concise title
created_at: 2026-08-01T12:00:00Z
updated_at: 2026-08-01T12:00:00Z
authors: [product-lead]
relationships: {}
```

Supported types and ID prefixes:

| Type | Prefix | Default directory |
|---|---|---|
| Signal | `signal_` | `product/signals/` |
| Pattern | `pattern_` | `product/patterns/` |
| Opportunity | `opportunity_` | `product/opportunities/` |
| Initiative | `initiative_` | `product/initiatives/` |
| PRD | `prd_` | `product/prds/` |
| Outcome Contract | `outcome_` | `product/outcome-contracts/` |
| Learning | `learning_` | `product/learnings/` |
| Product Update | `update_` | `product/updates/` |

Outcome Contracts are embedded in PRDs or Initiatives by default. The standalone type supports extracted reusable contracts.

## Relationship contract

Relationship values are stable artifact IDs. Validators must reject unknown IDs, type/prefix mismatches, duplicate IDs, and malformed relationship containers. External references such as Granola, Linear, analytics queries, implementation plans, commits, and URLs are not internal artifact IDs.

## Capability contract

Adapters describe existing MCP capabilities, not implementations:

- `transcript.search`, `transcript.read`
- `delivery.project.read`, `delivery.project.write`
- `analytics.query`
- `git.review.read`, `git.commit.read`

Every write workflow must be previewable and idempotent. Smoke tests are read-only.

## CLI contract

```text
product-os validate [workspace]
product-os smoke-test [workspace]
product-os adapter-check [workspace]
```

- Exit `0`: pass.
- Exit `1`: validation failure with actionable messages.
- Exit `2`: invocation/configuration error.
- `--json` returns a stable machine-readable report.

## Ownership

- Worker A: `schemas/`, `templates/`, `examples/fixtures/`
- Worker B: `src/product_decision_os/`, `tests/validator/`
- Worker C: `skills/`, `adapters/`, `integrations/`, `tests/skills/`
- Integration owner: root files, `README.md`, installer, end-to-end tests, assets, cross-cutting fixes.

## Acceptance bar

- Valid fixture passes all commands.
- Invalid fixtures cover duplicate IDs, broken references, type mismatch, oversized excerpt, transcript-sized content, credential-like content, stale adapter hashes, stale implementation reference, stale measurement definition, missing measurement anchor, unverified executable binding, and incomplete evidence waiver.
- Decision events are append-only against a configured Git baseline; mutation and removal fail validation.
- Re-running handoff projections creates no duplicate external object IDs.
- No fixture contains real customer data or credentials.
- `scripts/run_reference_journey.py` proves a clean install through final Learning for Codex, Claude Code, and OpenClaw using reachable Git version boundaries.
- The curated Best-in-class trading experience example contains six focused PRDs and labels every non-historical measurement as synthetic.
- Live MCP authorization, provider mutations, analytics execution, and model-quality evals are reported separately and are never inferred from fixture success.

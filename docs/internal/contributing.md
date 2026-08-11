# Contributing

Product OS is an agent-native, Git-backed product decision system. Contributions should preserve the separation between human-readable product work, deterministic repository contracts, and live provider behavior.

## Sources of truth

- Product behavior: [`docs/spec/product-os.md`](../spec/product-os.md)
- Verification and release claims: [`docs/internal/verification.md`](verification.md)
- Schemas: `schemas/`
- Canonical skills: `skills/`
- Generated client adapters: `adapters/`

Do not add workflow behavior to adapters or hand-edit generated hashes. Canonical workflow changes belong in `skills/` or `integrations/`; client-specific discovery prose and destinations remain in `adapters/`. After either kind of change, regenerate the projections and verify that generation remains deterministic.

## Local environment

Requirements: Python 3.11 or 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Verification commands

Run the complete test suite:

```bash
python -m pytest
```

Validate and smoke-test the compact valid workspace:

```bash
product-os check tests/fixtures/valid-workspace
```

Verify the immutable distribution manifest and generated adapters:

```bash
python scripts/manifest.py verify .
python scripts/generate_adapters.py --check
```

Exercise a clean installation and the repository-controlled reference journey:

```bash
python scripts/run_reference_journey.py --client codex
python scripts/run_reference_journey.py --client claude-code
python scripts/run_reference_journey.py --client openclaw
```

These commands prove repository behavior only. They do not prove live MCP authorization, provider mutations, analytics semantics, human identity, or model judgment. Follow [`docs/internal/verification.md`](verification.md) when describing what passed.

## Repository map

```text
schemas/                 Artifact contracts
templates/               Human-readable Markdown templates
skills/                  Canonical agent-neutral workflows
adapters/                Generated client projections
integrations/            Existing-provider capability mappings
src/product_os/ Deterministic repository tooling
examples/                Human-readable worked product documents
tests/fixtures/           Reproducible technical and failure journeys
tests/                    Contract, security, validation, and end-to-end coverage
```

## Contribution rules

- Preserve evidence provenance; never add secrets, raw transcripts, or customer PII.
- Keep Product OS separate from engineering planning. Delivery tools own estimates and sequencing; code repositories own Implementation Plans.
- Use existing provider MCPs rather than adding custom MCP servers.
- Keep narrative product content in Markdown and machine-critical identity or contracts structured.
- Add or update tests for every deterministic behavior and failure path.
- Regenerate derived artifacts instead of maintaining several manual copies.
- Do not turn fixture output into a claim about a live provider or production result.

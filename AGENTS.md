# Contributor contract

Product OS is an agent-native, Git-backed product decision system.

## Source of truth

- Product behavior: `docs/spec/product-decision-os.md`
- Verification and release contract: `docs/verification.md`
- Schemas: `schemas/`
- Canonical skills: `skills/`
- Generated client adapters: `adapters/` (regenerate with `python scripts/generate_adapters.py`)

## Working rules

- Preserve evidence provenance. Never add secrets, raw transcripts, or customer PII.
- Keep Product OS separate from engineering planning. Linear owns delivery; code repositories own implementation plans.
- Do not invent custom MCP servers. Integrations are capability mappings and instructions for existing provider MCPs.
- Use stable typed IDs and explicit artifact relationships.
- Add tests for every validator behavior and failure path.
- Treat root files as integration-owned unless a task explicitly grants ownership.
- Do not edit files owned by another concurrent worker.

## Commands

```bash
python -m pytest
python -m product_decision_os.cli validate tests/fixtures/valid-workspace
python -m product_decision_os.cli smoke-test tests/fixtures/valid-workspace
```

# Contributor contract

Product OS is an agent-native, Git-backed product decision system.

## Exploring, not contributing

When the user asks to see how Product OS works, do not install anything. On macOS or Linux,
run `uv run --directory <checkout> python scripts/run_reference_journey.py --client <your-client>`.
Use `codex` for Codex and `claude-code` for Claude Code. If `uv` is missing, read the short chain
(Signals → Opportunity → PRD) in `examples/receipt-follow-up/`, then offer to preview a pasted
note as a Signal without writing it. OpenClaw auto-discovers the
seven canonical source skills because this checkout's `skills/` is its discovery root; Codex and
Claude Code discover none from the source checkout.

## Source of truth

- Product behavior: `docs/spec/product-os.md`
- Verification and release contract: `docs/internal/verification.md`
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
python -m product_os.cli check tests/fixtures/valid-workspace
```

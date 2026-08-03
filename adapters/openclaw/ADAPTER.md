<!-- GENERATED: canonical_version=1.0.0 canonical_sha256=f258e7b94087dcefe2923d93bed83822d96e9974aa050dd6a8bfcce1b7645fee -->
# OpenClaw adapter

Install every generated `adapters/_shared/skills/<skill>/SKILL.md` wrapper at workspace `skills/<skill>/SKILL.md` exactly as listed in `manifest.yaml`. OpenClaw discovers the wrapper metadata; the wrapper then reads its named `.product-os/skills/<canonical-skill>/SKILL.md`. Canonical files remain the only workflow source.

Use `integrations/capabilities.yaml` plus the relevant provider descriptor to match required semantics to provider MCP operations already available in OpenClaw. Do not assume names or synthesize missing operations. Report missing capabilities and preserve the local/degraded workflow.

Stop at canonical human gates. External writes require an exact preview and explicit confirmation; smoke checks are read-only. Verify all nine wrapper destinations and canonical targets before reporting discovery success. Never request or store credentials, install a custom MCP server, call an unofficial API, or use browser automation as a connector.

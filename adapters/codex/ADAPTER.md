<!-- GENERATED: canonical_version=1.0.0 canonical_sha256=a163e23b21dcd78ece65fea6fb9418692a7eb2682cd7f6be96548560af9dd6f4 -->
# Codex adapter

Install every generated `skills/<skill>/SKILL.md` wrapper at `.agents/skills/<skill>/SKILL.md` exactly as listed in `manifest.yaml`. Codex discovers the wrapper metadata; the wrapper then reads its named `.product-os/skills/<canonical-skill>/SKILL.md`. Canonical files remain authoritative and wrappers add no workflow behavior.

For each declared capability, read `integrations/capabilities.yaml` and the selected provider descriptor. Resolve a semantically matching operation only from MCP tools already exposed to Codex. Tool names may differ. If required semantics are absent, report the capability as unavailable and follow the skill's degraded path.

Before any tool with external-write semantics, show the exact preview and stop for the skill's human confirmation. Smoke tests use read-only tools. Verify all nine wrapper destinations and canonical targets before reporting discovery success. Never install or generate a custom MCP, call an unofficial API, use browser automation, or request credentials.

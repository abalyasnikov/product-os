<!-- GENERATED: canonical_version=1.0.0 canonical_sha256=4934e5b1fa2af31dfd85502445337662fc07d2fd4b50a57873a1c0d0b383c596 -->
# Claude Code adapter

Install every generated `skills/<skill>/SKILL.md` wrapper at `.claude/skills/<skill>/SKILL.md` exactly as listed in `manifest.yaml`. Claude Code discovers the wrapper metadata; the wrapper then reads its named `.product-os/skills/<canonical-skill>/SKILL.md`. Canonical files remain authoritative and wrappers add no client-specific decision logic.

Resolve capability names through `integrations/capabilities.yaml` and a provider descriptor against MCP tools already configured in Claude Code. Match semantic inputs, outputs, access mode, and safety preconditions rather than assuming a fixed tool name. An incomplete match is an unavailable capability, not permission to add a fallback client.

Honor every human gate in the canonical skill. Preview external writes, await explicit confirmation, and keep smoke checks read-only. Verify all nine wrapper destinations and canonical targets before reporting discovery success. Never embed credentials, implement a custom MCP server, use an unofficial API, or scrape a provider UI.

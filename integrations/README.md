# Existing-provider MCP mappings

These files are declarative capability mappings and provider-specific guidance. They do not implement MCP servers, network clients, OAuth, proxies, transports, or provider APIs.

An executing agent must discover an already configured provider MCP, match one of its read/write operations to the semantic capability contract, and preserve the provider object's returned identity and provenance. Tool names are intentionally not hardcoded because supported clients expose configured MCPs differently.

If the existing MCP cannot satisfy the required inputs/outputs or safety semantics, the capability is unavailable. Report that gap; do not use browser automation, shell networking, unofficial SDKs, or a hidden data copy.

External SaaS descriptors (`granola`, `linear`, `amplitude`, `mixpanel`, `metabase`, and `github`) always require an already configured provider MCP and provider-managed credentials. `local-git.md` is narrowly scoped agent-native guidance for commit inspection and explicitly configured solo approval; it is not an exception for external SaaS access and cannot satisfy provider review.

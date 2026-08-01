# Generated client adapters

These static adapters teach supported agents where to find the canonical workflows and how to resolve capability descriptors against MCPs already configured in that client. They contain no workflow fork and no connector implementation.

## Canonical source digest

The `canonical_source.content_hash` in every manifest is SHA-256 over every regular file below `skills/` and `integrations/`, ordered by POSIX relative path. For each file, hash:

```text
relative/path + NUL + raw file bytes + NUL
```

The adapter freshness test recomputes this digest. Any canonical change requires regenerating all client manifests together. Generated files must not be hand-edited into a competing workflow source.

Adapters deliberately do not embed credentials, provider URLs, MCP transports, executable tool code, or unofficial fallbacks.

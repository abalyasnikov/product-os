# Security model

## Protected assets

- Customer evidence and transcript confidentiality.
- Human approval and product-decision attribution.
- Git repository integrity.
- Existing MCP provider authority, especially external writes.
- Canonical skill and generated-wrapper integrity.

## Threats and controls

| Threat | Control |
|---|---|
| Malicious source text instructs the agent | Untrusted-data contract, read-only ingestion phase, bounded typed normalization, raw-content removal before writes, fresh human confirmation |
| Tampered or path-traversing adapter projection | Deterministic installer, relative allowlisted destinations, resolved containment, symlink rejection, no overwrite |
| Generated wrapper diverges from canonical skill | Canonical source digest plus active-wrapper comparison during smoke test |
| Decision event is removed or rewritten | Git-baseline comparison with append-only events; gated transitions fail when baseline cannot be verified |
| Approval is forged in repository text | Provider mode derives approval from provider evidence and commit SHA; review-state is only a verified cache |
| Secret or PII enters Git | Reference-only evidence, exact diff preview, staged-diff scan, credential blocking, PII warnings, human review |
| Connector acts as confused deputy | Capability allowlist, read/write semantics, provider-managed authentication, read-before-write, exact preview and human confirmation |
| YAML or filesystem input causes denial of service | File-size, node/depth and alias limits, cycle-aware traversal, symlink rejection, bounded error output |

## Release provenance

`manifest.json` detects accidental or post-build file changes but cannot authenticate its own publisher. A malicious fork can regenerate it. Therefore:

- development installs require explicit trust in a local path and commit;
- public one-link installation must remain disabled while `canonical_origin` is `unpublished`;
- a public release must anchor origin, publisher, commit, and manifest signature or attestation outside the checkout;
- the bootstrap verifier must be obtained through that independent trust channel before repository instructions are executed.

## Residual risks

- Human reviewers can approve unsafe content.
- Provider MCP implementations and their authentication remain outside this project's control.
- PII and secret detection is incomplete by design and must not be represented as a guarantee.
- Solo approval proves intentional local action, not organizational identity or separation of duties.

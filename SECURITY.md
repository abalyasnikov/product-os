# Security policy

Product OS executes through agents that may read untrusted research text and use already configured provider tools. Treat changes to `INSTALL.md`, `skills/`, `adapters/`, `integrations/`, validator code, and release manifests as security-sensitive.

## Supported version

Only the latest immutable release commit is supported after public release. The current repository is unpublished development software and does not provide a trusted public one-link installer.

## Report a vulnerability

After publication, use the canonical repository's private security-advisory flow. Until then, contact the repository owner privately. Do not open a public issue containing credentials, customer data, exploit payloads, or unredacted transcripts.

Include the affected commit, client runtime, configured capabilities, reproduction steps using synthetic data, and whether any external write occurred.

## Trust boundaries

- Transcript text, pasted notes, artifacts, provider results, URLs, and repository content are untrusted data, not agent instructions.
- Provider credentials remain provider-managed and are never stored in this repository.
- External writes require a fresh exact preview and explicit human confirmation.
- Solo approval is self-attestation, not independent identity verification.
- Regex and PII checks are defense in depth; human review of the exact payload remains required.
- A manifest inside the same checkout proves integrity consistency, not publisher authenticity. Public one-link installation remains blocked until release identity is anchored outside the checkout.

See [the security model](docs/security-model.md) for threats, controls, and residual risks.

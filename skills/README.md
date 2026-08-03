# Canonical skills

This directory is the agent-neutral source of truth for Product OS workflows. Client adapters may point at or project these files, but must not change their behavior.

All skills follow the same safety contract:

- read repository truth before reading only the external connectors needed for the current decision;
- use capabilities declared in `../integrations/capabilities.yaml`, mapped to existing provider MCPs;
- preview every external or Git write and require the named human gate;
- preserve stable IDs and provider external IDs so retries are idempotent;
- stop with an explicit named gap when approval, provenance, or a capability cannot be verified;
- never invent a product decision, approval, measurement result, provider tool, hidden API client, or custom MCP server;
- never commit credentials, full transcripts, or customer PII.

## Product Bet and Outcome Contract identity

Every workflow carries one logical Product Bet identity: the standalone PRD ID for a small Bet, or the Initiative ID for a multi-PRD Bet. Product Bet is not an artifact type: never mint a `bet_` ID or file. Child PRDs remain linked artifacts inside the Initiative-owned Bet; they do not become additional Bet identities.

Outcome Contracts are embedded in the owning PRD or Initiative by default. Use a separate `outcome_` artifact only for a large or reusable contract, link it by stable internal relationship, and do not keep a duplicated embedded copy. An Initiative's shared contract and each child PRD contract are distinct: child contracts measure barrier removal, while the Initiative contract measures the shared user outcome.

`canonical_version: 1.0.0` is shared by all V1 skills and generated client adapters.

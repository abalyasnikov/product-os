# ADR 0001: Keep product truth separate from delivery and implementation

- Status: accepted
- Date: 2026-08-01

## Context

Product teams already use Git providers, Linear, transcript systems, analytics products, and coding agents. Copying their data into another runtime would create drift and administration.

## Decision

Product OS owns product evidence, contracts, decisions, and learnings in Git. Linear owns engineering tasks, estimates, and delivery sequencing. Code repositories own optional Implementation Plans and ADRs. Provider MCPs retain authentication and external data access.

The system stores stable references and version bindings instead of mirroring external systems. It ships no custom MCP server and no UI.

## Consequences

- A missing provider causes an explicit local degradation, not a hidden data copy.
- Product artifacts remain inspectable and portable across agent runtimes.
- Cross-system consistency depends on versioned references and idempotent handoffs.
- Technical correctness and release approval stay with engineering.

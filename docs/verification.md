# Verification model

Product Decision OS separates deterministic repository proof from live provider proof.
Passing a fixture never implies that an external account, mutation, or model judgment was
verified.

## Deterministic end-to-end proof

Run from a provenance-verified source checkout:

```bash
python scripts/run_reference_journey.py --client codex
```

CI executes the same journey for Codex, Claude Code, and OpenClaw. Each run starts with an
empty directory and proves:

1. release-manifest verification;
2. preview-first installation with a confirmed plan hash;
3. active skill projection for the selected client;
4. a real Git commit containing pre-authored normalized evidence and an undecided Opportunity;
5. a second commit containing the human-owned `pursue` event bound to the first commit;
6. an Initiative with four child PRDs and synthetic review records bound to reachable commits;
7. delivery and optional Implementation Plan references bound to the same reachable approval version;
8. an explicit measurement anchor and synthetic analytics result;
9. pre-authored Outcome Review, Learning decision, and sourced Product Update artifacts materialized through real version boundaries;
10. final `validate` and `smoke-test` passes.

For every decision or implementation handoff, the validator checks more than SHA
reachability: the referenced commit must contain the exact artifact. Solo review additionally
requires the configured approval trailer in that commit; a review-state cache cannot invent it.

The technical fixture uses synthetic measurement where source history contains no trustworthy
result. That is deliberate: it tests the operating contract without inventing Zerion production
facts. The human-readable historical example contains no fabricated result.
The runner does not judge source material, execute agent skills, interrogate a PM, or generate
the artifacts; those behaviors require an agent-quality eval and are not inferred from this
deterministic journey.

## Live provider proof

Live verification is environment-specific and requires the user's configured provider MCPs.
It must be reported capability by capability:

| Capability | Passing condition |
|---|---|
| Granola retrieval | The agent can search and read a user-approved meeting without exporting the full transcript into Git. |
| Linear or Jira handoff | A previewed create/update uses the PRD stable ID as its idempotency key and a retry reuses the same object. |
| Analytics measurement | The configured query runs against the declared definition version and returns provenance plus slice and guardrail results. |
| Git review | The provider review or explicit solo commit is verifiable at a reachable immutable commit, including provider identity rather than fixture metadata. |
| Agent quality | A separately versioned case set evaluates evidence fidelity, interrogation quality, PRD completeness, and unsupported-claim rate. |

Unavailable capabilities must be named as degraded. They may save drafts but cannot fabricate
provider output or cross the dependent human gate.

## Claim language

- Say **“deterministic reference journey passed”** after the automated runner succeeds.
- Say **“live provider flow passed”** only for capabilities actually exercised in that environment.
- Say **“full production loop verified”** only when all configured provider checks and the agent-quality eval pass together.

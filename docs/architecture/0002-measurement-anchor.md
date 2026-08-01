# ADR 0002: Anchor learning to observation, not project completion

- Status: accepted
- Date: 2026-08-01

## Context

A completed Linear project does not prove that users received a feature. Rollouts, feature flags, experiments, migrations, and pre-release evaluations begin observation at different times.

## Decision

Every completed Outcome Review records a measurement anchor. For a released experience, actual exposure is preferred; a verified release is the fallback. Case-based, qualitative, or pre-release work uses an explicit evaluation event.

The anchor includes its type, external or manual reference, time, and applicable rollout or evaluation scope. The configured measurement window starts from that event.

## Consequences

- Product Decision OS does not infer outcome timing from Linear completion.
- Outcome Review blocks unsupported success claims when the anchor is missing.
- Manual evaluation remains possible with provenance when no provider exposes an event.

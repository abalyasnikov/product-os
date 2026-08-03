# Public release checklist

No public one-link install may be advertised while `canonical_origin` is `unpublished`. That flag is the gate: flipping it tells every agent that a pinned public source exists and can be trusted, so it is the last step, not the first.

## Continuously enforced

CI runs these on every push and pull request, so they need no manual repetition at release time. A red build is a release blocker by itself.

- The clean-install reference journey for Codex, Claude Code, and OpenClaw.
- The full test suite, including the append-only decision history comparison.
- Distribution manifest verification against the working tree.
- Deterministic, idempotent adapter generation (`--check` fails on drift).

## Verified once, before publishing

- Public examples contain no private data, customer identifiers, credentials, transcript text, exact revenue figures, or commit references that resolve only inside a private repository.
- No non-English content or personal working notes remain in tracked files.
- Reader-facing documents lead with what the system does rather than how it is verified.

## Requires a human, still open

- Run one private-repository pilot: install into a real private repo through an agent, and take at least one artifact from evidence to an approved PRD.
- Report live MCP capability results separately. Deterministic fixtures are not evidence that a provider authorized, returned, or wrote anything.
- Calibrate the model-quality evaluation. The reference journey proves the operating model holds together; it says nothing about the quality of agent judgment.
- Produce the immutable release commit, then rebuild the manifest against the real origin:

  ```bash
  python scripts/manifest.py build . \
    --canonical-origin https://github.com/abalyasnikov/product-os \
    --publisher abalyasnikov \
    --release <version>
  ```

- Publish a commit-pinned raw URL for `INSTALL.md`. Never a branch, never a mutable tag: a branch URL silently changes what an agent installs after the user has already trusted it.

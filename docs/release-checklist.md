# Public release checklist

The local reference implementation must not advertise a public one-link install until all items pass:

- Run `python scripts/run_reference_journey.py --client codex` from the release candidate.
- Confirm CI runs the same journey for Codex, Claude Code, and OpenClaw.
- Report live MCP capabilities separately; do not present deterministic fixtures as live verification.

- Create the canonical public repository and record its exact origin and publisher in `manifest.json`.
- Produce an immutable release commit and rebuild the distribution manifest with `python scripts/manifest.py build . --canonical-origin <https-repository> --publisher <publisher> --release <version>`.
- Publish a commit-pinned raw URL for `INSTALL.md`; never use a branch or mutable tag.
- Verify generated client projections in clean Codex, Claude Code, and OpenClaw workspaces.
- Run CI, the full fixture suite, manifest verification, and one private-repository pilot.
- Confirm the public examples contain no Zerion-private data, customer identifiers, credentials, or transcript text.

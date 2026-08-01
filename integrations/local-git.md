# Agent-native local Git guidance

Local Git is an agent-native repository capability, not an MCP mapping, SaaS connector, custom server, or provider-review substitute.

Use local Git only when setup selected `agent_native_local_git`:

- `git.commit.read` may inspect immutable commit identity, commit metadata, diffs, and the configured default branch from the local repository.
- In configured `solo` review mode, first verify that the repository policy explicitly permits solo self-approval. Show the full commit SHA and diff, ask the human to self-attest to that precise version, and only after fresh confirmation create a normal commit containing the trailer `Product-Approval: explicit`.
- Read the resulting commit metadata back and verify the exact trailer before treating that version as approved.
- If the commit, trailer, policy, or human confirmation cannot be verified, approval is `unknown` and handoff stops.
- State the limitation: the solo trailer is self-attestation by the current operator. It is not independent identity proof, separation of duties, or evidence of approval by another reviewer.
- Any `.product-os/review-state.yaml` or other review-state file is cache only; refresh full local commit metadata and never use cached status as approval evidence.

Local Git cannot satisfy `git.review.read`: it cannot prove provider reviewer identity, review timing, pull-request target, discussion, or merge approval. Provider review mode therefore requires an existing provider MCP such as the GitHub mapping. Never silently fall back to a local trailer, and never implement a custom MCP, network client, or hidden review store.

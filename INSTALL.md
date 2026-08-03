# Agent installation instructions

You are installing Product OS into a private Git repository. Product OS is a set of schemas, Markdown templates, agent skills, integration mappings, and deterministic checks. It is not a hosted service and must not receive credentials.

## Safety gate

Before changing anything:

1. Resolve this document to an immutable Git commit. While `canonical_origin` is `unpublished`, accept only a user-confirmed local checkout path and its current commit; do not claim that a public one-link install is available.
2. Show the user the repository origin, publisher, commit, and target repository.
3. If the origin is a fork or differs from the canonical origin recorded in `manifest.json`, ask for explicit confirmation.
4. Verify every distributed file against `manifest.json`.
5. Stop on an origin, path, or content-hash mismatch.

Do not execute skills or scripts before provenance verification. Never request API keys, tokens, passwords, transcript exports, or customer data in chat.

## Install

1. Ask the user for an existing private repository URL or local path. If they do not have one, ask them to create a private repository and return with its URL or path; V1 does not create repositories.
2. Inspect the target. Never overwrite an existing file silently.
3. Ask for the client, default branch, and review policy: provider review with the configured Initiative/PRD approver, or explicit solo approval with the `Product-Approval: explicit` commit trailer. Preview the complete resulting `.product-os/config.yaml`; after confirmation, save it as the validated configuration input outside the target repository.
4. Run the deterministic installer below in preview mode. Show every source→destination action, conflict, file hash, and returned `plan_hash`. Do not write the target yet.
5. After fresh confirmation of that exact plan hash, apply the saved plan. Do not copy files manually. The installer adds the canonical assets under `.product-os/`, release provenance, and all nine route-only wrappers at the current client's declared discovery root.
6. Create `product/<type>/` directories lazily with the first artifact so Git does not depend on empty directories.
7. Ask which existing MCP providers the user wants to enable. Follow each provider's own authentication flow. Do not implement OAuth, proxy credentials, or create a custom MCP server.
8. From the provenance-verified source checkout, install the validator with `python -m pip install <absolute-source-checkout>`; for local development, `python -m pip install -e <absolute-source-checkout>` is allowed. Then run `product-os validate <target-repository>` and `product-os smoke-test <target-repository>`. Missing optional providers must degrade only their dependent workflows.
9. Show the exact proposed Git diff and final payload hash. Commit or push only after fresh confirmation.

The deterministic installer is preview-first. Substitute absolute verified paths and the selected client:

```bash
python <source>/scripts/install_workspace.py <source> <target> \
  --client <codex|claude-code|openclaw> \
  --config <confirmed-config.yaml> \
  --write-plan <plan.json>
```

For an unpublished local checkout, add `--allow-unpublished-local` only after the user explicitly confirms the local source path and commit. Show the generated `plan_hash`. Apply exactly that saved plan:

```bash
python <source>/scripts/install_workspace.py <source> <target> \
  --client <same-client> \
  --config <same-config.yaml> \
  --apply-plan <plan.json> \
  --expect-plan-hash <confirmed-plan-hash>
```

The installer replans and stops if source bytes, config, client, target conflicts, or the plan hash changed. It creates `.product-os/release-manifest.json`, `.product-os/install-plan.json`, and a scoped `.product-os/installed-manifest.json`.

## Completion report

Report:

- installed source commit and manifest digest;
- files added and files deliberately left unchanged;
- selected client adapter and enabled capabilities;
- smoke-test results and named degraded capabilities;
- the prompt that drafts `context/strategy.md` from the installed template, and a plain statement that until that file exists every strategic-fit judgment stays an explicit gap;
- the next natural-language prompt that creates the first Signal or Opportunity.

Installation never writes `context/strategy.md` itself. It is workspace content owned by the human and goes through the normal preview-and-confirm loop like any other artifact.

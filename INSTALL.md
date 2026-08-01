# Agent installation instructions

You are installing Product Decision OS into a private Git repository. Product Decision OS is a set of schemas, Markdown templates, agent skills, integration mappings, and deterministic checks. It is not a hosted service and must not receive credentials.

## Safety gate

Before changing anything:

1. Resolve this document to an immutable Git commit. While `canonical_origin` is `unpublished`, accept only a user-confirmed local checkout path and its current commit; do not claim that a public one-link install is available.
2. Show the user the repository origin, publisher, commit, and target repository.
3. If the origin is a fork or differs from the canonical origin recorded in `manifest.json`, ask for explicit confirmation.
4. Verify every distributed file against `manifest.json`.
5. Stop on an origin, path, or content-hash mismatch.

Do not execute skills or scripts before provenance verification. Never request API keys, tokens, passwords, transcript exports, or customer data in chat.

## Install

1. Ask the user for an existing private repository URL or offer to create a new private repository after explicit confirmation.
2. Inspect the target and preview all additions. Never overwrite an existing file silently.
3. Copy these canonical directories into `.product-os/`: `schemas/`, `templates/`, `skills/`, `adapters/`, and `integrations/`. Copy `manifest.json` as release provenance.
4. Install the current client's generated wrapper skills at the exact source→destination paths declared by its adapter manifest. Generated wrappers only route to `.product-os/skills/`; they never become workflow truth.
5. Create `product/<type>/` directories lazily with the first artifact so Git does not depend on empty directories.
6. Ask for the default branch and review policy: provider review with the configured Initiative/PRD approver, or explicit solo approval with the `Product-Approval: explicit` commit trailer. Preview the resulting `.product-os/config.yaml`.
7. Ask which existing MCP providers the user wants to enable. Follow each provider's own authentication flow. Do not implement OAuth, proxy credentials, or create a custom MCP server.
8. From the provenance-verified source checkout, install the validator with `python -m pip install <absolute-source-checkout>`; for local development, `python -m pip install -e <absolute-source-checkout>` is allowed. Then run `product-os validate <target-repository>` and `product-os smoke-test <target-repository>`. Missing optional providers must degrade only their dependent workflows.
9. Show the exact proposed Git diff. Commit or push only after confirmation.

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
- the next natural-language prompt that creates the first Signal or Opportunity.

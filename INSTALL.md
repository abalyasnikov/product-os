# Agent installation instructions

You are installing Product OS into a private Git repository. Product OS is a set of schemas, Markdown templates, agent skills, integration mappings, and deterministic checks. It is not a hosted service and must not receive credentials.

## Safety gate

Before changing anything:

1. Resolve this document to an immutable Git commit. While `canonical_origin` is `unpublished`, accept only a user-confirmed local checkout path and its current commit; do not claim that a public one-link install is available.
2. Show the user the repository origin, publisher, commit, `source_state`, and target repository. `source_state` says whether that commit describes the bytes being installed: `clean`, `uncommitted_changes:N`, or `not_a_git_checkout`. Anything other than `clean` means the human is confirming a working tree rather than a reviewed commit; say so plainly instead of presenting the SHA alone. This is the
   unpublished-source trust confirmation; target and configuration are confirmed inside the
   later plan-hash preview.
3. If the origin is a fork or differs from the canonical origin recorded in `manifest.json`, ask for explicit confirmation.
4. Verify every distributed file against `manifest.json`.
5. Stop on an origin, path, or content-hash mismatch.

Do not execute skills or scripts before provenance verification. Never request API keys, tokens, passwords, transcript exports, or customer data in chat.

## Install

1. Ask the user for an existing private repository URL or local path. If they do not have one, ask them to create a private repository and return with its URL or path; V1 does not create repositories.
2. Inspect the target. Never overwrite an existing file silently.
3. Ask for the client, default branch, and review policy: provider review with the configured Initiative/PRD approver, or explicit solo approval with the `Product-Approval: explicit` commit trailer. Save the schema-valid configuration input outside the target repository; its exact bytes are covered by the plan hash.
4. Run the deterministic installer below in preview mode. Show a short preview: version, target, selected client, review mode, file counts by ownership/action, conflicts, and `plan_hash`. Keep the full source→destination list in `plan.json` unless asked. Do not write the target yet.
5. After fresh confirmation of that exact plan hash, apply the saved plan. Do not copy files manually. The installer adds the canonical assets under `.product-os/`, release provenance, and every route-only wrapper at the current client's declared discovery root.
6. Create `product/<type>/` directories lazily with the first artifact so Git does not depend on empty directories.
7. Ask which existing MCP providers the user wants to enable. Follow each provider's own authentication flow. Do not implement OAuth, proxy credentials, or create a custom MCP server.
8. Without global pip state, run `uvx --reinstall --from <absolute-source-checkout> product-os check <target-repository>`. The installer itself can run as `uvx --reinstall --from <absolute-source-checkout> product-os-install …`. Missing optional providers must degrade only their dependent workflows.
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

## Ownership

| Class | Paths | Update behavior |
| --- | --- | --- |
| Managed | `.product-os/{schemas,templates,skills,integrations,adapters}/`, `.product-os/README.md`, selected-client wrappers | Update only from an unchanged installed baseline; a local edit conflicts and halts, while a local deletion is restored. |
| Preserved | `.product-os/config.yaml`; installed `AGENTS.md` and `CLAUDE.md` | Never overwritten. Config is checked for presence and schema; context files become user-owned after creation. |
| Generated | `.product-os/{release-manifest,install-plan,installed-manifest}.json` | Rewritten only by a confirmed install/update operation. |
| User-owned | `context/`, `product/`, `inputs/`, `external/`, everything else | Never touched. |

Managed files are not customization points and are never automatically merged.

## Update

Ask: “Update Product OS in `<target>` from this trusted checkout; check the installed baseline,
show the short plan, and wait for my confirmation.” The agent confirms the new origin and source
commit under the same unpublished trust gate, then runs the same `--write-plan` / `--apply-plan`
/ `--expect-plan-hash` flow. The installer reads the target's existing config, requires the prior
install to be committed and managed planned paths to be clean, and previews old commit → new
commit plus action/ownership counts, deletes, conflicts, and `plan_hash`.

Any conflict stops the entire update before its first write. The report lists conflicting files
and offers exactly: repair the named managed files to the recorded baseline and re-run, or stop
and keep the unsupported local edits. A clean preview ends: “Product artifacts and configuration remain unchanged.” Use `chore: update Product OS 0.1.0 (abc1234 -> def5678)` while unpublished.

## Check and recovery

“Check whether Product OS is healthy” runs `product-os check` and reports version plus
installed source commit, managed integrity, wrapper integrity as byte-verified, workspace
validity, and connector state (`degraded` is not a repository failure). Discovery is a next-session
fact, not a static-scan claim. With no `.product-os/`, answer: “Product OS is not installed here —
is your workspace at another path?” If the recorded checkout/commit is unavailable, re-clone the
origin, run `git checkout <recorded-commit>`, and retry.

Repair previews restoration of named Managed files only. A schema-invalid preserved config uses
the normal preview/confirm authoring loop. Rollback previews one `git revert` of the install/update
commit. Uninstall reverts an unused install; otherwise it previews deletion of Managed and
Generated manifest paths, preserves product/context/config files, and offers to remove dangling
Product OS routing from `AGENTS.md`/`CLAUDE.md`.

## Completion report

Report:

- installed source commit and manifest digest;
- files added and files deliberately left unchanged;
- selected client adapter and enabled capabilities;
- smoke-test results and named degraded capabilities;
- wrapper integrity as byte-verified for every wrapper, with live discovery deferred to the next session opened at the workspace root;
- a pointer to `.product-os/README.md`, the durable workspace guide, and a reminder that the worked example stays in the source checkout;
- the prompt that drafts `context/strategy.md` from the installed template, and a plain statement that until that file exists every strategic-fit judgment stays an explicit gap;
- the next natural-language prompt that creates the first Signal or Opportunity.

In the installing session, preview that first Signal by reading `.product-os/skills/discovery/SKILL.md`
directly. Natural-language skill triggering starts only in the next session opened at the workspace
root. Installation success is the useful first-Signal preview, not merely a green smoke-test.

Installation never writes `context/strategy.md` itself. It is workspace content owned by the human and goes through the normal preview-and-confirm loop like any other artifact.

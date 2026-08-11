# Shared artifact authoring contract

Read this contract completely before any Product OS repository write. Canonical workflow skills decide **what** may be written and which human gate applies; this contract defines **how** artifacts are created safely.

## Resolve the canonical shape

1. Determine the artifact type from the active workflow. Never infer it from a title or filename.
2. Read `.product-os/templates/<type>.md` and `.product-os/schemas/<type>.schema.json` before drafting. `product_update` uses `product-update.md` and `product-update.schema.json`. There is no separate Outcome Contract artifact: the contract lives in its PRD or Initiative.
3. Artifacts have one shape, and Markdown is the human surface. Frontmatter carries identity, the graph, and only fields a check executes; a required prose field with a one-character minimum is a checklist, not a check, and belongs in a readable heading the validator requires. Frontmatter contains: `schema_version`, `id`, `type`, `title`, and `relationships`. Evidence and workflow artifacts may add structured provenance, results, or decision events when the validator must execute them. Git provides authorship, timestamps, and version history. In PRDs and Initiatives, keep product reasoning, journeys, requirements, risks, and GTM in the canonical readable sections; do not rename or omit their headings, and record an explicit gap instead of leaving a section empty.
4. Keep the Outcome Contract in the named `````yaml product-os:outcome````` block under `## Outcome Contract`. This is structured because agents and validators must execute it; do not move the rest of the PRD or Initiative into YAML.
5. Write only to the canonical directory:

   | Type | Typed prefix | Directory |
   |---|---|---|
   | Signal | `signal_` | `product/signals/` |
   | Pattern | `pattern_` | `product/patterns/` |
   | Opportunity | `opportunity_` | `product/opportunities/` |
   | Initiative | `initiative_` | `product/initiatives/` |
   | PRD | `prd_` | `product/prds/` |
   | Learning | `learning_` | `product/learnings/` |
   | Product Update | `update_` | `product/updates/` |

6. Valid IDs use the typed prefix plus 8–32 uppercase Crockford Base32 characters. For every newly generated artifact, use the collision-resistant 32-character subset produced by an uppercased UUID4 hexadecimal value: for example `signal_` + 32 uppercase UUID4 hex characters. Generate decision IDs the same way with `decision_`. Never derive an ID from a title, filename, user text, timestamp, or mutable provider label. Preserve existing IDs on update. Curated examples and test fixtures in this distribution may use short readable IDs instead; that exception is for hand-authored illustration, never for a workspace an agent writes into.
7. Choose a short human-readable filename independently of identity. Before writing, scan all artifacts for duplicate IDs and resolve relationships by stable ID.
8. When readable prose names another artifact, write it as a relative Markdown link with the stable ID as the link text, in the form `[<id>](../<type>/<file>.md)`. The ID remains identity and the link is navigation, so the graph stays resolvable when a file is renamed and readable in any Markdown viewer — a repository host, an editor, a notes app — without a Product OS tool. A bare ID in prose is a grep, not a link. Links must resolve; `product-os check` reports a broken one.

## Pasted or local evidence

Process supplied content transiently and do not commit the raw input. Normalize bytes only for fingerprinting without changing the interpreted evidence. Compute the lowercase SHA-256 hex digest of those bytes and record:

- pasted input: `external_id: pasted_<first-24-hex>`;
- local input: `external_id: local_<first-24-hex>`;
- `content_fingerprint: sha256:<full-64-hex>`;
- `occurred_at`: the source event date supplied or confirmed by the human;
- `retrieved_at`: the actual retrieval timestamp;
- `storage: reference_only`.

If the occurrence date is unknown, ask for it or record a named blocking provenance gap; never silently substitute retrieval time. Show the normalized Signal and fingerprint, not the raw pasted/local content, in the commit payload.

## Write loop

1. Draft from the canonical template, replace every placeholder, preserve intentional human-authored content on update, and mark unresolved gaps explicitly.
2. Run `product-os check <workspace>` before proposing a commit. This is the one command; it verifies schemas, the relationship graph, append-only decision events, that every `based_on_version` is a reachable commit containing the artifact, evidence policy, and credential patterns. Running a narrower check and calling the draft valid is the failure this replaced. If the executable is unavailable, stop with a setup blocker; do not claim the draft is valid.
3. Repair only the fields named by actionable validation errors, rerun validation, and keep the artifact uncommitted until it passes. Never remove valid domain fields merely to silence a generic schema message.
4. Show the exact file path, complete proposed artifact payload, validation result, privacy/credential scan, and Git diff.
5. Stop at the active canonical skill's human gate. Write, commit, publish, or call an external write only after the required explicit confirmation.
6. After the write, rerun validation and report the stable ID, Git version when available, unresolved gaps, and exact next workflow prompt.

External provider objects remain outside this artifact write loop and follow their integration descriptor's preview, confirmation, provenance, and idempotency rules.

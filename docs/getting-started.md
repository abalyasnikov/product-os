# Five-minute solo walkthrough

This walkthrough proves the local evidence-to-decision path without Granola, Linear, analytics, or a hosted Git provider. External workflows remain explicitly degraded.

## 1. Install locally

Send an agent the absolute path to `INSTALL.md` in a trusted checkout. Confirm the displayed local origin and commit. Choose:

```yaml
selected_client: codex
review:
  mode: solo
  git_capability: git.commit.read
  solo_approval:
    allowed: true
    commit_trailer: "Product-Approval: explicit"
```

The agent installs canonical assets under `.product-os/`, generated wrappers in the current client's discovery path, and the validator from the same verified checkout.

## 2. Create evidence without a connector

Paste a short research note and say:

```text
Turn this into decision-relevant evidence. Store only a normalized Signal and a
sha256 fingerprint of my pasted source. Show the payload before writing it.
```

The agent derives a local source ID and fingerprint, creates a typed stable Signal ID, writes `product/signals/<slug>.md`, validates it, and asks before committing.

## 3. Decide whether to pursue

Ask:

```text
Does this evidence justify an Opportunity? Show gaps and contradictions first.
```

If an Opportunity is warranted, the agent commits the undecided draft, asks for `pursue`, `hold`, or `reject`, then appends the human decision based on that draft commit. `pursue` creates one logical Product Bet identity; it does not commit engineering capacity.

## 4. Draft and review the PRD

Ask:

```text
Interrogate me before drafting. Ask no more than three questions at a time,
summarize confirmed facts and unknowns, and save a resumable checkpoint.
```

The agent defines the problem, smallest intervention, GTM hypothesis, and honest Outcome Contract before drafting. In solo mode, explicit approval is recorded with the configured commit trailer. Linear remains unavailable until connected.

## 5. Inspect what needs attention

Ask:

```text
Show my Decision Queue. If it is empty, tell me the next useful action.
```

Use `open 1` to enter the underlying workflow. A missing connector appears as a named gap, not a fabricated result.

## Recovery

- Validation failure: keep the draft, fix the named field using its template, rerun validation, and show the diff again.
- Missing connector: continue only through workflows with a documented local/manual path.
- Unknown approval: stop delivery handoff until the configured Git evidence is verifiable.
- Missing measurement anchor: do not start the outcome window or claim success.

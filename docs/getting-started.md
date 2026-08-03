# Solo walkthrough

By the end of this walkthrough you will have taken one real customer signal and turned it into a decision you can defend later: what the problem is, why it is yours to act on now, what you committed to, and how you will know whether it worked.

You need nothing but a private Git repository and an agent. No Granola, no Linear, no analytics, no hosted Git provider — those workflows stay explicitly degraded rather than pretending to work.

Two things worth reading alongside it. The [Best-in-class trading experience](../examples/best-in-class-trading-experience/README.md) example shows what these documents look like once they are real. And if you would rather watch the whole path run end to end before doing it yourself:

```bash
python scripts/run_reference_journey.py --client codex
```

That runs on a synthetic dataset with real local Git commits. It shows the shape of the loop; it proves nothing about live providers or the quality of an agent's judgment.

## 1. Install locally

Send an agent the absolute path to `INSTALL.md` in a trusted checkout, and confirm the local origin and commit it shows you. The agent asks for the rest; solo mode without connectors settles at:

```yaml
schema_version: 1
workspace_profile: core_workspace
selected_client: codex
default_branch: main
review:
  mode: solo
  approver_rule:
    initiative: current-product-lead
    prd: current-product-lead
  git_capability: git.commit.read
  solo_approval:
    allowed: true
    commit_trailer: "Product-Approval: explicit"
evidence:
  storage: reference_only
  max_excerpt_chars: 500
connectors: {}
```

The agent installs canonical assets under `.product-os/`, generated wrappers in the current client's discovery path, and the validator from the same verified checkout.

## 2. Write down what the company is trying to do

Before any evidence, ask:

```text
Draft context/strategy.md from the template. Interview me for positioning,
this year's goal, ordered product principles, explicit trade-offs, and the
MUST/SHOULD/COULD/WON'T bands. Preview the file before writing it.
```

This is the step people skip, and skipping it is why agents produce well-argued PRDs for work the company already declined. Evidence can only tell you a problem is real. This file is what lets any later workflow ask whether the problem is yours, and whether now is when you deal with it.

Order the principles. Unordered principles cannot settle an argument, and settling arguments is the only thing a principle is for.

## 3. Create evidence without a connector

Paste a short research note and say:

```text
Turn this into decision-relevant evidence. Store only a normalized Signal and a
sha256 fingerprint of my pasted source. Show the payload before writing it.
```

The agent derives a local source ID and fingerprint, creates a typed stable Signal ID, writes `product/signals/<slug>.md`, validates it, and asks before committing.

## 4. Decide whether to pursue

Ask:

```text
Does this evidence justify an Opportunity? Show gaps and contradictions first.
```

If an Opportunity is warranted, the agent commits the undecided draft, asks for `pursue`, `hold`, or `reject`, then appends the human decision based on that draft commit. `pursue` creates one logical Product Bet identity; it does not commit engineering capacity.

## 5. Draft and review the PRD

Ask:

```text
Interrogate me before drafting. Ask no more than three questions at a time,
summarize confirmed facts and unknowns, and save a resumable checkpoint.
```

The agent defines the problem, smallest intervention, GTM hypothesis, and honest Outcome Contract before drafting. In solo mode, explicit approval is recorded with the configured commit trailer. Linear remains unavailable until connected.

## 6. Inspect what needs attention

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

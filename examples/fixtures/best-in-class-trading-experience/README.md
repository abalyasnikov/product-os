# Best-in-class trading experience

This is a complete worked Product Decision OS workspace derived from a historical planning shape. It modernizes a broad trading initiative decomposed into multiple PRDs without publishing production facts, customer data, private links, or internal implementation details; all provider activity and measurements in the example are synthetic.

All people, excerpts, event IDs, account segments, URLs, delivery keys, dates, baselines, targets, and observed results are anonymized or illustrative. They demonstrate the workflow and schemas only. Do not use the numbers as Zerion performance claims or as evidence for a current roadmap decision.

## Product Bet map

```text
6 synthetic Signals
  -> 2 Patterns
  -> 1 pursued Opportunity
  -> Initiative: Best-in-class trading experience
       -> PRD: Cross-chain Swap
       -> PRD: Send Flow Redesign
       -> PRD: Skip Redundant Native Confirmation
       -> PRD: Non-blocking Transaction Status
       -> PRD: Bridge Progress Tracking
       -> PRD: Token Approval Management
  -> Linear/Jira-style delivery references
  -> optional engineering-owned Implementation Plan reference
  -> illustrative Amplitude measurement
  -> 1 Learning and outcome decision
  -> 1 cited Product Update
```

The earlier “Cross-chain Send” concept is preserved only as a rejected alternative. Its deposit-address ambiguity could create CEX deposit risk, so the accepted scope became **Send Flow Redesign**, with **Bridge Progress Tracking** split into its own barrier and child PRD.

## How to exercise the example

From the repository root:

```bash
PYTHONPATH=src python -m product_decision_os.cli validate examples/fixtures/best-in-class-trading-experience --base-ref HEAD
PYTHONPATH=src python -m product_decision_os.cli smoke-test examples/fixtures/best-in-class-trading-experience --base-ref HEAD
```

The fixture includes synthetic provider snapshots under `inputs/` and `external/`. They are intentionally offline: a passing smoke test verifies the workspace contract and descriptors, not live authorization to Granola, Linear, Jira, GitHub, or Amplitude.

## Limitations

- Six directional signals are not a representative research sample.
- The aggregate learning cannot isolate the causal contribution of each child PRD.
- Historical Jira-style keys and current Linear-style IDs are safe placeholders under `example.invalid`.
- Full transcripts remain external by design; only approved anonymized excerpts appear in artifacts.
- The illustrative Cross-chain Swap Implementation Plan lives under `external/code-repositories/` to demonstrate that technical details stay outside the PRD.
- There is no claim that this exact initiative, sequence, or illustrative result reflects current product strategy.

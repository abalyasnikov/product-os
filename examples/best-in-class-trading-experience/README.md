# Best-in-class trading experience

This is a historical worked example built from real Zerion product work. The product problems, decisions, JTBDs, scope, requirements, open questions, and proposed success measures are preserved. Personal names, private workspace links, exact revenue targets, and claims that were not supported by post-release evidence are omitted.

It is intentionally a set of normal product documents, not a tutorial or a test fixture.

## Read it in this order

The example exists to show one chain, not five features:

1. [Strategy context](context/strategy.md) — who the product is for, the goal for the year, the ordered product principles, and the priority bands. Every document below was argued against this file.
2. [Initiative: Best-in-class trading experience](product/initiatives/best-in-class-trading-experience.md) — one company ambition turned into a single Product Bet with a shared Outcome Contract.
3. The five PRDs, each owning one barrier:
   - [Cross-chain Swap](product/prds/cross-chain-swap.md)
   - [Auto-slippage for Native Swaps and Bridges](product/prds/auto-slippage.md)
   - [Skip Signing Screen for Native Transactions](product/prds/skip-signing-screen-for-native-transactions.md)
   - [Transaction Toasters](product/prds/transaction-toasters.md)
   - [Bridge Progress Tracking](product/prds/bridge-progress-tracking.md)
4. [Learning: Segmentation found the failure the aggregate metric hid](product/learnings/auto-slippage-failure-rate.md) — the measured result for one of those barriers, and the decision that followed it.

## Where strategy actually changed the documents

The link between strategy and product work is the part that is easy to claim and hard to show. In this example it is checkable:

| Strategy line | What it decided |
|---|---|
| Trading is the largest revenue share | Execution reliability is argued as a revenue problem, not only a quality complaint — see the Auto-slippage **Why now** statement |
| **Reliable** outranks **Fast** | Skip Signing Screen removes a confirmation *only* when simulation and security checks are clean; the faster unconditional version was rejected |
| **Reliable** outranks **Fast** | Auto-slippage refuses to widen tolerance indefinitely, even though that would improve the success metric |
| **Power without noise** | Route and provider detail appears when it changes a decision, not as permanent ceremony |
| Prosumer, not beginner | No onboarding flow for Auto-slippage; the default is expected to just work |
| Competitive position vs. Phantom, Rainbow, Rabby | Cross-chain Swap is justified by a moving market baseline rather than by user requests |

## What this example does and does not prove

It shows the PRD format, the way several PRDs hold together through one Product Bet, the traceability from company strategy down to a requirement, and — for one barrier — the full path from evidence through a measured result to a recorded decision.

It is not an end-to-end runtime demonstration. The source snapshot came from the March 9–April 26, 2026 planning cycle, and most captured PRDs were draft/discovery documents. The example preserves the decisions being proposed at that point; it does not imply that every item shipped.

Auto-slippage is the exception, and it is deliberately the one that closes: it carries a real baseline, a real observed result, and a Learning. Even there the loop closes honestly rather than triumphantly. Execution-quality guardrail results were never recovered, so the contract's own decision rule cannot be fully evaluated and the recorded outcome decision is `iterate`, not `scale`. Everywhere else, proposed metrics and targets remain proposed.

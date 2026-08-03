---
updated: 2026-03-09
review_by: 2026-07-01
---

# Company and product strategy

> Historical context from real Zerion Wallet product work, reconstructed for this
> worked example. Exact revenue targets, internal links, and personal names are
> withheld; the structure and the decision content are preserved. This is the file
> the trading Product Bet was argued against.

## Positioning

**Who this product is for:** a prosumer — "crypto is a significant part of my life; I want one convenient, secure wallet that helps me earn more, stay ahead, and not lose money."

**What they are like:**

- two or more wallets, two or more chains, weekly usage, a year or more of experience
- meaningful money held in crypto
- trades, stakes, uses DeFi, interacts with dApps
- already tracks a portfolio outside any single wallet

**What frustrates them:** oversimplified UX, educational hand-holding, and artificial limits. They are knowledgeable and opinionated, care about speed, precision, and control, and will pay for quality.

**Who this product is not for:** beginners who need guidance over control, and institutional users who need scale, compliance, and collaboration.

## Goal for 2026

Breakeven. The wallet sustains itself regardless of market conditions.

| Parameter | Target |
| --- | --- |
| Company revenue | Withheld — the breakeven number for the year |
| Wallet revenue | Withheld — roughly double the prior year |

### Where value comes from

| Source | Share |
| --- | --- |
| Trading | Largest single share |
| Premium | Second |
| Perps | Material |
| MEV | Material |
| Other | Remainder |

Trading is the largest revenue line, which is why execution reliability is a revenue question and not only a quality question.

## Product principles

1. **Reliable** — a wallet you can trust with meaningful money. Core flows work every time, coverage extends to the assets and chains users actually hold, and risks surface before users get hurt.
2. **Fast** — never waste the user's time. Instant, predictable performance and short time-to-complete for swap, bridge, connect, and track.
3. **Power without noise** — serious capability without overwhelming the user. Clean UI, smart defaults, progressive disclosure instead of configuration.
4. **Futuristic** — agents and automation, but only once the first three hold.

The order is the point. When speed and reliability conflict in a review, reliability wins and the PRD says so.

## Explicit trade-offs

**We are:** opinionated about coverage — we support what is relevant rather than everything. Focused on the prosumer segment.

**We are not:** optimising for extra configurability, building for very advanced use cases, or supporting everything instantly at any cost.

## Priorities for H1 2026

| Band | Items |
| --- | --- |
| **MUST** | Security; error-free core flows; support; Premium; price alerts |
| **SHOULD** | Hardware wallets; Earn; limit orders; home revamp; search and explore; gasless (discovery); feed improvements |
| **COULD** | Gnosis Safe; privacy; token as a reward; offramp |
| **WON'T** | Other ecosystems; profiles; tax report |

## Competitive position

| Competitor | Their strength | How we differ |
| --- | --- | --- |
| Rabby | Pro features, security UI | Broader chain coverage, mobile-first |
| Rainbow | Design, Hyperliquid integration | Multi-chain depth, DeFi positions |
| Phantom | Solana-native, speed | True multi-ecosystem |
| MetaMask | Distribution, brand | UX quality, portfolio tracking |

## Quality bar

Quality is the primary growth lever, not a hygiene factor. The standard is a "zero bug mentality": fewer than 1% of users hitting errors in core flows, bugs fixed within a day or a week rather than scheduled for next quarter, and a personal response to every report. Marketing follows from fixed bugs and fast support rather than from feature lists.

## What every PRD must answer

- How does this serve the prosumer named in Positioning?
- How does it drive breakeven — directly through a revenue line, or through a named strategic effect?
- Which priority band does it belong to, and does it fit H1?
- Which product principle does it advance, and which one does it put under pressure?
- Which explicit trade-off does it approach or cross?

A PRD that cannot answer these is not blocked from existing. It is blocked from claiming strategic fit.

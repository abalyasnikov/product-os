---
updated: <YYYY-MM-DD>
review_by: <YYYY-MM-DD>
---

# Company and product strategy

<!--
Canonical path: context/strategy.md (workspace root, outside product/).

This is durable decision context, not a graph artifact: no stable ID, no schema,
no relationships. It answers one question for every product workflow — why should
this team act on this problem now?

Keep it to a single readable file. If it starts turning into a planning database,
it has stopped doing its job. Anything that changes weekly belongs in the delivery
system, not here. Record a review date and honour it; a stale strategy file is
worse than none, because agents will cite it with confidence.

Delete any section that does not change a decision in your context.
-->

## Positioning

**Who this product is for:** <the customer in one sentence, in their own words where possible>

**What they are like:** <2–5 concrete characteristics a reviewer could check against a real user>

**What frustrates them:** <what makes this segment churn or complain>

**Who this product is not for:** <the adjacent segment you deliberately decline>

## Goal for <year>

<The single outcome the company is organised around this year, in one line.>

| Parameter | Target |
| --- | --- |
| <company-level metric> | <target> |
| <product-level metric> | <target> |

### Where value comes from

| Source | Share |
| --- | --- |
| <revenue line or value driver> | <%> |

<!-- For non-commercial or internal products, replace with the value model that
decides trade-offs: adoption, retention, cost avoided, risk reduced. -->

## Product principles

<!--
Order matters. Unordered principles cannot resolve a conflict, and resolving
conflicts is the only thing a principle is for. When two principles disagree in a
PRD review, the higher one wins and the PRD says so explicitly.
-->

1. **<Principle>** — <what it means concretely; what it forbids>
2. **<Principle>** — <...>
3. **<Principle>** — <...>

## Explicit trade-offs

**We are:** <the deliberate choices, including unpopular ones>

**We are not:** <what you have decided not to optimise for, even when asked>

## Priorities for <period>

<!--
MoSCoW is used here as a commitment boundary, not a scoring exercise. WON'T is
the most valuable row: it is the one that lets an agent reject work that looks
reasonable in isolation.
-->

| Band | Items |
| --- | --- |
| **MUST** | <committed this period> |
| **SHOULD** | <expected, cuttable under pressure> |
| **COULD** | <only if capacity appears> |
| **WON'T** | <explicitly declined this period, with the reason if it is contested> |

## Competitive position

| Competitor | Their strength | How we differ |
| --- | --- | --- |
| <name> | <strength> | <deliberate difference, not a wish> |

## Quality bar

<The standard a change must meet before it ships, and the metric that proves it.>

## What every PRD must answer

<!--
This block is the reason the file exists. It converts strategy from a document
an agent may read into a check an agent must pass. Keep it short enough that it
is applied every time.
-->

- How does this serve the customer named in Positioning?
- How does it drive the goal above — directly, or through a named strategic effect?
- Which priority band does it belong to, and does it fit the current period?
- Which product principle does it advance, and which one does it put under pressure?
- Which explicit trade-off does it approach or cross?

A PRD that cannot answer these is not blocked from existing. It is blocked from
claiming strategic fit.

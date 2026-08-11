---
schema_version: 1
id: opportunity_01RCPT001
type: opportunity
title: The admin who owns the close cannot get receipts in without chasing people by hand
created_at: "2026-08-11T09:00:00Z"
updated_at: "2026-08-11T14:20:00Z"
authors: [product-lead]
relationships:
  signals:
    - signal_01RCPT001
    - signal_01RCPT002
    - signal_01RCPT003
    - signal_01RCPT004
  prd: prd_01RCPT001
evidence_ids:
  - signal_01RCPT001
  - signal_01RCPT002
  - signal_01RCPT003
  - signal_01RCPT004
evidence_quality:
  contradictions:
    - A single-admin workspace abandoned enforcement rather than wanting it automated, and would
      accept reminders only if they default to off.
    - The account with the sharpest pain has a finance function and sits in the stronger half of
      the compliance split, while the segment with the weakest compliance cares least.
    - The loudest account's own explanation for missing receipts is contradicted by support
      completion data, so the stated cause is unverified.
  coverage_gaps:
    - No cardholder has been interviewed, in a problem whose intervention targets cardholders.
    - Receipts attached to the wrong transaction have no analytics event, so that cluster cannot
      be sized.
    - Exempt transactions are not excluded from the compliance numbers.
    - The 4-6 hours per close is self-reported by one person and has never been observed.
decision_events:
  - id: decision_01RCPT001
    kind: opportunity
    choice: pursue
    decided_by: product-lead
    decided_at: 2026-08-11T14:20:00Z
    rationale: The cheapest available move against the retention goal, on narrow but real
      evidence. Taking it with the scope cut to what principle 1 allows - the system does the
      following-up, and we ship nothing that ranks employees, even though that is what the loudest
      account asked for twice.
    based_on_version: "1111111111111111111111111111111111111111"   # illustrative commit
    conditions:
      - statement: Talk to at least three cardholders before any requirement is treated as fixed.
        review_by: 2026-09-15
      - statement: The outcome must be measurable on the single-admin segment specifically,
          because the aggregate compliance number cannot show it.
        review_by: 2026-09-15
---

# The admin who owns the close cannot get receipts in without chasing people by hand

## Blocked value

Closing the month without spending hours acting as the company's collections department for its
own receipts.

## Affected users

Workspace admins accountable for the month-end close, most sharply the single-admin workspace named
in this year's positioning. Cardholders are affected as the recipients of any follow-up, and no
cardholder has been interviewed.

## Impact and urgency

**Impact:** one interviewed admin self-reports 4-6 hours per close on chasing alone. Receipt and
policy is 21% of Q3 support inbound and rising, and 51 of 88 such tickets are admins trying to hand
the chase to the support team. One Q3 churn named it in its exit call. The upper bound is unclear:
71% of missing receipts arrive within 30 days, so the recoverable value is the admin's time, not a
permanently missing ledger entry.

**Urgency:** the support trend is up 14% month over month while total volume is down 6%, and net
revenue retention sits at 96% against a 108% goal. None of that makes it urgent this quarter on its
own. It makes it the cheapest available move against the stated goal.

## Strategic fit

MUST band for H2 2026 — "remove manual work from the month-end close for the single-admin
workspace" — and it advances principle 2, the admin's hour is the unit of value.

It is under pressure from principle 1, automate the chase not the person. The two concrete asks
from the loudest account were escalation to a manager and a three-month ranking of the worst
offenders, and employee compliance ranking sits in this period's WON'T band. Principle 1 outranks
principle 2, so the version that removes the most admin work is not the version that can ship, and
the PRD has to say so rather than quietly optimising for the lower principle.

It also touches principle 3, no new habits for cardholders, because any reminder adds a step for
someone who did not choose this product.

## Evidence quality

**Source diversity:** four independent kinds of source in seventeen days — two customer interviews
with different roles, a support queue read-through covering 88 tagged tickets, and a self-serve
analytics query over 214 workspaces. No connector was involved; all four are local notes with
recorded fingerprints.

**Segment concentration:** heavily concentrated in workspace admins, and among those in two
accounts. The only broad source is the analytics query, and it is the weakest one. Nothing here is
first-hand cardholder evidence.

**Recency:** 22 Jul 2026 to 7 Aug 2026, with the support data covering one month and the analytics
window the trailing 90 days.

## Assumptions and risks

**Assumptions**

- Missing receipts are mostly forgotten rather than refused, so a timely prompt to the right person
  recovers them.
- The admin's hours go on identifying and contacting, not on judging edge cases.
- Cardholders will accept a small number of automated prompts without a support or morale cost.
- Admin seat count is a usable proxy for whether a workspace has a finance function.

**Risks**

- The intervention that most obviously removes admin work is the one the strategy forbids, so what
  ships may be materially weaker than what the loudest customer asked for.
- Chasing faster may move lateness earlier without changing the eventual 71% recovery rate,
  producing activity and no measurable win.
- A prompt about a transaction whose receipt is attached to the wrong transaction makes the
  existing confusion worse, and that cluster cannot currently be measured.

## Decision question

Should a Product Bet be pursued, held, or rejected?

The judgment: this is the cheapest available move against the retention goal, on evidence that is
real but narrow, and the most direct version of the solution is forbidden by the first product
principle. Pursuing it commits to finding an intervention that removes the admin's hours without
ranking or policing employees, and to accepting that it may only be provable on the single-admin
segment.

---
schema_version: 1
id: prd_01RCPT001
type: prd
title: The system runs the receipt follow-up instead of the admin
created_at: "2026-08-11T15:00:00Z"
updated_at: "2026-08-11T16:05:00Z"
authors: [product-lead]
relationships:
  opportunity: opportunity_01RCPT001
  signals:
    - signal_01RCPT001
    - signal_01RCPT002
    - signal_01RCPT003
    - signal_01RCPT004
evidence_waiver:
  assumption: Cardholders miss receipts because they forget, not because attaching one is hard or
    because they are refusing, so a timely prompt to the right person recovers the receipt.
  rationale: The Opportunity decision made three cardholder conversations a condition before
    requirements were fixed. They have not happened and the requirements below are fixed.
    Proceeding because the intervention is reversible per workspace and the decision rule treats a
    flat result as falsification rather than as a reason to iterate on cadence.
  risk: If the cause is friction or refusal rather than forgetting, this adds two messages per
    transaction for people who did not choose the product, damages the admin relationship the
    strategy is built on, and moves no metric.
  approved_by: product-lead
  approved_at: 2026-08-11T16:05:00Z
  review_date: 2026-09-15
---

# The system runs the receipt follow-up instead of the admin

## Problem

The admin who owns the month-end close is the only mechanism this product has for getting a missing
receipt in. The product detects the gap, flags the transaction, and stops. Everything after that is
human: export to CSV, filter, post in Slack, message people individually, repeat next month. One
interviewed finance lead does this for 4-6 hours per close. The single-admin workspace — the
customer this year's positioning names — does it worst, or gives up entirely.

**Why now / business reality:** net revenue retention is 96% against a 108% goal, receipt support
volume rose 14% month over month while total volume fell 6%, one Q3 churn named receipt chasing in
its exit call, and three accounts escalated it in the same quarter. This is the cheapest available
move against the retention goal; nothing about it is newly urgent this month.

## Evidence

[opportunity_01RCPT001](../opportunities/receipt-follow-up-is-unowned-admin-labour.md) and the four Signals beneath it: a finance lead's manual process
([signal_01RCPT001](../signals/finance-lead-rebuilt-chasing-outside-the-product.md)), 51 of 88 Q3 receipt tickets being admins asking support to chase
([signal_01RCPT002](../signals/support-tickets-are-admins-asking-us-to-chase.md)), compliance splitting 74% / 55% on whether more than one admin seat exists
([signal_01RCPT003](../signals/compliance-splits-on-who-owns-the-close.md)), and, as counter-evidence, a single-admin workspace that abandoned enforcement
and wants reminders off by default ([signal_01RCPT004](../signals/single-admin-workspace-gave-up-on-enforcement.md)).

Confidence: medium on the problem, low on the intervention.

Contradictions stay open rather than being averaged. The account with the sharpest pain sits in the
*stronger* half of the compliance split, while the segment with the weakest compliance cares least.
Coverage gaps unresolved at drafting: no cardholder interviewed; the stated cause of missing
receipts is second-hand and contradicted by support data; the wrong-transaction cluster cannot be
sized; and 71% of missing receipts already arrive within 30 days, so part of any target may be
lateness that resolves itself.

## JTBD

**Who:** the admin accountable for closing the month, in a workspace with 20-60 cardholders.

**When** the month I have to close contains transactions without receipts, **I want** the missing
ones to arrive without me contacting anyone, **so that** closing the month is a review rather than
a collections job.

## Current and desired journey

**Current:** transaction posts → policy flags it as needing a receipt → nothing happens → admin
notices at close → admin exports and filters → admin posts a list in Slack and messages people →
some receipts arrive → admin re-checks and repeats.

**Desired:** transaction posts → policy flags it → the cardholder is told by the product, on the
day and again a few days later → the receipt arrives before the close → the admin opens the close
and sees what is still open and why, without having contacted anyone.

## Scope

### Requirements

- A cardholder with a flagged transaction is notified by the product, without an admin acting, on a
  schedule the admin sets once. Default: day 1 and day 5 after the transaction posts.
- The notification takes the cardholder to that specific transaction and nothing else.
- A cardholder can answer "there is no receipt" with a reason, closing the item as
  resolved-without-receipt rather than leaving it open forever.
- The admin sees, in one view, which flagged transactions are waiting on a person and which have
  been answered — replacing the CSV export rather than supplementing it.
- Follow-up is on by default for new workspaces and off by default for existing ones, and can be
  switched off per workspace in one action.
- A cardholder never receives more than two automated messages about the same transaction.

### Non-goals

- No ranking, scoring, or comparison of cardholders, on any surface, including exports. This is the
  loudest customer ask in the evidence and it is out of scope by principle 1 and the H2 WON'T band,
  not by capacity.
- No escalation to a manager or to anyone other than the cardholder in this version. Manager
  escalation is the same mechanism as ranking with a smaller audience and needs its own decision.
- No change to how a receipt is captured, matched, or read. Mobile capture and the
  wrong-transaction problem are separate barriers.
- No policy engine changes: thresholds, categories, and exemptions stay as they are.
- Not a digest or a notification centre. One transaction, one message, one link.

## GTM hypothesis

**Audience:** existing workspace admins, single-admin workspaces first.

**Promise:** you will stop chasing receipts; the product will.

**Discovery channel:** an in-product prompt on the compliance view plus one lifecycle email to
admins. No launch campaign.

**Adoption action:** the admin turns follow-up on and does not turn it off within 30 days.

**Launch measurement:** share of eligible existing workspaces with follow-up enabled 30 days after
exposure, and the disable rate inside that window.

## Risks and dependencies

- The intervention may only move lateness earlier: 71% of missing receipts already arrive within 30
  days, so a faster prompt could produce activity with no change to what the admin does at close.
- Cardholder tolerance is unmeasured. Two automated messages per transaction across 35 cardholders
  is a new stream of product-generated mail, and the interviewed admin explicitly feared people
  would come to resent the tool and then her.
- What ships is weaker than what the loudest account asked for; she may read the absence of
  escalation and ranking as the problem not being solved.
- Depends on a per-cardholder notification channel that reliably reaches people who rarely open the
  app. Email deliverability to work addresses is an assumption, not a verified capability.
- Depends on the analytics events named in the Outcome Contract existing before exposure starts.
  They do not exist today.

## Open questions

- What actually stops a cardholder from attaching a receipt? No cardholder has been interviewed,
  and the whole intervention assumes forgetting rather than friction or refusal.
- Is the admin's time saved by receipts arriving earlier, or by not having to look? If it is the
  second, the metric below measures the wrong thing.
- Should resolved-without-receipt count as compliant? It is the honest answer for the admin and it
  inflates the number.
- Why 70% and not 62% or 80%? The target is asserted, not derived: it is the midpoint between the
  single-admin segment today and the multi-admin segment that already has a person doing this work.

## Outcome Contract

Better means the admin stops doing the chasing by hand and the receipts still arrive — measured on
the single-admin segment, where the problem is worst and where the aggregate number hides it.

```yaml product-os:outcome
definition:
  version: "receipt-follow-up-v1"
  method: behavioral_metric
  baseline: "55% median seven-day receipt compliance in single-admin workspaces with ten or more
    active cardholders, from an unreviewed self-serve query over 214 workspaces; the 62% aggregate
    across all workspaces is not the baseline and must not be used as one"
  target: "70% median seven-day compliance in the same segment, with no increase in
    receipt-related cardholder support tickets"
  metric: "share of transactions above the workspace receipt threshold with a receipt attached
    within seven days, per workspace, median across the segment"
  window: 30 days after follow-up is enabled for a workspace
  slices:
    - single-admin workspaces
    - multi-admin workspaces
    - workspaces that disabled follow-up
  guardrails:
    - receipt-related cardholder support tickets per 100 active cardholders
    - share of workspaces that disable follow-up within 30 days of enabling it
  decision_rule: "Scale only if single-admin compliance improves materially and neither guardrail
    regresses. If compliance improves but cardholder tickets rise, iterate on the message rather
    than the schedule. If compliance does not move, do not iterate on cadence - treat the
    forgetting assumption as falsified and return to discovery with cardholders."
binding:
  status: planned
  owner: product-lead
  due_before: release
```

The definition is honest about one thing it cannot do. This year's goal is stated in admin hours
per close, and no instrument for that exists. Compliance is a proxy chosen because it is
measurable, and the decision rule above does not let a compliance improvement alone be read as
hours saved.

## Delivery

Not handed off. No delivery connector is configured in this example, so the handoff workflow would
degrade to a local projection and report the missing capability as a named gap.

## Customer context

Two accounts carry most of the qualitative weight and want opposite things from the same feature: a
140-cardholder logistics SaaS on a growth plan (`account-logistics-saas-140`, renewal Feb 2027,
medium revenue band) and a 60-person design agency on the starter plan
(`account-design-agency-60`, low band, sole admin, already stopped enforcing policy). That is why
"off by default for existing workspaces" is a requirement rather than a rollout preference.

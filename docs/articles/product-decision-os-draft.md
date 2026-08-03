# How I Rebuilt Product Work Around Coding Agents

*A field report from Zerion: putting company strategy, evidence, product bets, PRDs, delivery, and learning into one system that both people and agents can read.*

For years at Zerion, a PRD felt finished when the Notion page was shared. I collected comments, updated the document, handed it to engineering, and then tried to remember who needed to hear about it when something changed.

That workflow was fine while LLMs lived in the browser. I pasted context into a chat, copied the output back into Notion, and did it again next session. Then models like Claude Opus made agent development practical, and the mismatch stopped being tolerable. An agent could reason across an entire codebase. The reasoning behind the product was still sitting in pages I had to find and paste by hand.

So I made a small move rather than a grand one: I put our product documents in Git, where the agents already worked.

Git turned out to change more than storage. It became a shared product interface: for PMs, for reviewers, for developers, and for their agents.

This is a field report, not a playbook. It worked in our environment because PMs and engineers were already working with coding agents every day. Examples come from real Zerion Wallet work, with private data, internal links, and personal names removed. Over time I turned the working model into [Product OS](../../README.md), an open-source reference implementation. It grew out of my experience at Zerion; it is not an official Zerion product or methodology.

## Git became our review system

I did not want to build another workflow with custom statuses, approval buttons, and a product-management UI to maintain. Git already had branches, pull requests, comments, approvals, and an immutable merged version. Every one of those had taken years to become boring and reliable.

PMs opened PRs for PRDs. As their manager, I reviewed them. We argued about the product decision in the PR, and the author updated the document. Agents could read the same comments and respond by changing the PRD, so I never had to open a separate AI interface just to translate review feedback into edits.

Merging mattered more than I expected. Once a PRD was merged, everyone — including agents — could point at the same immutable version. Later edits became a new review instead of a silent change to something we had already approved.

Delivery stopped aging the document, too. Developers added the product repository as a submodule in their codebase. We still had calls, and the submodule never replaced that human handoff; it removed a smaller, more persistent one between the developer and their coding agent. Nobody had to paste an old PRD into a prompt or remember that a requirement had moved last week.

Versioning solved drift. It did not solve judgment. Handing an agent the latest PRD is not much help if the agent cannot see why the company should want this work at all.

## The PRD template was the least important part

A template can make an agent fill in the right sections. It cannot make the decision underneath those sections any good. What actually did that work was the context sitting around the PRD.

We kept a compact strategy file in the Zerion repository: who the product was for, the goal for the year, where revenue came from, product principles, explicit trade-offs, competitive position, and the current priority bands. For the wallet, the principles were ordered — reliable first, then fast, then power without noise. Trading was the largest revenue line, and product quality was the primary growth lever.

Ordering is what made those principles usable. Unordered principles cannot settle an argument, and settling arguments is the only thing a principle is for. When speed and reliability collided in a review, reliability won, and the PRD had to say so out loud.

That file changed the questions an agent asked. A request stopped being evaluated on its own merits. Does it serve the customer we named? Does it move the goal? Which priority band is it in? Which principle does it strain?

Evidence explains why a problem might be real. Strategy context explains why this team should act on it now. Product OS keeps that as one readable file per workspace — deliberately one, because a strategy context that grows into a second planning database stops being read, and an unread strategy file is indistinguishable from having none.

## A company ambition became one Product Bet

Zerion had a broad objective: create a best-in-class crypto trading experience.

That sentence is too large to become a PRD. I started collecting the barriers standing between it and reality, and what struck me afterwards was how differently each one had surfaced:

- **Cross-chain Swap** came from the market, not from users. Nobody asked for it. Competitors had made single-intent cross-chain trading the baseline, and our journey still made people coordinate a bridge themselves.
- **Auto-slippage** came from support: transactions that looked ready to execute and then failed onchain. Analytics came later, and at first it argued the opposite.
- **Skip Signing Screen** came from inspecting our own flows and finding a confirmation that repeated information the user had already accepted.
- **Transaction Toasters** came from the same inspection: pending and success screens that blocked the rest of the wallet.
- **Bridge Progress Tracking** came from a dependency. Cross-chain Swap would be irresponsible to ship while long settlements stayed an ambiguous wait.

Five barriers, five different origins, one outcome. That mix is the argument for the structure. A system that only ingests user feedback would have found exactly one of these. A system that only follows strategy would have found a different one. Neither would have found the three that came from looking hard at our own product.

In Product OS, the unit that takes an investment decision and later produces a learning is a Product Bet. A small bet is a single PRD. A broad outcome becomes an Initiative when several independent barriers have to fall together, which is what this was.

Strategy shaped the bet rather than decorating it. Removing a duplicate confirmation served speed, but only conditionally: because reliability outranks speed, the signing screen is skipped only when simulation and security checks come back clean. The unconditional version would have been faster, and it was rejected on the strength of a principle order written down months earlier.

Shipping all five would still not prove the trading experience improved. The Initiative owns that aggregate claim; each PRD owns evidence that its own barrier is gone. Our [worked example](../../examples/best-in-class-trading-experience/README.md) keeps the whole chain intact, from the strategy file down to individual requirements.

## The metric that said there was no problem

Auto-slippage is the one I keep coming back to, because almost everything I believe about evidence is in it.

The signal came from users, not from a dashboard. People wrote in saying their trades were failing: they signed the transaction, the wallet accepted it, and it never landed onchain. Support had consolidated the repeated reports in Linear, and when we needed the raw signal we pulled the original Intercom conversations.

Then I checked it in Mixpanel, at the aggregate level, and the failure rate looked like noise.

That is the moment worth dwelling on. If I had stopped there, the honest answer — the defensible, data-backed, completely wrong answer — would have been that we did not have a problem, just a handful of vocal users.

So I decomposed it instead. I broke the transaction funnel down by stage, then segmented the failures by cause, by network, and by asset type and market cap. The last cut is where it appeared. For low-market-cap assets, roughly 15% of initiated trades were failing. The reason was not subtle once you could see it: we applied a largely static slippage tolerance to everything, and these assets move far more between quote and inclusion than majors do.

The fix was a tolerance adapted to asset characteristics, liquidity, and volatility instead of one global default. Failure rate in that segment went from about 15% to about 2%.

But between the diagnosis and the fix, review caught something. Reducing the failure rate is trivially easy if you are allowed to widen tolerance — you just accept worse prices on the user's behalf, watch the metric improve, and call it reliability. One review pass in February 2026 closed that door, and the change to the document was almost nothing:

```diff
- Fewer failed native swaps/bridges
+ Fewer failed native swaps/bridges while maintaining execution quality
```

Four words. The same commit added the guardrails that made them real: median execution delta against the quote, the share of trades whose effective slippage crossed a material threshold, and price-related support contacts, each with an acceptance criterion against control. It also deferred the high-slippage warnings to a later iteration, on the grounds that we should measure real execution delta before inventing thresholds for it.

Everything technical underneath kept moving after that. Classification rules changed. The calculation changed. A liquidity factor came and went. The product contract never moved again, because it had stopped being a statement about a number and become a statement about a trade-off.

## One number was hiding three problems

The same decomposition surfaced two more failure categories that had nothing to do with slippage. One was technical errors in the transaction builder. The other was users who held the stablecoin they wanted to trade but no native token for gas, which we addressed with gas sponsorship for eligible cases.

Three segments, three unrelated causes, three different interventions, and a single headline metric that showed none of them and would have argued against all three.

The sequence is what I kept. Qualitative signal told me where to look. Segmentation told me who was actually affected. Only then was there anything worth designing. An aggregate is not evidence that things are fine; often it is just evidence that you have not cut the data yet.

## The PRD stayed short enough to be read

That same PRD showed me where another line sits. Classification rules, coefficients, fallback algorithms: all important, none of them the durable product decision. They were engineering hypotheses wearing product clothing.

Long PRDs failed on our team for an unglamorous reason: people did not read them. So the format got compact. A PRD covered the user problem and use cases, the business reason to act now, the evidence, the desired journey, requirements, non-goals, risks, and the outcome we intended to observe. Competitor context appeared when it changed the decision, not as a market-research appendix nobody asked for.

Architecture, algorithms, API contracts, migrations, and rollout mechanics moved into an engineering-owned Implementation Plan living in the code repository. That split did two things. It kept the PRD readable, and it stopped an implementation detail from quietly redefining the product outcome.

Product safety bounds stayed in the PRD, though, and that distinction took me a while to get right. "Auto never exceeds 10%, manual caps at 25%" is a promise to the user. The rule deciding where a specific trade lands inside those bounds is engineering's business.

GTM went through the same reconsideration. It is not equally urgent for everything: a straightforward reliability fix rarely needs a launch strategy. But for anything new, GTM cannot wait until the build is done. Who discovers this, what promise makes them try it, and which adoption action counts are questions that change the feature itself. Build first and invent distribution later, and you usually ship dead weight.

## I stopped ending the process at handoff

My old workflow had one more structural problem: it ended at the engineering handoff. Product OS follows the decision further.

```text
evidence
  → opportunity
  → product bet
  → PRD + Outcome Contract
  → delivery
  → measurement
  → learning and next decision
```

Git holds the artifacts and the decision trail. Everything else keeps its natural job: transcript providers own full interviews, Linear owns delivery, analytics systems own behavioral data, code repositories own implementation plans. An agent connects them and brings the next decision to a human.

Three judgments stay human. Whether to pursue an opportunity. Whether to approve the bet. What to do once the result is in. An agent can investigate, draft, compare, and recommend — it does not get to make those three calls quietly.

## GitHub is useful, and still a barrier

The operating model worked. Its interface did not work equally well for everyone.

GitHub is a technical tool. PMs already living in coding agents adapted in days. Designers and other collaborators needed help, and I gave it to them through Loom walkthroughs, live demos, and time in Claude Cowork and Claude Code. The curve got shorter. It never went away.

That is the trade-off I would name honestly to anyone considering this: you get a review system nobody has to build and a context store agents can read, and you pay for it with an interface that excludes part of your team by default.

It also convinced me the agent, not GitHub, should be the front door. A PM should be able to ask "what decision needs my attention?" or "interrogate me before I draft this PRD" without learning an artifact graph or hand-editing YAML.

## What I have proved, and what I have not

I should be precise about which parts of this are load-bearing.

The system I ran at Zerion was real. It handled live Linear, Notion, Mixpanel, and support workflows, and the examples in this article come out of that work.

Product OS, the open-source reference implementation, is a different claim. Its V1 is complete and deterministically verified: artifacts, relationships, immutable decisions, version boundaries, installation integrity. What I have not yet done is re-run it against live MCP flows, calibrate its model-quality evaluation, or pass the public one-link installation check.

There is a smaller admission inside the Auto-slippage story too. We closed the primary metric convincingly and never closed the guardrails: the execution-quality results the review had insisted on were not in hand when the work was declared done. By its own decision rule that contract does not permit a "ship it and scale" conclusion, only "keep going and finish the evidence." Writing the rule down is what makes that gap visible instead of comfortable, which is the entire argument for writing it down.

## The shift is bigger than moving Markdown into Git

Better PRD templates were not the answer, and neither was relocating Markdown into a repository. Value came from the chain: company context, evidence, a Product Bet, delivery, and eventually a learning that changes the next decision.

Setup is meant to be agent-native. You hand Codex, Claude Code, or another capable agent a commit-pinned `INSTALL.md` link and an existing private repository. It verifies the source, previews the plan, installs the skills and schemas, and asks before writing anything. Forking is for people who want to change Product OS itself; a product team should install it into its own private workspace, where its strategy and evidence belong.

My transferable lesson is narrower than "move every product team to Git." If your team already works with coding agents, product context should not arrive as a one-off prompt. Put strategy, evidence, and decisions where both people and agents can review them. Let Git preserve what you decided. Let the agent carry that decision into delivery and back into learning.

That is what changed for me. The PRD stopped being the end of the product process and became one versioned contract inside a loop that keeps running.

The repository is here: **[Product OS repository: add public URL]**.

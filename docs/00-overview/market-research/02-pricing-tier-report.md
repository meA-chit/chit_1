# Tier-based pricing report

- Date: 2026-10-07
- Status: **Hypotheses to test, not decisions.** Prices are anchors from public competitors and have not been tested with any Chit household. Currency is EUR for Chit tiers (Germany-first), USD for US competitors as published.
- Inputs: [`01-market-research-report.md`](01-market-research-report.md) (findings F1–F10), [`../open-decisions.md`](../open-decisions.md), ADR-0009 (hub-first, hosted profile), ADR-0007 (no auth yet)
- Companion: [`03-missing-feature-analysis.md`](03-missing-feature-analysis.md)

## 1. What the market tells us about pricing

### 1.1 Price anchors

| Product | Hardware | Recurring | Notes |
|---|---|---|---|
| Skylight Calendar (15") | from about $299.99 (range $219–$599 by size) | **Plus $79/yr**, first month free *(an older snippet quoted $39/yr; the vendor page now says $79)* | Plus holds photos, meal planning, Magic Import, rewards, Disney mode. Free tier keeps calendar sync, task manager, colour coding, lists. |
| Hearth Display | about $600–$700 | about $6/mo (about $108/yr) *(sources vary; unverified)* | Premium-priced anchor. |
| DAKboard / Mango Display | uses your own screen | about $5/mo | The "bring your own screen" price point. |
| FamilyWall Premium | none | €39.99/yr or €4.99/mo (Germany); $44.99/yr, $7.99/mo (US) | Budget, meals, documents, location, sync. 30-day trial. |
| Cozi | none | Gold tier exists *(price not verified)* | Free tier cut to 30 days ahead; ads. |
| Splitwise Pro | none | about $5/mo, $40/yr | Free tier capped at about 3–5 expenses a day. |
| Honeydue | none | Free | Couples' selective sharing. |
| Monarch / YNAB / Copilot | none | $99.99/yr / $109/yr / $13/mo per person | Bank-sync budgeting; heavy users. |
| Greenlight | debit card | $5.99–$14.98/mo | Chores plus real money. |
| BusyKid | debit card | about $4/mo per family | Lowest quoted. |
| Home Assistant | your own server | Free (Nabu Casa cloud about $65/yr *(unverified)*) | The free-DIY anchor for the technical segment. |

### 1.2 Willingness-to-pay signals (what users actually reward and punish)

| Signal | Evidence | Pricing rule for Chit |
|---|---|---|
| People pay $40–$110 a year when the product visibly saves effort | Skylight Plus, FamilyWall, Monarch, YNAB all have paying bases | A household subscription in the **€40–€100/yr** band is conventional; an annual price below Skylight's $79 is a reasonable opening position. |
| People are angry when something they relied on gets gated or removed | Cozi's 30-day free cut; Skylight photos stopping on lapse; Splitwise daily cap (F1) | **Never gate the core daily loop** (calendar view, chores, reminders, the shared screen). Lapse must degrade gracefully and be disclosed at purchase. |
| Hardware plus subscription feels double-charged | "Buying a car and paying annually to roll down the window" | If a hardware kit exists, include a Plus period in it and say plainly what stops on lapse. |
| Per-seat and per-child limits breed resentment | Cozi/Splitwise-style caps; OurHome invite friction (F1, F7) | Price per **household**, not per member or per child. |
| Marginal-cost features are the defensible paywall | Skylight Magic Import (AI parsing) is paid; Splitwise OCR is paid | Gate features with real running cost: AI parsing, bank-sync aggregation, cloud relay, hosting, backups. |
| Technical users will not pay for what they can self-host | HA community prefers local, free, open | The free tier must be a complete, self-hosted product. |

## 2. Pricing principles (proposed)

1. **Core is free and local.** The household overview, planner, chores, reminders and the shared screen work offline with no subscription. This is also what the product principles promise (local-first, graceful absence).
2. **Charge for cost and convenience, not for the data.** Paid features are those that cost money to run or remove effort: automatic capture, remote access and push, encrypted off-site backup, bank connection, hosted hub.
3. **One price per household.** No per-member, per-child or per-calendar caps.
4. **Say what stops on lapse.** A lapsed Plus must leave data intact and exportable, with a clear list shown before purchase.
5. **Annual-first, monthly available.** Anchor on yearly price; show monthly at about 20–25% premium.
6. **Hardware is optional and not a profit centre early on.** Bring-your-own screen first; a kit only if setup friction (F5) blocks adoption.

## 3. Proposed tiers

### Tier overview

| | **Chit Home** | **Chit Plus** | **Chit Money** | **Chit Cloud** |
|---|---|---|---|---|
| Positioning | Complete local household overview | Remove effort, reach it from anywhere | Add shared finance | We run the hub for you |
| Who | Self-hosters, HA households, anyone with an always-on device | Mainstream planner parent (S-A), kids with phones away from home Wi-Fi | Couples, flatmates, families (S-D) | Households with no always-on device |
| Price to test | **€0** | **€49/yr** (test €39–€69); €5.99/mo | **+€39/yr** on Plus (test €29–€59), i.e. about €88/yr total | **€12.99/mo** (test €9.99–€14.99), includes Plus |
| Hardware | Own PC / Pi / mini PC; own screens | same | same | none |

### What goes where

| Capability | Home | Plus | Money | Cloud |
|---|:-:|:-:|:-:|:-:|
| Household, members, avatars, settings | ✔ | ✔ | ✔ | ✔ |
| Calendar feeds (ICS), weather, timeline, chores with streaks, reminders, skips | ✔ | ✔ | ✔ | ✔ |
| Shared screen, screen-safe mode, data-state labels | ✔ | ✔ | ✔ | ✔ |
| Kids: school-day plan, stars and goals, homework, grades, kid phone app on the home network | ✔ | ✔ | ✔ | ✔ |
| Devices: Home Assistant read-only connector | ✔ | ✔ | ✔ | ✔ |
| Energy: one tariff provider plus one inverter; best-window suggestions | ✔ | ✔ | ✔ | ✔ |
| Energy: more providers, appliance-aware planning, cost-saved reporting | | ✔ | ✔ | ✔ |
| **Smart Import** (email, PDF, photo, chat text to calendar and to-dos; review before saving) | | ✔ | ✔ | ✔ |
| **Remote access and push notifications** (kids and parents away from home Wi-Fi) | | ✔ | ✔ | ✔ |
| **Encrypted off-site backup** and restore | | ✔ | ✔ | ✔ |
| **Weekly household digest** ("what needs attention") | | ✔ | ✔ | ✔ |
| Shared expenses, settle-up, recurring bills, goals (manual entry) | ✔ (basic) | ✔ | ✔ | ✔ |
| **Bank connection** via open banking, budgets, per-person privacy | | | ✔ | add-on |
| Multiple households (separated parents, grandparents) | | | ✔ | ✔ |
| Managed hosting, updates, monitoring | | | | ✔ |
| Support | Community | Email | Email | Priority email |

Design choices and why:
- **Basic shared expenses in Home.** Splitwise's daily-cap backlash (F1) is an open door. A split-and-settle tool with no cap, no ads and local data is a credible acquisition wedge for couples (S-D), and costs almost nothing to run. Bank connection, which has per-account aggregator fees, is what is charged for.
- **Kids' phone app stays on the home network in Home.** Gating it would hit the most emotionally loaded feature in the product. Push and remote access cost money and belong in Plus.
- **Energy basics free.** The energy wedge (F8) is how Chit reaches S-B and S-C. Provider breadth (Tibber is the only provider today; Octopus Agile, aWATTar and Nordpool are the obvious next ones) is a natural Plus lever once more than one exists.

### Hardware and bundles (optional, test only if setup friction proves to be the blocker)

| Offer | Price to test | Anchor |
|---|---|---|
| **Hub kit:** pre-flashed Pi-class hub, storage, case; includes 12 months of Plus | €149–€199 one-time | Skylight Calendar from $299.99 with Plus included; our kit has no screen |
| **Screen bundle:** hub plus partner 15" display, mounting, 12 months of Plus | €329–€379 | Skylight 15" from $299.99; Hearth about $700 |
| **Bring your own screen** (the default) | €0 | DAKboard/Mango at about $5/mo on any screen |

### Partner and channel ideas (hypotheses, not prices)
- **Energy-supplier or installer partnership** (Tibber, Octopus, local solar installers): co-branded "household energy view", per-household licence or referral fee. Matches F8 and the German growth in dynamic tariffs, but needs a conversation, not a spreadsheet.
- **School or club feeds** are a content partnership rather than a revenue line. They would reduce Smart Import cost by providing clean feeds.

## 4. Why this shape (and what it rejects)

| Choice | Alternative rejected | Reason |
|---|---|---|
| Free complete local product | Free trial of everything, then paywall | Trial-then-paywall is the pattern that produced the Cozi and Skylight backlash (F1). Technical users, who are Chit's likeliest first adopters, would not tolerate it. |
| Price per household | Per member / per child | Per-seat limits are a named irritant; kids and grandparents should join freely. |
| Charge for Smart Import | Give it away free | It has real recurring cost (model usage) and is the feature Skylight already monetises at $79/yr. Our cheaper price is a deliberate wedge. |
| Money tier separate from Plus | Include finance in Plus | Bank connection has per-account cost; not every household wants finance; and finance is where separated privacy and regulation risk concentrates (open aggregator terms, data-protection impact). Keep it separable so it can fail without sinking Plus. |
| Hosted tier at a higher price | Subsidised hosting | ADR-0009 gives one container per household, so cost scales per household. A subsidy is a margin leak. |
| No real-money allowance (kids' debit card) | Greenlight-style card | Needs a regulated card programme and licensed partner. Stars and goals are our scope; a payout integration could be a later partnership. |

## 5. Preconditions and dependencies (these gate when anything can be sold)

| Tier or feature | Blocked by | Reference |
|---|---|---|
| Any paid tier | A billing and entitlement design, and an identity design. There is **no authentication** today. | ADR-0007; open decision 2 |
| Remote access and push | Identity, HTTPS, a relay design | ADR-0007, ADR-0012 follow-ups |
| Smart Import | A privacy design for reading email or documents, and a decision on cloud models vs local models | `non-negotiable-rules.md`; product principle 3 |
| Chit Money | Data-protection decisions, open-banking aggregator choice, per-person privacy | roadmap "Households beyond families" gate |
| Chit Cloud | Hosted profile hardening and a cost model per household | ADR-0009 |
| Hardware kits | Supply, support and returns; only after the setup-friction test | n/a |

Practical consequence: **Home is the only tier that can launch on the current build.** Everything else is a roadmap gate, which is also the reason to keep prices as hypotheses.

## 6. How to test the prices (before building billing)

| Step | Method | Sample | Outcome |
|---|---|---|---|
| 1 | **Van Westendorp** price sensitivity, framed on the Plus bundle | 30+ per segment (S-A, S-B, S-D) | Acceptable range for €/yr |
| 2 | **Gabor-Granger** on 3 price points (€39, €49, €69) | same respondents | Demand curve and revenue-maximising price |
| 3 | **Feature-value ranking** (MaxDiff) on the capability list in section 3 | 100+ if possible | What is worth paying for, replacing our judgement |
| 4 | **Fake-door landing pages**: with vs without "runs on your own hardware, data stays home" | paid or community traffic in Germany | Whether local-first lifts or hurts conversion (F10) |
| 5 | **Concierge pilot**: 5–8 households use Chit for 8 weeks, then are offered Plus | pilot households | Real willingness-to-pay and what they miss most |
| 6 | **Churn-trigger interviews** with people who left Skylight or Cozi | 10 | Exact paywall tolerance thresholds |

Decision rules to agree in advance (suggested): proceed with a paid tier only if at least **20% of concierge households** say they would pay at the tested price **and** the Smart Import unit cost per household per month is under **20% of monthly Plus revenue** at expected usage. Both thresholds are placeholders to be set by the product owner.

## 7. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The segment that loves local-first will not pay, and the segment that will pay does not want to host | High | High | Hosted tier and the hub kit; treat Home as the community and acquisition engine |
| Smart Import costs more than Plus revenue | Medium | High | Usage caps per month, local or small models for common formats, review-before-save to reduce retries |
| Skylight or Cozi respond with price cuts or free tiers | Medium | Medium | Do not compete on price alone; compete on openness, energy, kids' school data and privacy |
| Finance regulation and data-protection overhead | Medium | High | Keep Money separable; start with manual and shared expenses; defer bank connection |
| Tibber or another supplier changes API terms | Medium | Medium | Multi-provider connector contract (ADR-0011); do not hard-wire revenue to a single supplier |
| Pricing in EUR is wrong for the US | n/a | Medium | Decide launch geography first (open decision) |

## 8. Recommendation

1. Commit to **Home (free, complete, local)** as the launch tier and make it genuinely good: that is what the current build can deliver.
2. Plan **Plus at about €49/yr** as the first paid tier, built around **Smart Import, remote access with push, and backup**, because those are the features users want most (F4) and are the ones that cost money to run.
3. **Do not build billing yet.** Run steps 1–5 of section 6 first, in parallel with the identity ADR, so price and design mature together.
4. Treat **Money** and **Cloud** as options to open only after Plus shows demand.

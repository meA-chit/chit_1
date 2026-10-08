# Market research report: Chit vs the family-organiser and smart-home market

- Date: 2026-10-07
- Status: **Directional** (level 8 in the `AGENTS.md` source-of-truth order). It does not change scope. It is input to roadmap and story decisions.
- Companion reports: [`02-pricing-tier-report.md`](02-pricing-tier-report.md), [`03-missing-feature-analysis.md`](03-missing-feature-analysis.md), [`04-kids-module-research.md`](04-kids-module-research.md)
- Extends [`../market-synthesis.md`](../market-synthesis.md), which covered only Skylight and Home Assistant.

## 1. How to read this report (evidence limits)

This is desk research, not customer research. Please weigh it accordingly.

| What we used | What we did not have |
|---|---|
| Public app-store, Trustpilot and review-aggregator summaries (Skylight, Cozi, Splitwise, FamilyWall, Greenlight, BusyKid, Honeydue, Monarch) | Raw review counts per theme. Themes are ranked by how consistently they recur across sources, not by a counted sample. |
| Home Assistant community threads and Reddit-derived summaries | Direct Reddit access. r/skylightcalendar data came from a search summary (about 11k members). |
| Vendor pricing pages (Skylight) and pricing roundups (others) | Verified current prices for every vendor. Items marked *(unverified)* need a second look. |
| Trade and market-sizing press | Reliable market sizing. Third-party figures below vary by orders of magnitude and are for orientation only. |
| Our own docs and code at commit `18df403` plus working tree on `devs` | Any Chit user interviews. No Chit household has used it other than the owner's. |

**Geography.** The search tooling is US-weighted. European evidence is thinner: German FamilyWall pricing, Octopus and Tibber adoption, GDPR-flavoured alternatives. Treat EU conclusions as hypotheses to confirm with local interviews (Germany first, given the German grading scale in the kids module).

**Confidence labels** used below: **High** = recurs across three or more independent sources. **Medium** = two sources or one strong one. **Low** = single or indirect signal.

## 2. Market map

Chit sits across five product categories, and nobody in the market spans all of them. That is both the opportunity and the risk: Chit is compared against the best product in each category, not against a category of one.

| Category | Examples | What they sell | Typical price |
|---|---|---|---|
| A. Family display hardware plus app | Skylight Calendar, Hearth Display, Mango Display, DAKboard, NestBoard | A glanceable wall screen: synced calendar, chores, meals, photos | Device $219–$700 plus $39–$108/yr; DAKboard about $5/mo on your own screen |
| B. Family organiser apps | Cozi, FamilyWall, plus AI newcomers (Goldee, Carly, Nori, Ohai) | Phone-first shared calendar, lists, messaging, and (AI newcomers) email-to-calendar | Free tier with ads; FamilyWall Premium €39.99/yr in Germany ($44.99/yr US) |
| C. Kids' chores and money | Greenlight, BusyKid, GoHenry, OurHome | Chores that earn allowance, often with a debit card | About $4/mo (BusyKid) to $5.99–$14.98/mo (Greenlight) |
| D. Shared-money apps | Splitwise, Tricount, Honeydue, Monarch, YNAB, Copilot | Split expenses or share a budget | Honeydue free; Splitwise Pro about $40/yr; Monarch $99.99/yr; YNAB $109/yr |
| E. Smart-home and energy dashboards | Home Assistant (+ Forecast.Solar, Solcast, Tibber, Nordpool blueprints), Octopus and Tibber apps | Local control, energy dashboards, dynamic-tariff automation | Free DIY; tariff apps are free to customers |

Chit's module map (household, planner, kids, energy, devices, finance) deliberately mixes A, B, C, D and E behind one local-first hub. Nobody sells that bundle. Whether *households* want that bundle is untested.

Orientation figures (low confidence, vendor-reported market reports): a "family calendar apps for kids" market of about $1.2B in 2025 growing about 8.5% a year, and a broad smart-display market growing much faster. We would not use either in a plan.

## 3. What users are actually saying (synthesis)

Ten findings, ordered by frequency and impact. Each is traceable to sources in section 9.

### F1. Paywalls on features people already consider basic cause the most visible anger. (High)
- Skylight: photo display, rewards and meal planning moved behind Plus, and photos stop displaying when the plan lapses without that being clear at purchase. One Trustpilot reviewer likened it to "purchasing a car and paying annually to roll down the window." (Paraphrase of a reviewer comparison; see source S3.)
- Cozi: the free calendar was cut to the next 30 days with about a week's notice, which users called "virtually useless." Ads are described as intrusive. (S2)
- Splitwise: a daily cap of roughly three to five expenses on free accounts, plus receipt scanning and charts behind Pro, sent users hunting for alternatives. (S6)
- **Implication:** users accept paying, but they punish *taking away* or *gating the thing that is the product*. Pricing must gate costly extras, never the core loop.

### F2. Sync reliability is the make-or-break trust issue for calendar products. (High)
- Skylight users report Google events not appearing and deletions from the device failing, forcing a return to the phone. Cozi reviews cite slow loading, glitches and inconsistent sync. (S1, S2)
- **Implication:** a read-only ICS reader that "ignores `RRULE`, treats floating times as UTC, caps at 100 events and fetches on every request" (Chit's own gaps 4 and 5 in `docs/core/current-implementation.md`) would fail exactly this test on day one. Recurring events are most family events.

### F3. The person who builds the system loves it; everyone else ignores the screen. (High, strongest in Home Assistant)
- HA community: tablets "getting dust"; spouses "never use the HA app"; family members want to know "is something wrong, is something coming up, did something finish." The thread argues for notification-first design over browse-and-click dashboards. (S7)
- **Implication:** the stated Chit principle "explainable attention" and "needs attention cards" is the right bet, but it is currently the *last* pilot phase. The WAF (spouse acceptance) test is the real product test.

### F4. Parents want information captured *for* them, not another place to type. (High)
- The most requested feature in the mental-load tools is turning school and club emails, PDFs, newsletters and chat threads into calendar events and to-dos automatically. Skylight monetises this as "Magic Import"; start-ups (Goldee, Carly, Nori) exist purely for it. (S8, S9)
- Couples apps show the same pattern: manual entry fatigue is why partners stop updating. (S5)
- **Implication:** manual-entry-first products decay. Chit's kids and finance modules are mostly manual entry today.

### F5. Setup and cost friction decides who even gets started. (High)
- Skylight is "plug in and it works" at $219–$599 plus $79/yr. Hearth is about $700 plus a monthly fee. DIY Home Assistant is free but needs an enthusiast. Mango and DAKboard win people who want to reuse a screen they own. (S4, S7)
- Skylight's own community lists "Feature Request: API" among its recurring topics (8 posts) and "Regret" posts (6). (S1)
- **Implication:** Chit has a dead zone between "plug in" and "build it yourself." A household hub on a Pi or mini PC is better than HA for non-experts only if setup is genuinely short.

### F6. Couples want visibility without losing autonomy. (Medium-High)
- Roughly 60% of couples' accounts are shared at some level and 40% are not (single source, S5). Honeydue's selective sharing is its selling point. Credential-sharing reluctance (linking bank accounts to third parties) and low setup friction recur.
- Splitwise-style tools win on *settling up*, not budgeting.
- **Implication:** "per-person privacy" is a feature people explicitly choose products for, and fits Chit's ADR-0005 and the "sensitive" privacy class.

### F7. Kids' apps split into "chore stars" and "real money", and parents pay for the second. (Medium)
- Greenlight ($5.99–$14.98/mo, 4.8 stars with 440k+ ratings) and BusyKid (about $4/mo) bundle chores with a debit card. OurHome's reviews mention invite and onboarding failures. (S10)
- Skylight keeps the rewards system behind Plus. Chit's stars, goals, grades, homework and medication are shipped but not attached to money.
- Parents also worry about their children's data even while sharing it (survey of 75 parents, S11).
- **Implication:** star-based rewards are a commodity; the distinctive part of Chit's kid app is the *school-day plan, grades, homework and tests* in a parent-controlled, local-first frame.

### F8. Dynamic electricity tariffs give people a real, repeating job, but the tooling is expert-only. (Medium)
- Octopus Agile in the UK (250k+ customers in early 2026), Tibber in Germany, the Nordics and the Netherlands, and aWATTar in Austria and Germany are growing. Octopus reports over one million customers in Germany. Households often just "remember to defer the wash." (S12)
- HA's solar-forecast ecosystem has friction: Solcast cut new-account API calls to 10 per day, and users compare forecast accuracy between vendors. (S13)
- **Implication:** a family-readable "run the dishwasher at 13:00" card is genuinely useful and not served well by anyone outside HA YAML. Chit supports **only Tibber** and **only SolarEdge**, and neither has been exercised against a live account.

### F9. Meal planning, grocery lists and shared lists are table stakes in the organiser category. (High)
- Present in Skylight, Cozi, FamilyWall, Hearth and Mango. Missing sorting and repeating chores are named complaints in Cozi reviews. Self-hosters pair HA with Grocy and Mealie for the same job. (S2, S4, S14)
- **Implication:** Chit has none. Whether to build or integrate is a strategy call (see report 3).

### F10. Privacy and local-first are a preference for a minority and a trust tiebreaker for others. (Medium, Low in EU sizing)
- HA users explicitly prefer "no cloud dependency, works offline, private data" (Grocy, Mealie). Monarch's data collection is criticised. GDPR-friendly OpenFamily and Donetick exist because of this demand. (S5, S14, S15)
- Skylight "requires an ongoing Wi-Fi connection." (market-synthesis.md)
- **Implication:** local-first is a real differentiator for the technical early adopter and a credible EU trust claim, but there is no evidence yet that mainstream families will pay extra for it. Do not make it the *only* reason to buy.

### What we did **not** find
- No evidence that households want a *single* app for energy, kids, chores and money. Every competitor stays in one lane. This is the largest unvalidated assumption in the product.
- No evidence on shared-screen sensitivity (hiding names or medicines on a TV) as a purchase driver. It is a principled design choice, but not an observed user demand.

## 4. Segments (behavioural, evidence-linked)

| Segment | What they do today | What they would hire Chit for | Evidence strength |
|---|---|---|---|
| **S-A Overloaded planner parent** (mainstream) | Skylight/Cozi/Google Calendar plus group chats | "Make school and club chaos appear on one screen without me typing it" | High (F2, F4, F9) |
| **S-B HA-literate household** (early adopter) | HA with calendars, Tibber/Forecast.Solar, a tablet that gathers dust | "A family-readable layer above HA that my spouse will actually look at" | High (F3, F8, F10) |
| **S-C Dynamic-tariff solar household** (EU wedge) | Tibber/Octopus app plus inverter app | "Tell me when to run things" | Medium (F8) |
| **S-D Couples and flatmates** | Splitwise, Honeydue, spreadsheets | "Share what I choose, settle up, no paywall cap" | Medium (F1, F6) |
| **S-E Parents of 10+ kids with phones** | Greenlight/BusyKid, Google Family Link, school portals | "My child sees their own day, I control what" | Medium-Low (F7) |

S-A is where the money is; S-B and S-C are where Chit's current build is strongest. This tension drives the recommendations.

## 5. Chit today (verified from the repo, 2026-10-07)

| Area | State | Source |
|---|---|---|
| Hub, shell, React client, encrypted SQLite, module registry | Working; loopback only | `docs/core/current-implementation.md` |
| Household setup, members, avatars, commute | Working | same |
| Planner: calendar agenda (ICS feed), weather (Open-Meteo), timeline, recurring chores with streaks, reminders, skips | Working, calendar with known gaps | same |
| Per-child calendar links (school, care, sport) and regular weekly activities with commute | Working; feeds ignore `RRULE`; activities are weekly only; no in-app event creation (checked in code, 2026-10-07) | household setup, `calendar_sources`, `child_activities` |
| Energy: Tibber hourly price and consumption, SolarEdge production, expected-solar estimate, best-two-windows suggestion | Built; **not exercised against live accounts** | same, gap 3 |
| Devices: climate card | **Demo data**; no Home Assistant connector yet | same, gap 11 |
| Kids: stars and goals, grades (German scale), school-day plan, medication, homework and tests, kid phone app (PWA with QR plus code pairing and isolated gateway) | Built; phone flow verified on desktop only | ADR-0012, kid-phone memory |
| Finance | **Structure only**, no code | module manifest |
| Authentication | **None**; loopback single-owner pilot | ADR-0007 |
| Messaging, AI import, push, remote access, meals, lists, photos | Not built | n/a |

## 6. Scorecard: Chit vs the market, rated against what users want

Method: for each user want (rows), **Weight** = how strongly the evidence says users care (1–5; High-confidence themes score 4–5). Each product scored 0–5 on how well it serves that want today (0 absent, 1 planned only, 2 partial or demo, 3 solid, 4 strong, 5 best in class). Competitor scores are our reading of public features and reviews, not hands-on testing. Weighted score = Σ(weight × score) ÷ Σ(weight × 5).

| # | User want | Wt | Chit | Skylight | Cozi | FamilyWall | Home Assistant DIY |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | Calendars that sync reliably, including recurring events | 5 | 2 | 3 | 2 | 3 | 3 |
| 2 | Auto-capture of school and club info (email, PDF, photo) | 5 | 0 | 4 | 0 | 1 | 0 |
| 3 | Glanceable shared screen the whole family will look at | 5 | 3 | 4 | 2 | 2 | 2 |
| 4 | Proactive "needs attention" over browse-and-click | 4 | 1 | 2 | 1 | 2 | 2 |
| 5 | Fair pricing, no paywall on core use | 4 | 4 | 2 | 2 | 3 | 5 |
| 6 | Quick, low-effort setup | 4 | 2 | 5 | 4 | 4 | 1 |
| 7 | Chores with rewards for kids | 3 | 3 | 4 | 2 | 2 | 1 |
| 8 | Kid-facing phone view with parent control | 3 | 3 | 2 | 1 | 2 | 0 |
| 9 | Meal planning and grocery and shared lists | 4 | 0 | 4 | 4 | 4 | 3 |
| 10 | Shared money: split, settle, budget with per-person privacy | 3 | 0 | 0 | 0 | 2 | 0 |
| 11 | Dynamic-tariff and solar guidance in plain language | 3 | 3 | 0 | 0 | 0 | 3 |
| 12 | Local-first privacy and data ownership | 3 | 5 | 1 | 1 | 1 | 5 |
| 13 | Extensibility, API, integrations | 2 | 2 | 1 | 1 | 1 | 5 |
| 14 | Works on any screen the family owns | 3 | 2 | 1 | 4 | 4 | 4 |
| 15 | Trustworthy labelled data (measured vs forecast vs manual) | 2 | 5 | 1 | 1 | 1 | 3 |
| | **Weighted score (out of 100)** | | **43** | **51** | **35** | **45** | **47** |

Reading it:
- Chit is mid-pack: within a few points of FamilyWall (45) and Home Assistant DIY (47), and about 8 points behind Skylight (51), at pilot stage and with no marketing. It gets there by winning the rows nobody else is competing on (11, 12, 15) and being credible on 3, 7 and 8.
- Chit loses decisively on the two highest-weight mainstream rows (1 and 2). Those are the first rows a mainstream buyer tests. Closing rows 1, 2 and 9 to a score of 3 would lift Chit to about 55, above every product scored here.
- Home Assistant users are the segment where Chit's value case is most defensible today (rows 4, 11, 12, 15) and also the segment least likely to pay. See report 2.
- The scores are a conversation starter, not a measurement. A one-point change on a weight-5 row moves Chit's total by about 2 points, so Chit, FamilyWall and HA are **not reliably ranked** against each other. Skylight's lead is larger and more robust.

## 6b. Missing features at a glance

Ranked in full, with scoring method, sequencing and kids-module findings, in [`03-missing-feature-analysis.md`](03-missing-feature-analysis.md). Focused kids research is in [`04-kids-module-research.md`](04-kids-module-research.md).

| Order | Missing or weak | Why users want it | Where Chit is |
|---|---|---|---|
| 1 | **Calendar-feed recurrence** (`RRULE`, exceptions, time zones) and **activities beyond a weekly slot**, with a way to create one-off events | Sync reliability is the top trust issue (F2); clubs publish trainings as repeating events | Feeds connect per child; recurrence is dropped |
| 2 | **Smart Import** of school letters, PDFs and photos | Most requested mainstream feature (F4) | Absent |
| 3 | **Real Home Assistant connector** and **live-verified energy** | Wedge segments (F3, F8) | Demo data; Tibber and SolarEdge untested live |
| 4 | **Attention cards** (notification-first) | Spouse acceptance (F3) | Designed, not built |
| 5 | **Meals and lists** (integrate first) | Table stakes in the organiser category (F9) | Absent |
| 6 | **Shared expenses without a daily cap** | Splitwise backlash (F1, F6) | Structure only |
| 7 | **Reminders on phones**, including medication at dose time | Best-evidenced part of children's medication apps | Log and refill warning only; no push |
| 8 | **Kid-app transparency screen and shared-tablet pairing** | KIM 2024: 63% of 10–11s own a phone, so 37% do not; teen trust research | Absent |
| 9 | **Adult authentication** | Privacy promises depend on it (F6, F10) | None (ADR-0007) |

Deliberately not recommended now: kid debit card and real-money allowance, location sharing and messaging, direct school-portal integrations, two-way edits to external calendars.

## 7. Strategic read

1. **Do not fight Skylight on Skylight's turf.** A $300 plug-and-play wall screen with email import is hard to out-polish. Chit wins where Skylight is structurally weak: price model, openness (an API is a recurring user request), energy, kids' school data, and privacy.
2. **The wedge is "HA-literate household with a spouse who ignores the dashboard" (S-B) plus dynamic-tariff solar (S-C),** because Chit's current build (energy, trust labels, local-first, shared-screen safety) matches the evidence and the competitors are DIY. It is also the segment that gives sharp feedback.
3. **The mainstream expansion gate is F2 and F4:** reliable recurring calendar sync, and *some* form of automatic capture. Without them, S-A will choose Skylight or Cozi.
4. **The "one app for everything" bet needs a test before more modules get built.** Evidence shows every strong competitor wins one lane. The finance module (structure only) is the clearest candidate to validate with five couples before writing code.
5. **Kids' money is a different business.** Real-money allowance means regulated payments and a card programme. Treat star and goal rewards as the scope and leave payouts to partners or integrations.
6. **Resolve the identity gap before any wider pilot.** Auth is "None" (ADR-0007). Couples-finance privacy, kids' data and any hosted profile all depend on it, and F6 and F10 turn on it.

## 8. Risks and open questions

- Do households want a single hub, or a best-in-class app per lane? (Test: concierge pilot with 5–8 households.)
- Will S-A tolerate a hub they have to host? (Test: setup time under one hour with the Pi hub.)
- Is "local-first" a purchase reason or a tiebreaker outside the HA community? (Test: smoke-test landing pages with and without the claim.)
- How big is the German dynamic-tariff-plus-solar segment reachable through a Tibber/aWATTar/Octopus integration? (Test: desk sizing from network-regulator data plus a partner conversation.)
- Do shared-screen privacy modes matter to anyone? (Test: observe use in the pilot household.)
- Follow-up research: ten 30-minute interviews each with S-A, S-B and S-D; a Van Westendorp price survey (see report 2); review mining at volume (app-store exports) to replace our qualitative theme ranking.

## 9. Sources

Gathered 2026-10-07. Third-party aggregators vary in reliability; where possible a claim is backed by at least two.

| ID | Source | Used for |
|---|---|---|
| S1 | [Skylight community summaries (r/skylightcalendar via GummySearch)](https://gummysearch.com/r/skylightcalendar/) and [Best Buy Skylight reviews](https://www.bestbuy.com/product/skylight-calendar-15-inch-touchscreen-smart-calendar-and-chore-chart-white/J3Q5Q2C7XR/sku/6567807/reviews) | Sync problems, API requests, regret posts |
| S2 | [Cozi review analysis (Kimola)](https://kimola.com/reports/explore-in-depth-user-feedback-analysis-on-cozi-family-organizer-app-store-us-148390), [Cozi on JustUseApp](https://justuseapp.com/en/app/407108860/cozi-family-organizer/reviews), [Cozi Trustpilot](https://nz.trustpilot.com/review/cozi.com) | Ads, 30-day free limit, sync, missing features |
| S3 | [Skylight Trustpilot](https://au.trustpilot.com/review/skylightframe.com?page=6), [Skylight on JustUseApp](https://justuseapp.com/en/app/1438779037/skylight-app/reviews) | Subscription frustration, support praise |
| S4 | [Hearth alternatives roundup](https://mangodisplay.com/best-hearth-display-alternatives/) (vendor-authored, treat as biased), [Skylight product page](https://myskylight.com/products/skylight-calendar) | Prices, features, positioning |
| S5 | [Best budgeting apps for couples 2026](https://getfinny.app/blog/best-budgeting-apps-for-couples-2026) (vendor-authored) and [Honeydue on TechCrunch](https://techcrunch.com/2017/08/07/honeydue-is-a-money-management-app-for-couples/) | Couples' needs, pricing |
| S6 | [Splitwise feedback report (Kimola)](https://kimola.com/reports/splitwise-app-feedback-report-uncover-user-insights-google-play-en-144452), [Splitwise limits coverage](https://www.itvoice.in/splitwise-has-introduced-restrictions-on-the-number-of-free-expenses-users-can-add), [Splitwise alternatives 2026](https://getfinny.app/blog/best-splitwise-alternatives-2026) | Paywall backlash |
| S7 | [HA community: "Are we thinking about wall tablets the wrong way?"](https://community.home-assistant.io/t/are-we-thinking-about-wall-tablets-the-wrong-way/1019690) | Notification-first, WAF |
| S8 | [Reducing parental mental load with email and AI](https://pixelparenting.castos.com/episodes/how-to-reduce-the-mental-load-of-parenting-email-attention-and-ai-amy-briggs) | Email-to-calendar demand |
| S9 | [Goldee AI](https://good-design.org/projects/goldee-ai-the-ai-personal-assistant-for-busy-families/), [Ohai back-to-school](https://www.ohai.ai/blog/organize-family-back-to-school-season) | Auto-capture product category |
| S10 | [Greenlight chore apps](https://greenlight.com/best-chore-apps-for-families), [Chore app comparison](https://seniorsimple.org/articles/best-chore-apps-for-kids-2026) | Kids' money pricing |
| S11 | [Parents and family-app privacy (PoPETs 2025)](https://petsymposium.org/popets/2025/popets-2025-0159.php) | Parent privacy concerns |
| S12 | [Dynamic tariffs coverage](https://en.reset.org/consume-energy-when-it-is-cheap-with-dynamic-electricity-tariffs/), [The invisible optimisation tax](https://tarrysingh.com/blog/the-invisible-optimisation-tax) | Tibber, Octopus, aWATTar adoption |
| S13 | [Solcast for Home Assistant](https://github.com/Ashleysbox/ha-solcast-solar), [Forecast.Solar integration](https://www.home-assistant.io/integrations/forecast_solar/) | HA solar tooling, API limits |
| S14 | [Home Assistant integration research (Cooklang)](https://cooklang.org/cli/commands/home_assistant_integration_research/), [Grocy](https://www.libhunt.com/r/grocy/grocy) | Local-first meals and chores |
| S15 | [Cozi alternatives from the EU](https://alternativeto.net/software/cozi/?origin=eu) | GDPR-oriented alternatives |
| S16 | [FamilyWall on the App Store](https://apps.apple.com/app/id496889629) and [pricing history](https://adapty.io/paywall-library/familywall/) | FamilyWall pricing |
| S17 | [Family calendar apps market (Marketintelo)](https://marketintelo.com/report/family-calendar-apps-for-kids-market) | Orientation only |

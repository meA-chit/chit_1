# Missing-feature analysis, rated by user need

- Date: 2026-10-07
- Status: **Directional.** Ranks gaps by how strongly outside evidence says users want them, then by what Chit already has. It is input to story-writing, not a backlog.
- Inputs: [`01-market-research-report.md`](01-market-research-report.md) (findings F1–F10, scorecard), the kids research, the product owner's note that school and sport calendar links are connected per child in household setup, repo state at commit `18df403` plus working tree, [`../../core/current-implementation.md`](../../core/current-implementation.md)
- Companions: [`02-pricing-tier-report.md`](02-pricing-tier-report.md), [`04-kids-module-research.md`](04-kids-module-research.md) (focused research behind the kids items, M14, M15, M23, M24)

## 1. Method

1. **Need (1–5)** is how strongly the outside evidence says users want the capability: frequency across sources, intensity (anger or workarounds), and whether people already pay for it. 5 = recurring, intense and paid for elsewhere; 3 = present in several products, moderate signal; 2 = niche or weak. These are judgements from desk research, not measured demand.
2. **Chit today (0–5)** is the same scale as the scorecard: 0 absent, 1 planned only, 2 partial or demo, 3 solid, 4 strong, 5 best in class. Taken from the repo, not from docs claims.
3. **Effort** is a rough engineering size: S under a week, M one to three weeks, L over a month, XL a programme or an external partner. Sized by feel from the existing module structure; the module owners should re-size.
4. **Gap value** = Need × (5 − Chit today). **Value per effort** = Gap value ÷ effort points (S=1, M=2, L=3, XL=5).
5. Two lenses can override the number: **product rules** (read-only pilot, local-first, privacy, no messaging) and **dependencies** (anything needing identity or HTTPS).

**Caveat on the formula.** Value-per-effort favours small items, so a photo screensaver outranks Smart Import. Section 3 therefore gives a recommended order that adjusts for need of 4 or more, dependencies and the wedge strategy. Use the table to see why, not to build top-down.

## 2. Ranked feature gaps

| Rank | ID | Missing feature | Need (1-5) | Chit today (0-5) | Effort | Gap value | Value per effort | Evidence | Note |
|:-:|---|---|:-:|:-:|:-:|:-:|:-:|---|---|
| 1 | M10 | Photo screensaver or frame from local folder or a photo server | 3 | 0 | S | 15 | 15.0 | F1, F3; Skylight paywalls photos | Cheap, makes the screen feel finished |
| 2 | M11 | Recurring bills with amounts and due-date reminders | 3 | 1 | S | 12 | 12.0 | F6; finance/recurring-bills | Reuses planner reminders |
| 3 | M23 | Kid app: extend 'About me' (shows which sections are shared) to what parents see of the child's own activity, plus pairing on a shared family tablet | 3 | 1 | S | 12 | 12.0 | Kids research 3; KIM 2024; Oxford teen study | 37% of 10-11s have no own phone; the About me sheet already lists shared sections, but only one direction |
| 4 | M3 | Meals and grocery or shared lists (build small, or surface Mealie/Grocy via HA to-do and calendar entities) | 4 | 0 | M | 20 | 10.0 | F9 | Integrate first, build second |
| 5 | M6 | Shared expenses and settle-up, no daily cap, local data | 4 | 0 | M | 20 | 10.0 | F1, F6; Splitwise backlash | Acquisition wedge for couples |
| 6 | M24 | Weekly grades digest instead of a live grade view (parent-only) | 2 | 0 | S | 10 | 10.0 | Kids research 2a | Demand unproven; validate with parents before building |
| 7 | M2 | Smart Import: email, PDF, photo or chat text to events and to-dos, saved only after review | 5 | 0 | L | 25 | 8.3 | F4, F1; Skylight Magic Import, Goldee, Carly | Needs privacy ADR and model-hosting decision |
| 8 | M4 | Attention cards: few, explained, dismissible, notification-first | 4 | 1 | M | 16 | 8.0 | F3 | Core attention service is already designed (US-501..503) |
| 9 | M5 | Real Home Assistant connector (replace demo climate card; read-only) | 4 | 1 | M | 16 | 8.0 | F3, F10; segment S-B | Prerequisite for the wedge |
| 10 | M1 | Calendar-feed recurrence: RRULE and exceptions, floating times and time zones, caching, event limit, SSRF guard | 5 | 2 | M | 15 | 7.5 | F2; Chit gaps 4,5; owner note: school and sport feeds are the main source | Feeds already connect per child in household setup; a series published as one RRULE event is not expanded. Check your real feeds for RRULE |
| 11 | M7 | Kiosk or any-screen mode (Pi or TV reaching the hub) and burn-in-safe display | 4 | 2 | M | 12 | 6.0 | F5; Chit gap 8 | Blocked by loopback-only hub (ADR-0007) |
| 12 | M8 | More energy providers (Octopus Agile, aWATTar, Nordpool) behind the connector contract | 4 | 2 | M | 12 | 6.0 | F8 | Tibber-only today (ADR-0011) |
| 13 | M12 | Fair-share view: who carries which chores and tasks (mental-load balance) | 3 | 1 | M | 12 | 6.0 | Inferred; market-synthesis web:31 | Differentiator to test; weak direct evidence |
| 14 | M14 | Activities beyond a fixed weekly slot: every other week, term dates, holiday pauses, one-off events and festivals, created in Chit | 4 | 2 | M | 12 | 6.0 | F4; owner note; Chit has weekly activities only | Regular activities exist in household setup (weekday, time, place, commute); no in-Chit event creation. Verify during activity creation. The kids/activities folder itself is empty |
| 15 | M13 | Perks catalogue and redemption for stars | 3 | 3 | S | 6 | 6.0 | F7 | Completes the rewards loop |
| 16 | M18 | Budgets and bank connection (open banking), per-person privacy | 3 | 0 | L | 15 | 5.0 | F6; Monarch, Honeydue | Regulation and cost; separable tier |
| 17 | M19 | Two-way calendar edits from Chit | 3 | 0 | L | 15 | 5.0 | F2; Skylight users edit on phone | Conflicts with read-only rule; needs per-capability ADR |
| 18 | M15 | Medication: dose-time reminder that persists until confirmed, missed-dose alert to a second adult, name-free on shared screens | 3 | 2 | M | 9 | 4.5 | Kids research 2b; Medisafe, MyTherapy; asthma trial | Evidence supports reminders, which are the unbuilt part; needs push; park if not built |
| 19 | M16 | Public API, webhooks, and Chit entities exposed to Home Assistant | 3 | 2 | M | 9 | 4.5 | F5; Skylight 'Feature Request: API' (8 posts) | Distribution channel into S-B |
| 20 | M9 | Setup wizard and pre-built hub image (target: under one hour) | 4 | 2 | L | 12 | 4.0 | F5 | Decides who can adopt at all |
| 21 | M17 | Explained appliance guidance with measured savings report | 4 | 3 | M | 8 | 4.0 | F8 | Best-two-windows exists; savings not shown |
| 22 | M21 | Family location sharing and in-app messaging | 2 | 0 | L | 10 | 3.3 | FamilyWall premium | Conflicts with privacy principle and non-goals |
| 23 | M20 | Kid real-money allowance and card | 3 | 0 | XL | 15 | 3.0 | F7; Greenlight, BusyKid | Regulated; partner instead |
| - | M22 | German and other EU localisation (UI language, date, school terms) | 3 | ? | M | - | - | F5, geography limit | Current state not verified; check before ranking |

## 3. Calendar links and recurring events (checked in the code, 2026-10-07)

The product owner reported that household setup connects calendar links for school, sport and other child activities, and that the likely gap is creating recurring events. The code agrees with the first part and refines the second.

| Layer | What exists | What is missing |
|---|---|---|
| **Calendar links** (household setup, `calendar_sources`) | One feed link per calendar, with a type (including school care and sport activity) and the members it belongs to. Read-only. This is what fills the family view with school events and regular trainings. | Recurrence inside a feed: the reader ignores `RRULE` and `EXDATE`, treats floating times as UTC, and reads only the next 21 days. A club that publishes "every Tuesday" as **one** repeating event would show nothing useful; a feed that lists each date separately works. |
| **Regular activities** (per child, household setup) | Name, place, time range, weekdays, commute mode, travel time, escort. Appears on the timeline. | Only a fixed weekly pattern. No every-other-week, no start and end dates (seasons or terms), no holiday pauses, no single-date changes. |
| **Creating events in Chit** | None. The planner calendar is read-only. One-off reminders and recurring chores exist. | A way to add a one-off event or a series (festival, tournament, parents' evening) without a calendar feed. |

**To check when you create an activity or event** (not verifiable from code alone):
1. Open your school and club feeds as text and search for `RRULE`. If it appears, Chit is dropping those series today.
2. Does the club or school publish a feed at all? Where it does not, parents re-type the schedule as a weekly activity, which cannot express exceptions.
3. Whether creating events inside Chit conflicts with the read-only pilot rule (`AGENTS.md`). The rule is about changing someone else's schedule or devices; events kept in Chit's own store may be fine, but that needs a story and a decision.

This is why **M1** (feed recurrence) and **M14** (activities beyond a weekly slot, created in Chit) are the two practical fixes, and why the earlier plan to add "paste your school's iCal link" is already met by the existing calendar links.

## 4. Kids module: what fits the market and what is missing

Detailed evidence is in [`04-kids-module-research.md`](04-kids-module-research.md). Confidence is lower here than elsewhere: parent-experience evidence for German schools was thin, and no evidence exists for what 10–13-year-olds want from the kid app.

### Aligned with the research
| Kids feature | Evidence | Fit |
|---|---|---|
| Parent-controlled kid phone view (QR plus code pairing, per-child toggles, revocation, isolated gateway) | Parent concern about children's data (F7); in Germany 63% of 10–11s and 79% of 12–13s own a smartphone (KIM 2024) | Strong; no organiser shows a child-device story |
| Grades and medication off by default, absent from the response when not shared | Selective sharing is what privacy-minded users choose (F6, F10) | Strong |
| Stars, goals and parent approval, free and uncapped | Skylight gates rewards behind its paid plan; Greenlight and BusyKid sell chores for money (F1, F7) | Good, but a commodity |
| Calendar links per child for school and sport | School and club information is the main source of mental load (F4) | Good; works for feeds that list each date |
| Child adds their own homework | Typing fatigue ends tracking (F4); shared class planners such as Sharezone use the same idea | Partial help |
| Grades never treat a missing grade as zero | Parent portals cause panic when entries are incomplete | Good practice |

Two features have **no demand evidence either way**: weighted German grade averages, and the medication log. The market response to grades is a weekly digest, not live numbers.

### Missing (ordered by evidence)
| # | Gap | Evidence | Item |
|---|---|---|---|
| 1 | **Automatic capture of school letters and PDFs.** Calendar links cover timetables and trainings, but not letters, trips and one-off announcements, which still need typing. | F4; schools pick the portal and parents cannot choose it, so capture beats integration | M2 |
| 2 | **Feed recurrence and non-weekly activities** | F2; section 3 | M1, M14 |
| 3 | **Reminders that reach the phone**, including medication at dose time | Reminders are the best-evidenced part of children's medication apps; the kids README lists them as not built | M15 |
| 4 | **Transparency in both directions and shared-tablet pairing** (the About me sheet lists shared sections today) | KIM 2024: 37% of 10–11s have no own phone; Oxford teen study on autonomy and trust | M23 |
| 5 | **Real adult authentication** | "View as" is not access control (ADR-0007), so the strict privacy class is stronger than the enforcement | Enabler |
| 6 | **Grades as a weekly digest** | Over-checking evidence; no demand evidence | M24 |
| 7 | **Routines and a spendable rewards loop** | Skylight offers routines free; stars are deliberately never spent | Park |

### Decided against, with reasons
- **Direct integrations with Schulmanager, Sdui or schul.cloud.** No official export was found, unofficial APIs break without notice, and a school, not a parent, chooses the platform.
- **Location sharing.** Parents rank it first when buying a first phone (83% in KIM 2024), but it conflicts with the privacy principle and with the non-goals. Expect parents to ask; decide deliberately.
- **Real-money allowance.** Regulated payments; partner later if ever.

## 5. Recommended sequencing

### Now: fix trust and finish the wedge
| Order | Item | Why now |
|---|---|---|
| 1 | **M1** Feed recurrence (RRULE, exceptions, time zones, caching, SSRF guard) | Recurrence is how clubs publish trainings, and calendar reliability is the top trust issue (F2). Also a security fix (gap 5). Check your real feeds first. |
| 2 | **M5** Real Home Assistant connector | The strongest segment (S-B) needs real devices; the climate card is demo data. |
| 3 | **Verify Tibber and SolarEdge on live accounts** (enabler) | Energy cards are untested against reality. |
| 4 | **M4** Attention cards (first three types) | Notification-first is the spouse-acceptance test (F3). |
| 5 | **M14** Activities beyond a weekly slot, plus a way to create one-off events | Closes the gap you identified; verify with a real activity first. |
| 6 | **M23** Kid-app transparency screen and shared-tablet pairing (small) | Cheap; backed by the best teen-acceptance evidence. |
| 7 | **M10** Photo screensaver (small) | Cheap; makes the screen feel finished. |

### Next: widen the audience (needs the identity decision)
| Order | Item | Why |
|---|---|---|
| 8 | **M2** Smart Import for school letters, PDFs and photos | The most requested mainstream feature and the strongest paid-tier candidate (F4). Privacy ADR and a three-household concierge test first. |
| 9 | **M3** Meals and lists via integration | Table stakes (F9); integrate Mealie and Grocy through Home Assistant before building. |
| 10 | **M6** Shared expenses and settle-up | Acquisition wedge against Splitwise's cap (F1, F6); test with five couples. |
| 11 | **M8** More tariff providers | Opens the EU segment beyond Tibber (F8). |
| 12 | **M9** Setup wizard and hub image | Adoption lever for non-experts (F5). |

### Later, validate first, or partner
M15 medication reminders (build the reminder with a second-adult alert, or park the feature), M24 weekly grades digest (validate first), M7 kiosk mode, M11 and M18 bills and bank connection, M12 fair-share view, M16 API and Home Assistant entities, M17 savings report, M13 perks.

### Do not build now
| Item | Reason |
|---|---|
| **M20** Kid debit card and real-money allowance | Regulated payments; partner or integrate. |
| **M21** Location sharing and in-app messaging | Conflicts with the non-goals and the privacy principle. |
| **M19** Two-way edits to external calendars | Conflicts with the read-only pilot rule; needs a per-capability ADR. (Creating events held in Chit's own store, M14, is a different and smaller decision.) |
| Direct school-portal integrations | See section 4. |

## 6. Enablers (not user "wants", but nothing above ships without them)

| Enabler | Blocks | Source |
|---|---|---|
| Identity and authentication for adults | Remote access, paid tiers, finance, strict kids privacy in practice, any non-loopback use | ADR-0007; open decision 2 |
| HTTPS for the kid phone gateway; web push | Medication and chore reminders on phones, off-network use | ADR-0012 follow-ups |
| Network decision for TV and Pi displays | M7; also LAN use generally | Chit gap 8; `CHIT_LAN` in commit `18df403` |
| Live-account verification of Tibber and SolarEdge | Honest energy cards | Chit gap 3 |
| Real-iPhone verification of kid app Home Screen handoff | Kid phone claims | ADR-0012 consequences |
| Provenance carried end to end | Trust labels beyond the agenda | Chit gap 2; ADR-0003 |
| Linting and CI | Definition of done | Chit gap 6 |
| Billing and entitlements design | Any paid tier | Report 2, section 5 |

## 7. Where Chit already has something users want that competitors lack
These are not gaps. They are the proposition. Protect them while closing the gaps above.

| Strength | Evidence of demand | Competitor coverage |
|---|---|---|
| Honest data states: measured, forecast, manual, unavailable, demo | HA solar users compare forecast and actual; mistrust of unlabelled values (F8, F3) | Almost none outside HA |
| Dynamic-tariff and solar guidance in a family-readable view | Growth of Tibber, Octopus and aWATTar (F8) | Tariff apps show prices only; HA is DIY |
| Parent-controlled kid phone app with scoped views and revocation | Parent privacy concern (F7); phone ownership data (KIM 2024) | Skylight and Cozi show no child-device story |
| School-day plan, grades (German scale), homework and tests, medication in one kids module | Mental-load literature; German household | No organiser covers grades and medication |
| Per-child calendar links for school and sport, with regular activities and commute on one timeline | F4 | Skylight and Cozi sync calendars but have no child commute or activity model |
| Local-first with an encrypted store | Preference among HA and EU privacy users (F10) | Skylight, Cozi and FamilyWall are cloud |
| Per-member and per-surface enablement, screen-safe mode | Principle-driven; not yet observed as demand | None observed |

## 8. Product-brainstorm lens: what to challenge before building from this list

**Anti-pattern warning (feature-parity trap).** Parts of this list, such as meals, lists and photos, exist because competitors have them. They are here because users use and complain about them, not because they exist. Ask which user job each serves and whether integration serves it equally well.

**Riskiest assumptions and the cheapest test for each**
1. *Households want one hub for chores, kids, energy and money.* Test: five couples use shared expenses alone for two weeks, then say what they wanted next.
2. *The spouse who did not build the system will look at the screen.* Test: put the current dashboard in the owner household's kitchen for two weeks and log glances and taps.
3. *Parents will let an AI read school letters.* Test: a concierge version where parents forward three real letters to a person-operated flow, then review the output.
4. *Non-experts can host a hub.* Test: time three non-technical volunteers installing from the current docs.
5. *Children aged 10–13 will use the kid app.* Test: 20-minute sessions with five to eight children; ask what they would open it for and what they would hide.

**How might we**
- How might we show the family what changed today instead of everything that exists?
- How might we capture school and club information without parents typing, and without Chit reading their inbox?
- How might we give a child something useful that is theirs, so a parent-controlled app feels fair?
- How might we help a household decide when to run things in under five seconds?

**Eliminate (SCAMPER).** If only three things survive: reliable shared calendar, attention cards, and energy windows. Everything else is optional and can follow evidence.

## 9. Open questions
- Do the school and club feeds in your household use `RRULE`, and do other target households' schools provide feeds at all? (Check the feeds as text; ask five German parents.)
- What is the UI language and localisation state? (M22 could not be ranked.) Check before planning an EU launch.
- Is photo display (M10) a real driver or a symptom of Skylight's paywall anger?
- Can Chit's module structure absorb "integrate Mealie and Grocy" without breaking module isolation, or does it need a core connector? (`docs/core/connectors.md` should answer.)
- Do parents want grade entry at all, and would a medication feature be used when free dedicated apps exist? (Five to eight parent interviews.)

## 10. Suggested next steps
1. Open stories for M1, M5, M4 and M14; use your real feeds as the acceptance test for M1.
2. Draft ADRs: identity for adults, Smart Import privacy and model hosting, creating events held in Chit.
3. Run the cheap tests in section 8 before committing to M2, M6, M9 or more kid-app work.
4. Schedule interviews: ten each with mainstream parents (S-A), Home Assistant households (S-B) and couples (S-D); include five children aged 10–13 for the kid app.

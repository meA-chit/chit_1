# Chit consciousness: problems, ratings and build plan

- Date: 2026-10-08
- Status: **Directional proposal.** It changes no scope and approves no story. Where it touches an open decision (event bus #11, identity #2, data classes #15, health scope #8) it recommends; the product owner decides through an ADR.
- Inputs: `docs/00-overview/*` (vision, personas, customer journey, module map, rules, open decisions), `market-research/01`, `03` (04 is frozen and only linked), `docs/core/*` (attention, trust, data model, contracts, current implementation), ADR-0003/0004/0009/0011/0012, `docs/releases/*`, the store migrations 001–018.
- Evidence limit: this is desk synthesis. Needs and wants below are judgements built on the market reports, not measured demand. No Chit household other than the owner's has used the product. Treat every score as a hypothesis to test.

## 1. What "conscious" means for Chit (working definition)

Chit is conscious when it **knows the household's situation now, remembers what mattered, anticipates what comes next, knows what it does not know, and uses that to spend as little of the household's attention as possible.** Success is measured by happiness and by money and time saved, not by how clever it sounds.

Five faculties, each a testable capability:

| Faculty | Question it answers | Today |
|---|---|---|
| Perceive | What is happening, from which source, how fresh? | Connectors, provenance envelope (partial, ADR-0003) |
| Remember | What happened, what did we decide, what is normal here? | Tables per feature; no memory model, no event ledger |
| Understand | What does it mean, what conflicts, what is due? | Deterministic bits per module (best-two-windows, streaks) |
| Attend | What deserves a human's attention, for whom, when, on which surface? | Designed (US-501..503), not built |
| Reflect | Was I right, useful, noisy? What should I change? | Absent |

A sixth property cuts across them: **self-awareness**. Chit knows its sources, their health, its confidence, and its limits (read-only, no inference from absence). This is already Chit's strongest asset (data states, rule 3), and it is what separates honest awareness from a chatbot that guesses.

## 2. Problems Chit solves, rated

### 2.1 Method
- **Need (1–5)**: how strongly the underlying job exists and hurts, from the market reports (F1–F10, missing-feature analysis) and personas. **Want (1–5)**: how much people ask for it or already pay for it. Need without want (trust, privacy) is an enabler: users punish its absence but do not shop for it.
- **Leverage (1–3)**: how much memory, awareness or anticipation changes the outcome. 1 = a plain feature does the job; 3 = the problem *is* noticing, remembering or anticipating.
- **Priority** = Need × Want × Leverage (max 75). Value pillar: **T** time, **M** money, **H** happiness.
- **Chit today (0–5)** is from the repo state (`docs/core/current-implementation.md`), same scale as the missing-feature analysis.

### 2.2 Problem list

| ID | Problem (household language) | Personas | Pillar | Need | Want | Leverage | **Priority** | Chit today |
|---|---|---|---|---|---|---|---|---|
| P3 | "School and club information arrives as letters, PDFs and chats and I have to retype it." | Coordinator, Parent | T | 5 | 5 | 3 | **75** | 0 |
| P2 | "I carry the whole plan in my head: who goes where, who collects, what to prepare." (mental load) | Coordinator, Member | T, H | 5 | 4 | 3 | **60** | 2 |
| P4 | "Things slip: a deadline, a bill, medication, a form, the swimming bag." | All adults, Parent | T, M, H | 5 | 4 | 3 | **60** | 2 |
| P7 | "I do not know when to run the washer or charge the car to pay least or use the sun." | Energy-aware homeowner | M | 4 | 4 | 3 | **48** | 3 |
| P1 | "Calendars, chores, weather and home info live in five places." | Coordinator, Member | T | 5 | 5 | 2 | **50** | 3 |
| P6 | "Only the person who built it looks at the screen." (spouse acceptance, notification-first) | Member, Partner | H | 5 | 3 | 3 | **45** | 1 |
| P5 | "The calendar is wrong or late, so I stop trusting it." (sync, recurrence) | All | T | 5 | 4 | 2 | **40** | 2 |
| P8 | "Shared money, bills and settling up cause friction." | Partner, flatmates | M, H | 4 | 4 | 2 | **32** | 0–1 |
| P10 | "I want to know how school is going without nagging." | Parent, Child | H | 3 | 3 | 2 | **18** | 3 |
| P11 | "Medication and health routines of a child must not be missed." | Parent | H | 3 | 3 | 2 | **18** | 2 |
| P14 | "Setting up and maintaining this is a project." | Administrator | T | 4 | 4 | 1 | **16** | 2 |
| P12 | "Is this number real, forecast or demo?" (trust) | All | H | 4 | 2 | 2 | **16** | 4 |
| P9 | "The kids will not do chores without motivation." | Parent, Child | H | 3 | 4 | 1 | **12** | 3 |
| P13 | "Private details must not show on the shared screen." | Privacy-conscious | H | 4 | 3 | 1 | **12** | 3 |
| P15 | "Meter readings, filters, warranties, service dates." | Administrator | M, T | 3 | 2 | 2 | **12** | 2 |
| P16 | "Who carries how much of the chores?" (fair share) | Partner | H | 3 | 2 | 2 | **12** | 1 |

### 2.3 What the ratings say
1. **Consciousness pays most where the problem is noticing, remembering or anticipating** (P3, P2, P4, P7, P6). Those are the top five by leverage-weighted priority, and they are exactly the jobs a static dashboard cannot do.
2. **P3 capture is the single largest gap** and a trust risk at once: it needs a language model and an untrusted-input boundary. It is also the most requested mainstream feature (F4). It must come with a review step, never auto-save.
3. **P1, P5, P12, P13 are the floor.** A conscious layer on top of a wrong calendar is false awareness. Calendar recurrence (M1) and live verification of Tibber/SolarEdge come before learning anything.
4. **P6 is the real product test.** The screen has to come to the person (a few cards, a push, a morning line) rather than wait to be opened. That needs identity and HTTPS (open decision 2); until then notification-first runs on the shared screen only.
5. **P9, P10, P11, P16 are real but low-leverage for memory.** Do not spend consciousness budget there; and P16 (fair-share) and any per-child scoring carry surveillance risk (section 5).
6. **Money and time are measurable only where Chit can compute a baseline**: P7 (price × consumption), P4 (late fees avoided, user-confirmed), P3 (minutes of typing avoided, estimated). P2 and P6 are happiness metrics and need a pulse question.

## 3. Architecture of the conscience

Principle: **the model decides nothing that has a right answer.** It phrases, extracts and asks. Conflicts, availability, amounts and dates stay deterministic (`docs/core/attention-and-insights.md`). The consciousness layer is a set of **core services** that modules feed through public contracts; no module imports another and nothing hard-codes who sees what.

```
 SENSES            LEDGER             MEMORY               REASONERS            ATTENTION          SURFACES
 connectors   ->   event outbox  ->   working state    ->  L1 deterministic ->  ranker +        -> tv / tablet / web
 module events     (append only,      episodic (13 mo)     (module insights)    scheduler          mobile (later)
 user actions      replayable)        semantic facts   ->  L2 pattern miner ->  budget per      -> push (later)
 time triggers                        preferences          (local, small)       surface/day
                                      value ledger     ->  L3 language      ->  explanation
                                                           (extract, phrase)    + evidence
                                                                 ^                   |
                                                                 +--- L5 reflection <-+ feedback (ack, dismiss, outcome)
```

### 3.1 Memory (how to build it)

Five tiers, one owner (core), modules declare what they contribute:

| Tier | Holds | Form | Rebuildable? | Retention default |
|---|---|---|---|---|
| M0 Working state | The household "now": today's plan, open items, source health, current prices | Derived snapshot per household, incrementally updated | Yes, from M1 and sources | Minutes to a day |
| M1 Episodic ledger | What happened: `chore.completed`, `reminder.acknowledged`, `appliance.run.finished`, `source.degraded`, `card.dismissed`, `bill.paid` | Append-only typed events `<entity>.<verb>`, with the provenance envelope, no free text from external sources | No, it is the record | Detailed 13 months, then compacted to aggregates |
| M2 Semantic facts | What is normal here: "Tue 17:00 football, 25 min by car", "dishwasher cycle 2.1 h, 1.1 kWh", "school bag needed Mon, Thu" | Fact = subject, predicate, value, evidence ids, confidence, `learned` / `confirmed` / `rejected`, valid-from/to | Yes (mined), except confirmations | Until superseded or rejected; expiry review every 6 months |
| M3 Preferences | Quiet hours, which cards each member wants, channel, language, detail level | Member-scoped settings, editable | No | Until changed |
| M4 Value ledger | Interventions and outcomes: card shown, accepted, estimated minutes or euros saved, user-confirmed or not | Append-only, each estimate labelled `forecast` or `manual` until verified (rule 4) | No | 36 months, aggregates forever |

Rules for every tier:
- **A learned fact never silently changes behaviour.** It starts as a hypothesis, shows as "Chit noticed… is that right?", and only confirmed facts feed cards that touch people (L1 ignores unconfirmed ones; L2 may use them for ranking low-stakes items).
- **Every memory record carries**: owner module, data class (`personal`, `household`, `public`, `operational`; ADR-0009), audience scope (household / member / strict), source ids, `observedAt`, `ingestedAt`, schema version.
- **Forgetting is a feature.** A retention engine runs daily from the module's declaration; "forget this" works per fact, per member and per module; revocation invalidates caches (existing trust rule).
- **Module declares its memory** in `module.manifest.yaml` (extends the existing "each module declares what it stores" rule): events it emits, facts it owns, fields it must never persist, retention. The manifest schema gets a `memory:` block; the isolation check enforces it.
- Per-person memory in sensitive classes waits for identity (open decision 2). Until then, household-level and non-sensitive memory only.

### 3.2 Intelligence (how to structure it)

| Layer | Job | Method | May decide? | Where |
|---|---|---|---|---|
| L1 Deterministic reasoners | Conflicts, availability, due dates, leave-by times, price windows, streaks | Rules, solvers, arithmetic | **Yes**, they own correctness | Module `insights`/domain submodules (exists in part) |
| L2 Pattern miner | Routines, typical durations, forecast error (weather, solar), baselines, anomalies | Small local statistics over M1; no external calls | Produces hypotheses with confidence only | New `core/memory` job |
| L3 Language | Turn letters, PDFs, photos, chat text into proposed events and to-dos; phrase explanations; answer "ask Chit" by calling read contracts as tools | Local model first (OpenClaw per ecosystem doc); cloud only per approved purpose (rule: no household data to cloud processors without policy) | **No.** Proposes; a person confirms; deterministic code validates | New `core/language`, used by planner and kids |
| L4 Attention | Pick few cards, per audience and surface, at the right time | Documented score (below), hard caps, quiet hours | Decides *what to show*, never what to do | Core attention service (US-501..503) |
| L5 Reflection | Weekly self-review: card precision, noise, misses, source health | Counters over M1 and M4, shown to the admin | No | Core, simple at first |

**Attention score (starting point, tune with feedback):**
`score = urgency × impact(time, money) × audience_fit × confidence × novelty − fatigue`, with hard rules above it: sensitive classes only on allowed audiences and masked on shared screens; max N cards per surface; a dismissed card of the same evidence stays quiet until the evidence changes; unknown or stale evidence lowers confidence and is *said so* instead of hidden.

**Untrusted input boundary (P3):** calendar text, letters and PDFs are data. Extraction runs with no tools beyond "emit a proposal", output is schema-validated, nothing is saved before review, and external text is never written into memory M2 or prompts as instructions (threat already listed in `trust-and-privacy.md`).

### 3.3 Always aware (how it never sleeps)

1. **Always-on hub.** The conscience runs as part of the hub daemon on an always-on machine; restart catches up from the ledger (missed time triggers are replayed or skipped by rule, never lost silently).
2. **Event backbone.** Recommend resolving open decision 11 as **in-process pub/sub plus a persisted outbox in the same SQLite**: at-least-once, idempotent consumers, replay so a new learner can be trained on history. No broker; hosted profile unchanged.
3. **Source watchers.** Each connector reports freshness against its policy; transitions emit `source.degraded` / `source.recovered`. Awareness of its own blindness is the first thing built, because every other feature depends on it.
4. **Time triggers.** A scheduler emits `T-minus` events from deterministic rules: leave-by for the next commute, "tonight: pack tomorrow's bag", bill due in 3 days, price window opens in 30 minutes, day rollover, weekly reflection.
5. **"What changed" per surface.** Each surface remembers what it last showed; the dashboard highlights deltas (new, moved, cancelled, newly overdue) instead of everything that exists.
6. **Delivery order.** Shared screen (works today) → phone push with an opaque "something changed" signal (ADR-0009, needs identity and HTTPS) → read-only Telegram/WhatsApp queries (deferred, privacy review). Nothing outward-acting without a per-capability ADR.

## 4. What to store as history, and what not

Test for storing anything: **(a)** it answers a recurring question or feeds a learner, **(b)** it is the household's own decision or outcome or a cheap aggregate, **(c)** its absence would lose value that cannot be re-fetched, **(d)** the household could be shown it and explain why it is kept. If it fails (c) because the source keeps it, do not mirror it (ADR-0004).

| Data | Store? | Form | Retention | Class | Why |
|---|---|---|---|---|---|
| Subscribed calendar events | **No mirror** | Rolling window of metadata only (start, end, member, category, source) for diffs and pattern mining; title, location, notes, attendees only inside the display horizon | 90 days metadata | personal | Source is authoritative (ADR-0004); history is needed only to learn routines and detect changes |
| Chore completions, reminders ack/skip | **Yes** | M1 events | 13 months detailed, aggregates after | household | Streaks, fairness only if opted in, routine learning |
| Weather | Aggregates + **forecast error** | Daily summary; forecast-vs-actual pairs | Hourly 30 days, daily 13 months | public | Calibrates "will it rain on the walk", solar estimate quality |
| Electricity prices | **Yes** | Hourly | 13 months | public | Seasonality and tariff comparison |
| Energy consumption / production | **Yes, aggregated** | Hourly aggregate; raw intervals short | Raw 30 days, hourly 13 months, daily forever | personal | Savings baseline and yearly comparison |
| Appliance runs | **Yes** | One record per run: start, duration, energy, window used | 13 months | household | Learns cycle length and tests suggestions |
| Raw power traces / device chatter | **No** | — | — | — | High volume, low value, appliance-use fingerprinting risk |
| Meter readings | **Yes** | Existing | Forever | household | Low volume, high value |
| Suggestions and cards: shown, ack, dismissed, outcome | **Yes** | M1 + M4 | 13 months (value ledger 36) | household | The only way Chit learns whether it helps |
| Source health transitions | **Yes** | Events | 13 months | operational | Self-awareness, diagnosing "why was it wrong" |
| Money: shared expenses, bills, amounts, categories (manual) | **Yes** | The product itself | Until household deletes | personal (sensitive) | Core of finance; per-person privacy between partners |
| Bank transaction descriptions | **Minimise** | Amount, date, category only if import ever exists | — | personal (sensitive) | Descriptions reveal more than the function needs |
| Stars, goals, approvals | **Yes** | Ledger | Until child ages out, then archive or delete by parent choice | personal (strict) | The reward loop |
| Grades | **Yes, parent-scoped** | As entered | Parent choice; no derived "ability" metrics | personal (strict) | Never treat missing as zero |
| Medication taken or missed | **Yes, minimal** | Time, taken/missed, no name in derived views | 12 months | personal (strict) | Second-adult alert; privacy on shared screens |
| Imported letters / PDFs / photos (P3) | **Result, not source** | Reviewed structured proposal + source hash; original deleted after review | Original 30 days max (user setting), result follows its entity | personal | Cuts exposure; the event is the value |
| LLM prompts, outputs, chat transcripts | **No by default** | Only confirmed extractions and confirmed facts survive | — | — | Memory poisoning, privacy, cost; opt-in evaluation samples with consent |
| Location / presence | **No history** | Current state only, short TTL, never an hourly trail | Minutes | personal (strict) | Product vision already says no persisted location trail |
| Health metrics (steps, sleep, HRV) | **Opt-in, aggregate only** | Daily summary | Per person, short, revocable | personal (strict) | Highest privacy risk (open decision 8); leave out of v1 conscience |
| Connector secrets, tokens | **Never in memory or logs** | Encrypted config only | — | personal | Existing rule |
| Config and permission changes | **Yes** | Audit log | Forever or 36 months | operational | Trust and incident review |

**Compaction:** detailed events roll up to daily/weekly aggregates before deletion so patterns survive without the details. **Backups** carry household-class memory only as client-side encrypted blobs (ADR-0009).

## 5. What to track, and what not

**Track outcomes and system health, not people.**

| Track | For |
|---|---|
| Source freshness and failures | Self-awareness, repair |
| Card precision: acted on / dismissed / ignored, per card type (not per member) | Tuning attention, reducing noise |
| Time-to-know: seconds from event to the right surface showing it | "Always aware" test |
| Estimated minutes saved per accepted proposal and per card (labelled `forecast` until confirmed) | Time value |
| Euros saved: accepted energy suggestion vs the household's own baseline, bills paid on time | Money value |
| Weekly pulse: one question to the household ("did Chit make this week easier?"), plus a thumbs on cards | Happiness |
| Spouse test: did a non-admin member open, acknowledge or dismiss anything this week (yes/no per member, shown only to that member and the admin) | P6 |
| Misses reported by the household ("Chit should have told me") | Recall |

| Do not track | Why |
|---|---|
| Per-member screen time, glances, or "who looked" | Surveillance inside the family, and it would chill honest use |
| Children's scores, rankings, "behaviour" or ability profiles; grade prediction | Child profiling; strict class; harm outweighs any gain |
| Location history, commute traces, presence timelines | Privacy principle and non-goals |
| Chore counts compared between adults as blame (fair-share view) | Only as an opt-in, shared-by-both view, never a leaderboard (P16 is low priority anyway) |
| Raw content of messages, letters or health streams beyond the confirmed result | Minimisation |
| Any product analytics leaving the hub | Local-first; metrics stay on the hub, optional aggregate export is a separate decision |
| Inference of availability or behaviour from absence of data | Rule 3 |

## 6. Plan

Gate rule from the roadmap applies: a phase starts when its gate decisions are recorded.

### Phase 0: Ground the conscience (decisions plus plumbing)
| Item | Output |
|---|---|
| ADR-0013 Memory model | Tiers M0–M4, record envelope, retention engine, "learned vs confirmed" rule, what is never stored (section 4) |
| ADR-0014 Event backbone | Resolves open decision 11: in-process bus plus persisted outbox in SQLite, idempotent consumers, replay |
| ADR-0015 AI boundary | L3 proposes only, local model first, untrusted-input handling, no household data to cloud models without a policy, evaluation data consent |
| Data classes per table | Closes open decision 15; every table and event states its class |
| Manifest `memory:` block + isolation check | Modules declare events, facts, retention, never-store fields |
| Core `events` table (outbox) and `source.*` events | First awareness: Chit knows when a feed or connector goes stale |
| Prerequisites already on the list | Calendar recurrence and SSRF guard (M1), live Tibber/SolarEdge verification, provenance end to end (US-102) |

Gate: ADR-0013/0014/0015 accepted. Exit: ledger exists, two modules emit events, source health visible on the dashboard.

### Phase 1: Aware (attention and heartbeat)
| Item | Output |
|---|---|
| Scheduler with T-minus triggers | Leave-by, bag-the-night-before, bill-due, price-window opening |
| Attention service US-501..503 | Ranker, cap per surface, explain, ack/dismiss writes M1/M4 |
| First three card types | (1) Tomorrow's prep and conflicts, (2) best energy window with savings estimate, (3) source degraded / data missing |
| "What changed" strip | Deltas since this surface last showed |
| Feedback capture | Thumbs, dismiss reason (optional), weekly pulse |

Exit signals (hypotheses to test, not targets yet): in the owner household, cards acted on outnumber dismissed; the second adult acknowledges at least one card per week; no card appears with stale or demo data unlabelled.

### Phase 2: Remembering (patterns and facts)
| Item | Output |
|---|---|
| Compaction and retention jobs | Aggregates, expiry, per-fact forget |
| L2 miners, narrow first | Weekly activity routine, appliance cycle length, forecast error for weather and solar |
| "Chit noticed…" confirmation UX | Hypothesis → confirmed / rejected → used by cards |
| Value ledger M4 and monthly summary | Minutes and euros, labelled by data state |
| Reflection v1 | Weekly report to the admin: precision, noise, misses, sources |

### Phase 3: Understanding language (capture and ask)
| Item | Output |
|---|---|
| Smart Import (M2) with review | Email, PDF, photo, chat text → proposed events/to-dos; original deleted after review. Concierge test with three real households first |
| "Ask Chit" (read-only) | Answers by calling read contracts as tools, always citing evidence and data state; says "I don't know" when a source is unavailable |
| Weekly household digest | Replaces opening five screens; the happiness lever for P2 |

Needs: AI boundary ADR, local model hosting decision, identity for per-person scope.

### Phase 4: Reach and act (only with their own ADRs)
Phone push, read-only messaging, then confirmed actions per capability (appliance start, calendar write). Each needs identity, HTTPS, and a per-capability ADR (roadmap "Actions").

### Dependencies and order
Identity (open decision 2) gates per-person memory, push (P6 beyond the shared screen), finance and strict kid data. Phases 0–2 can run on household-level data and the shared screen before it lands. Do not build L2/L3 on a calendar that drops recurring events.

## 7. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Creepiness: Chit knows too much | Show what it remembers (a "What Chit knows" page), per-fact forget, no hidden inference, strict classes excluded from learning |
| False confidence from learned facts | Learned vs confirmed; confidence shown; unknown stays unknown |
| Memory poisoning via calendar text or letters | External text never enters semantic memory or prompts as instruction; schema-validated extraction; review before save |
| Alert fatigue | Hard caps per surface, evidence-aware re-surfacing, precision tracked per card type |
| Child profiling creeping in | Explicit do-not-track list, no derived child scores, parent-scoped views |
| Data-class leakage to cloud paths | Class on every table and event; reviewers reject personal data in cloud-bound code (ADR-0009) |
| Local model cost and quality | Deterministic first; L3 limited to extraction and phrasing; measure before widening |
| Scope creep into autonomy | Read-only rule stays; Phase 4 gated by per-capability ADRs |
| Unmeasurable value claims | Estimates labelled `forecast`/`manual` until verified; baseline defined before the savings figure is shown |

## 8. Decisions needed from the product owner
1. Accept the event backbone recommendation (in-process plus persisted outbox) for open decision 11?
2. Is a local language model on the hub acceptable for L3, with cloud models off by default?
3. Default retention: 13 months detailed, aggregates after. Right for this household?
4. Health data stays out of the conscience in v1 (open decision 8): confirm.
5. Sequencing: calendar recurrence and source health first, then attention, then memory, then language. Confirm, or pull Smart Import (largest need score) forward at the cost of the order of dependencies.

## 9. Research still needed
- Do the owner's real school and club feeds use RRULE? (gates the calendar floor)
- Three-household concierge test of Smart Import: will parents forward real letters, and do they trust the reviewed result?
- Two-week glance and acknowledge log with the second adult in the owner household (P6).
- Five to eight parent interviews and five child sessions already planned in the missing-feature analysis; add two questions: "what should Chit remember for you" and "what should it never remember".
- Baseline for P7 savings: what the household would have paid without suggestions.

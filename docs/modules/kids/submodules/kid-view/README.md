# Submodule: kid-view (module `kids`)

> Parent: [`docs/modules/kids/README.md`](../../README.md) · Code: `modules/kids/submodules/kid-view/`

## Purpose
Composition of the child's own mobile view: which modules and cards appear, as configured by an adult in household settings.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/kids/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## What it does
`/kids` composes the other submodules' panels. A parent picks a child and a tab (Today, Stars, Grades, Health). Viewing as a child shows only that child's school day, stars, chores and goals: no grades, no medication, no management controls. "View as" is a convenience, not access control, until identity exists (ADR-0007).

## Child's own phone (ADR-0012)
A parent turns on the phone view per child and chooses what it shows on the child's **Phone** tab of the Kids page (it used to be the household settings section `kid-phone`, removed in the navigation rework). Pairing is a QR code (single-use secret) plus a 6-digit code shown only on the parent's screen, typed on the phone (an installed Home Screen app, which cannot scan, types the 8-character link code instead); the phone then holds a revocable device token. The phone reaches only the *phone gateway* (`CHIT_PHONE=1`, port 8766): the kid app (`apps/kid-app/`) and `/api/kids/phone/device/*`. Grades and medicine are off by default and, when not shared, are not in the response at all. A child can tick their own chore; stars stay a parent decision.

Routes: parent `GET/PUT /api/kids/phone/settings[/{member}]`, `POST/DELETE /api/kids/phone/pairings`, `DELETE /api/kids/phone/devices/{id}`; phone `POST .../device/pair|handoff|exchange|unpair`, `GET .../device/view|manifest`, `POST .../device/chores/{id}/done`, `POST .../device/homework`, `POST .../device/homework/{id}/done`, `DELETE .../device/homework/{id}`, `POST .../device/homework/{id}/dismiss`, `POST .../device/reminders/{id}/state`, `POST .../device/bag/tick`, `POST .../device/bag/items`, `DELETE .../device/bag/items/{id}`. Tests: `tests/test_phone.py`, `tests/test_plan.py`, `tests/test_gateway_http.py`.

## Status
Implemented (first version); child's phone view and pairing added 2026-10-07.

## Privacy from parents (grades and medicine)
A child can take grades or medicine private from their parents, on their own phone (**Your privacy** in the phone's About screen). Parents set the minimum age per section under **Kids > Phone & privacy** (defaults: grades 10, medicine 14; stored in `kid_privacy_policy`); the child's choice is in `kid_privacy` and only counts while the child is at or above the age, so a parent who raises the age takes the choice back and the phone says so. Age comes from the birth date; a child without one is under every age. While a section is private the parent screens receive `state: private`: grades send the subjects only (no grade, average or trend), medicine sends only medicines a parent marked **safety-critical** (`kid_meds.critical`) plus a count of hidden ones. Parents can see that a section is private, never what is in it. Routes: parent `GET /api/kids/privacy`, `PUT /api/kids/privacy/policy`; phone `PUT /api/kids/phone/device/privacy`, and `privacy` in `GET .../device/view`. Not covered yet: a parent can still add a grade for a child who keeps grades private; parent alerts and the week timeline do not use grades or medicine today, so nothing else needed hiding.

## What the phone app does today (code audit 2026-10-08, updated after K1, K2, K4 and K8 on 2026-10-08)
Source: `apps/kid-app/index.html` (single file, no build step), `sw.js`, `manifest.webmanifest`, `server/routes.py` (`GET /api/kids/phone/device/view` and the writes below). Only sections a parent shares are in the payload; the app shows a tab only when its section is present.

| Screen | What the child sees | What the child can do |
|---|---|---|
| **Today** | Time-of-day greeting and hero colour; chips (stars, homework due tomorrow, or stars to the next goal); a Today / Tomorrow switch. **What leads depends on the time of day** (morning, school, after school, evening, weekend, from the timetable and a default bag time of 19:30): a **Next up** card (current lesson with progress bar, or the next lesson, activity or calendar event with "leave by" and who takes the child), **Before you go** (the bag checklist for today in the morning, **Pack for tomorrow** or the next school day in the evening and at weekends), **Due soon** (at most three homework items, tests with a countdown), **Later today** (lessons, activities, calendar events and chores merged by time), an earn strip to Stars after school and at weekends, today's medicine | Tick or untick a chore; tick bag items and homework; edit the bag lists; open a lesson or homework |
| **Plan** (was Timetable) | Monday to Friday grid by period, current lesson outlined, room per cell; **each cell shows the subject's code with its type as a superscript** (c core, m minor, e elective) and a legend sits under the grid, while lists and sheets use the full name; **Activities** (the child's regular weekly activities with time, place and leave-by); **Coming up** (the next two weeks of events from the child's own calendar links, with an honest notice when no calendar is linked, the feed could not be read, or the list is a stale copy) | Tap a lesson for time, room and the child's own average (if grades are shared) |
| **Homework** | Four tiles (due tomorrow, tests in two weeks, overdue, done this week), open items per weekday, groups (Overdue, Today, Tomorrow, This week, Later), "Done recently" | Add homework or a test (the subject is picked from the child's subject list, grouped core, minor, elective, with no typing; due date defaults to the next lesson of that subject, or seven days out for a test); tick; delete **their own** entries only (a parent's can only be removed by a parent) |
| **Stars** | Total, stars per weekday this week, chores today (with "Done well", "Try again tomorrow", "Waiting for a parent"), goals with progress and "Reached! Ask a parent" | Tick a chore. The star is always a parent decision |
| **Grades** | Overall average and per-subject averages on the German 1 to 6 scale with a colour scale; detail sheet per subject (written and spoken) | Read only |
| **Health** | Next medicine, today's list, last seven days | Read only; the parent logs doses. After the dose time the row says "Ask <adult>" |
| **About me** (avatar) | "Your parents are sharing" list: each section (including activities and the bag checklist) shown as shared or hidden by the parents | Add to Home Screen; remove this phone |

Other behaviour: **writes are queued** (see below); **tablet and landscape** show Today on the left and the chosen tab on the right from 760 px wide; pinch zoom works and the manifest no longer locks portrait; sheets trap focus, close on Escape and make the page behind inert; pairing by QR code plus six digits, or typed link code (see above); iOS Home Screen handoff; demo mode (`?demo=1`, `&now=`, `&theme=`) with a visible "Demo data" ribbon; light and dark follow the phone; reduced motion respected; the last view is kept in `localStorage` and shown with an "Offline" ribbon; the view refreshes when the app returns to the foreground, when the phone comes back online and every 60 seconds. Language is English only, with the German grade scale. Subject colours come from a built-in map of English and German subject names, otherwise a hash of the name.

### Not in the phone app yet (verified against the code; rows marked **Done** were built on 2026-10-08)
| Missing | Detail |
|---|---|
| **Activities and trainings** (K1, **Done**) | Built: weekly activities with leave-by and escort, and calendar events from the child's own calendar links, are in the phone payload (`activities`, share key `activities`), cached for ten minutes on the hub (the calendar reader fetches over the network). Remaining limits: activities are weekly only; the feed reader ignores `RRULE`; leave-by exists only for activities with a commute entered, not for feed events. Original gap: regular activities (household setup, `child_activities`: weekday, time, place, commute, escort) and school or sport events from the child's calendar links are **not in the payload**. The child cannot see practice start times or when to leave. |
| **A bag checklist** (K2, **Done**) | Built: items per subject or activity (table `kid_bag_items`), written by the child or a parent; the checklist for today and the next school day is derived on the hub from the lessons' items, reminders, homework due that day and that day's activities, de-duplicated, ticked per day (`kid_bag_ticks`), and "bag ready" is a quiet confirmation (no star). Not built: weather (the hub has it, the phone does not), a nudge at bag time (needs push), learning from a forgotten item, the parent's "bag ready: yes or no" view (needs the tiers). |
| **Pocket money, perks, earning opportunities** | There is no allowance balance, perk catalogue, redemption or list of extra jobs. Stars and goals only (`rewards` is stars-only by design). |
| **Weather** | Available in the hub (planner/weather), not used here. |
| **Push or on-screen reminders** | Needs HTTPS and web push (ADR-0012 follow-ups). Medicine and bag reminders do not reach the phone when it is closed. |
| **Writes while offline** (K4, **Done**) | Built: homework adds, ticks and deletes, chore ticks, bag ticks and bag item edits are applied on screen at once, kept in a queue in `localStorage` that survives closing the app, and sent in order when the hub is reachable. A banner says how many changes are waiting. A change the hub refuses (for example a parent already reviewed that chore) is dropped with a message. The queue is cleared when the phone is unpaired. |
| **Child-level preferences** | Nothing is configurable by the child (section order, reminder times, theme, which home sections to show). |
| **Age-based behaviour** | The member birth date exists in household setup but nothing uses it. Parent control is six on/off switches per child (`timetable`, `reminders`, `homework`, `stars` on by default; `grades`, `health` off). The model has no notion of what the *parent* sees of the child's own activity. |
| **Tablet layout** (K8, **Done**) | Built: from 760 px wide Today stays on the left and the chosen tab fills the right; the column cap is 1100 px; the portrait lock is gone from both manifests. Not tested on a real tablet. |
| **Accessibility** (K8, **Done**, first pass) | Built: pinch zoom is allowed; tabs, toggles and bag items have accessible names and `aria-pressed` or `aria-current`; focus survives a re-render; sheets are modal dialogs with a focus trap, Escape and an inert background; changes are announced through a live region; tap targets are at least 44 px; visible focus ring; `prefers-contrast` is honoured. Not done: a screen-reader pass on a real device, German text. |

The parent side (`/kids` board, `KidPhoneSettings`) is a wide desktop or tablet board; it has not been verified at tablet widths.

The design that follows from this audit and from [`docs/00-overview/market-research/04-kids-module-research.md`](../../../00-overview/market-research/04-kids-module-research.md) is in [`../../kid-experience.md`](../../kid-experience.md).

## Done, not relevant, cards and icons (2026-10-08)
- **List or cards.** The phone has a list/cards toggle (remembered on the phone). In cards, "Due soon", reminders, chores and the Homework tab show **two-column cards** with **Done** and **Not relevant** (a chore only has Done: the star stays a parent decision). Marking something done or not relevant offers an **Undo** toast; "Not relevant" homework moves to a "Not relevant" section on the Homework tab.
- **Reminders** have per-day marks that belong to one screen: the child's phone and the household dashboard are separate (`reminder_states`, member `''` is the dashboard), so a child ticking a reminder does not hide it from a parent. In the checklist layout a reminder is still an item in the bag list; ticking it marks the reminder itself done and "not relevant" removes it from the list, so both layouts agree.
- **Homework "not relevant"** (`kid_tasks.dismissed_at`) is not the same as done: it is neither open nor finished work, it never counts toward "done this week", and done and not relevant exclude each other.
- **Icons.** Activities and calendar events carry an `icon` chosen by the hub from their name (`config/event-icons.json`, English and German). The phone shows it on the next-up card, in Later today, in the Plan's Activities and Coming up; the family calendar and timeline on the dashboard show the same icon.



## Navigation (web, rework of 2026-10-08)
One way in: the left rail picks the module; on Kids a parent picks the child, then a topic tab (Overview, School, Stars & chores, Homework, Grades, Health, Phone; the tab is in the URL as `?tab=`). **Edit** is a mode of a tab (School, Stars & chores, Grades): timetable, subjects, chores and goals are changed where they are viewed, and Done editing returns to the read-only view. A child viewing as themselves sees only their own day, stars and homework, with no tabs and no Edit. Not built: a "needs attention" card on Overview (homework due and tests are on the Homework tab).

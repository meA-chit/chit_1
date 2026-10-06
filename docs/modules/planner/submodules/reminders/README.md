# Submodule: reminders (module `planner`)

> Code: `modules/planner/submodules/reminders/` · table `reminders` (migration 006)

**Purpose.** Planned nudges for one person or the whole family, shown on the family timeline.

**Behaviour.** A reminder is **one-off**: a title, an optional member (none = everyone), a **date you pick** (Today, Tomorrow or any date) and a **day part** (morning 06-10, day 10-16, evening 16-20, or any time), never an exact time. It appears in that zone band on that day's timeline (any-time ones in their own row) and in the dashboard to-do card. **Skip today** hides it for that day only (undoable); **Remove** archives it. Past one-offs are not listed. (The API can still store weekly-recurring reminders; the UI does not offer them.)

**API.** `GET /api/planner/reminders`, `GET /api/planner/reminders/today` (today's, skipped, and the next 7 days' upcoming), `POST /api/planner/reminders`, `PUT|DELETE /api/planner/reminders/{id}`, `POST /api/planner/reminders/{id}/skip {skipped}`. State `manual`.

**UI.** Added, edited, skipped and removed on the dashboard **Today's to-do** card, and listed in the **household settings screen** (a contributed section, saved instantly). Both use the same form (`modules/planner/shared/forms.tsx`).

**Not built.** Notifications or alerts (Chit does not message anyone in this version), snooze/done state, reminders for a *time of week* other than weekdays (e.g. monthly), reminders from calendar feeds.

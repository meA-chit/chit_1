# Submodule: chores (module `planner`)

> Code: `modules/planner/submodules/chores/` · tables `chore_series`, `chore_completions` (migration 005)

**Purpose.** Recurring household chores with who does them and a streak.

**Behaviour.** A chore series has a title, optional assignee, weekdays (empty = daily) and a **day part** (morning, day, evening or any time) instead of an exact time. Day parts are 1-2 hour zones whose hours the server owns (`modules/planner/shared/dayparts.py`; morning 06:00-10:00, day 10:00-16:00, evening 16:00-20:00; the rest of the day is Relax). Completing today adds a completion row; the **streak** is computed (consecutive expected days with a completion, ending today, or yesterday while today is still open), never stored. Chores not due today are not listed. The card toggles completion and can add a daily chore.

**API.** `GET /api/planner/chores/today` (due today, ordered by day part), `GET /api/planner/chores` (all, for settings), `POST /api/planner/chores`, `PUT|DELETE /api/planner/chores/{id}` (delete archives: history and streak data are kept), `POST /api/planner/chores/{id}/toggle {done}`, `GET /api/planner/chores/options`. State is `manual`.

**Skip today.** `POST /api/planner/chores/{id}/skip {skipped}` hides one occurrence (undoable, kept in a "Skipped today" list). A skipped day is not expected, so it neither breaks nor extends the streak.

**UI.** The dashboard **Today's to-do** card shows chores and reminders together: tick off, add (the same full form as setup: person, days, zone), and per-row actions (skip today, edit, remove). The **household settings screen** lists and edits the same chores (a contributed settings section, saved instantly).

**Seed.** `seed/planner/chores.json` (`seed_streak` is expanded relative to today so demo streaks never go stale). Calendar-generated chores (`chores` table, from feeds) are separate and not shown here yet.

**Not built.** Restore archived chores, rewards link (kids), a full "View all" page, chores on the timeline.

-- "Done" and "not relevant" for reminders and homework.
--
-- A reminder is a nudge, not a task, so it has no completion of its own. The household dashboard and each child's phone can both mark it
-- done for a day, and the two are separate (member_id '' is the dashboard; a child's id is that child's phone), so a child ticking a
-- reminder does not hide it from a parent. "Not relevant" on the dashboard stays the existing per-day skip (planner_skips).
CREATE TABLE reminder_states (
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    reminder_id TEXT NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL DEFAULT '',
    day TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('done', 'na')),
    updated_at TEXT NOT NULL,
    PRIMARY KEY (reminder_id, member_id, day)
);

-- Homework that turned out not to matter (the teacher cancelled it). Not the same as done: it never counts as work finished.
ALTER TABLE kid_tasks ADD COLUMN dismissed_at TEXT;

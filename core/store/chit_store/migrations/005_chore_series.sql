-- Owned by planner/chores. Recurring chores with a completion history, so streaks are computed, not stored.
-- weekdays: comma-separated 0-6 (Monday = 0); empty means every day.
CREATE TABLE chore_series (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    assignee_id TEXT REFERENCES household_members(id) ON DELETE SET NULL,
    weekdays TEXT NOT NULL DEFAULT '',
    due_time TEXT,
    archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX chore_series_by_household ON chore_series(household_id, archived);

CREATE TABLE chore_completions (
    series_id TEXT NOT NULL REFERENCES chore_series(id) ON DELETE CASCADE,
    day TEXT NOT NULL,
    completed_by TEXT,
    completed_at TEXT NOT NULL,
    PRIMARY KEY (series_id, day)
);

-- Day parts are named zones (morning/day/evening), not exact times; their hours live in planner/shared/dayparts.py.
-- NULL day_part = any time of day.
ALTER TABLE chore_series ADD COLUMN day_part TEXT CHECK (day_part IS NULL OR day_part IN ('morning', 'day', 'evening'));

-- Owned by planner/reminders. A reminder is either one-off (on_date) or recurring (weekdays; empty = every day).
CREATE TABLE reminders (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    member_id TEXT REFERENCES household_members(id) ON DELETE SET NULL,
    on_date TEXT,
    weekdays TEXT NOT NULL DEFAULT '',
    day_part TEXT CHECK (day_part IS NULL OR day_part IN ('morning', 'day', 'evening')),
    archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX reminders_by_household ON reminders(household_id, archived, on_date);

-- "Skip for today": hide one occurrence of a chore or reminder without deleting it. Skipped days do not break a streak.
CREATE TABLE planner_skips (
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('chore', 'reminder')),
    item_id TEXT NOT NULL,
    day TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (kind, item_id, day)
);

CREATE INDEX planner_skips_by_day ON planner_skips(household_id, day);

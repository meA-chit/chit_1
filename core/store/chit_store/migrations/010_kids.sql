-- Owned by the kids module: star chores and goals, school grades, the school-day plan and medication.
-- Everything belongs to a child member of a household and is removed with it. Health rows are the strictest data class.

-- Stars: a chore can earn a star; a parent grants the outcome of a finished chore ('well' = green star, 'again' = try again).
CREATE TABLE kid_star_chores (
    series_id TEXT PRIMARY KEY REFERENCES chore_series(id) ON DELETE CASCADE
);
CREATE TABLE kid_chore_outcomes (
    series_id TEXT NOT NULL REFERENCES chore_series(id) ON DELETE CASCADE,
    day TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('well', 'again')),
    granted_at TEXT NOT NULL,
    PRIMARY KEY (series_id, day)
);
-- Goals count the child's stars since started_on. Stars are never spent; a parent approves a reached goal.
CREATE TABLE kid_goals (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    note TEXT,
    cost INTEGER NOT NULL CHECK (cost BETWEEN 1 AND 10000),
    started_on TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'approved', 'archived')),
    approved_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX kid_goals_by_member ON kid_goals(member_id, status);

-- Grades (German scale 1 best to 6). Two graded types per subject; subjects are main or other; weights per household.
CREATE TABLE kid_subjects (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    kind TEXT NOT NULL CHECK (kind IN ('main', 'other')),
    archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
    created_at TEXT NOT NULL
);
CREATE TABLE kid_grades (
    id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL REFERENCES kid_subjects(id) ON DELETE CASCADE,
    grade_type TEXT NOT NULL CHECK (grade_type IN ('written', 'oral')),
    grade REAL NOT NULL CHECK (grade BETWEEN 1 AND 6),
    given_on TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX kid_grades_by_subject ON kid_grades(subject_id, given_on);
CREATE TABLE kid_settings (
    household_id TEXT PRIMARY KEY REFERENCES households(id) ON DELETE CASCADE,
    main_written_pct INTEGER NOT NULL DEFAULT 50 CHECK (main_written_pct BETWEEN 0 AND 100),
    other_written_pct INTEGER NOT NULL DEFAULT 30 CHECK (other_written_pct BETWEEN 0 AND 100)
);

-- School-day plan typed in by a parent (lessons, recess, meals, care), per weekday (Monday = 0).
CREATE TABLE kid_school_slots (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    kind TEXT NOT NULL CHECK (kind IN ('lesson', 'break', 'meal', 'care')),
    note TEXT
);
CREATE INDEX kid_school_slots_by_member ON kid_school_slots(member_id, weekday, start_time);

-- Medication reminders and a given/missed log. weekdays: comma-separated 0-6, empty = every day.
CREATE TABLE kid_meds (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    dose TEXT,
    time_of_day TEXT NOT NULL,
    weekdays TEXT NOT NULL DEFAULT '',
    remind_member_id TEXT REFERENCES household_members(id) ON DELETE SET NULL,
    supply INTEGER CHECK (supply IS NULL OR supply >= 0),
    archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
    created_at TEXT NOT NULL
);
CREATE TABLE kid_med_log (
    med_id TEXT NOT NULL REFERENCES kid_meds(id) ON DELETE CASCADE,
    day TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('given', 'missed')),
    logged_at TEXT NOT NULL,
    PRIMARY KEY (med_id, day)
);

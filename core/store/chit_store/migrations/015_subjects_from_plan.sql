-- Subjects now come only from the school-day plan (kids/school), each with a type: core, minor or elective.
-- The subjects a parent had typed in by hand (migration 010) are removed completely, with the grades entered under them.
-- A subject is created for every lesson title already in a child's plan; the type starts as 'minor' and a parent sets it.
DROP TABLE kid_grades;
DROP TABLE kid_subjects;

CREATE TABLE kid_subjects (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    kind TEXT NOT NULL DEFAULT 'minor' CHECK (kind IN ('core', 'minor', 'elective')),
    -- archived: the lesson left the plan. Grades are kept and the subject returns if the lesson is added again.
    archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX kid_subjects_by_name ON kid_subjects(member_id, name COLLATE NOCASE);

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

INSERT INTO kid_subjects(id, household_id, member_id, name, kind, created_at)
SELECT lower(hex(randomblob(12))), household_id, member_id, MIN(title), 'minor', strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now')
FROM kid_school_slots WHERE kind = 'lesson' GROUP BY household_id, member_id, lower(title);

-- One written-share percentage per subject type (was main and other). Core keeps the old main value; minor and elective the old other value.
CREATE TABLE kid_settings_new (
    household_id TEXT PRIMARY KEY REFERENCES households(id) ON DELETE CASCADE,
    core_written_pct INTEGER NOT NULL DEFAULT 50 CHECK (core_written_pct BETWEEN 0 AND 100),
    minor_written_pct INTEGER NOT NULL DEFAULT 30 CHECK (minor_written_pct BETWEEN 0 AND 100),
    elective_written_pct INTEGER NOT NULL DEFAULT 30 CHECK (elective_written_pct BETWEEN 0 AND 100)
);
INSERT INTO kid_settings_new(household_id, core_written_pct, minor_written_pct, elective_written_pct)
SELECT household_id, main_written_pct, other_written_pct, other_written_pct FROM kid_settings;
DROP TABLE kid_settings;
ALTER TABLE kid_settings_new RENAME TO kid_settings;

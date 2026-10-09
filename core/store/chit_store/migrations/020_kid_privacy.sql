-- Owned by kids/kid-view: a child can take some of their own data private from their parents once they are old enough.
-- `kid_privacy_policy` is the parents' rule per household and section: the age from which a child may choose. Not stored: defaults
-- (grades 10, health 14). `kid_privacy` is the child's own choice, made on their phone; it only counts while the child is
-- at or above the age, so a parent who raises the age takes the choice back, and the phone says so.
-- `kid_meds.critical` marks a medicine a child cannot hide (for example a daily medicine).
CREATE TABLE kid_privacy_policy (
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    section TEXT NOT NULL CHECK (section IN ('grades', 'health')),
    min_age INTEGER NOT NULL CHECK (min_age BETWEEN 0 AND 18),
    PRIMARY KEY (household_id, section)
);

CREATE TABLE kid_privacy (
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    section TEXT NOT NULL CHECK (section IN ('grades', 'health')),
    private INTEGER NOT NULL DEFAULT 0 CHECK (private IN (0, 1)),
    updated_at TEXT NOT NULL,
    PRIMARY KEY (member_id, section)
);

ALTER TABLE kid_meds ADD COLUMN critical INTEGER NOT NULL DEFAULT 0 CHECK (critical IN (0, 1));

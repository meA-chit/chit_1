-- Owned by kids/learning: homework and tests a child has to do. Written by the child or a parent (created_by).
CREATE TABLE kid_tasks (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('homework', 'test')),
    subject TEXT,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    due_on TEXT NOT NULL,
    note TEXT,
    done_at TEXT,
    created_by TEXT NOT NULL CHECK (created_by IN ('parent', 'child')),
    created_at TEXT NOT NULL
);
CREATE INDEX kid_tasks_by_member ON kid_tasks(member_id, due_on);

-- The phone may show homework unless a parent turns it off.
ALTER TABLE kid_phone_access ADD COLUMN share_homework INTEGER NOT NULL DEFAULT 1 CHECK (share_homework IN (0, 1));

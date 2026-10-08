-- Owned by kids/school and kids/kid-view: the bag checklist and what the phone shows of a child's activities (K1, K2).

-- Items a child takes for a subject (PE: sports kit) or an activity (Swimming: swim bag). Written by the child or a parent;
-- nothing is ever added silently. The daily checklist is derived from these plus reminders and homework, and is not stored.
CREATE TABLE kid_bag_items (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    subject TEXT NOT NULL CHECK (length(trim(subject)) > 0),
    label TEXT NOT NULL CHECK (length(trim(label)) > 0),
    created_by TEXT NOT NULL CHECK (created_by IN ('parent', 'child')),
    created_at TEXT NOT NULL,
    UNIQUE (member_id, subject, label)
);

-- One row per ticked item per school day. `key` is the lower-case label, so an item needed by two subjects is ticked once.
CREATE TABLE kid_bag_ticks (
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    day TEXT NOT NULL,
    key TEXT NOT NULL,
    ticked_at TEXT NOT NULL,
    PRIMARY KEY (member_id, day, key)
);

ALTER TABLE kid_phone_access ADD COLUMN share_activities INTEGER NOT NULL DEFAULT 1 CHECK (share_activities IN (0, 1));
ALTER TABLE kid_phone_access ADD COLUMN share_bag INTEGER NOT NULL DEFAULT 1 CHECK (share_bag IN (0, 1));

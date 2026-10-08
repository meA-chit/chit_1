-- Owned by kids/kid-view: a child's own phone (ADR-0012).
-- A parent enables the phone view per child and chooses what it may show; pairing is a single-use QR secret plus a code
-- shown only on the parent's screen. Secrets, codes and device tokens are stored as hashes, never in clear.

CREATE TABLE kid_phone_access (
    member_id TEXT PRIMARY KEY REFERENCES household_members(id) ON DELETE CASCADE,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    enabled INTEGER NOT NULL DEFAULT 0 CHECK (enabled IN (0, 1)),
    -- what the phone may show; grades and health are off until a parent turns them on (strict privacy class)
    share_timetable INTEGER NOT NULL DEFAULT 1 CHECK (share_timetable IN (0, 1)),
    share_stars INTEGER NOT NULL DEFAULT 1 CHECK (share_stars IN (0, 1)),
    share_reminders INTEGER NOT NULL DEFAULT 1 CHECK (share_reminders IN (0, 1)),
    share_grades INTEGER NOT NULL DEFAULT 0 CHECK (share_grades IN (0, 1)),
    share_health INTEGER NOT NULL DEFAULT 0 CHECK (share_health IN (0, 1)),
    updated_at TEXT NOT NULL
);

CREATE TABLE kid_phone_pairings (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    secret_hash TEXT NOT NULL UNIQUE,      -- sha256 of the QR secret
    code_salt TEXT NOT NULL,
    code_hash TEXT NOT NULL,               -- sha256(salt + 6-digit code)
    attempts INTEGER NOT NULL DEFAULT 0,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'used', 'cancelled', 'locked')),
    created_at TEXT NOT NULL
);
CREATE INDEX kid_phone_pairings_by_member ON kid_phone_pairings(member_id, status);

CREATE TABLE kid_phone_devices (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,       -- sha256 of the device token; the token itself lives only on the phone
    label TEXT,
    paired_at TEXT NOT NULL,
    last_seen_at TEXT,
    revoked_at TEXT
);
CREATE INDEX kid_phone_devices_by_member ON kid_phone_devices(member_id);

-- One-use bridge from Safari to the Home Screen app, which has its own storage on iOS.
CREATE TABLE kid_phone_handoffs (
    token_hash TEXT PRIMARY KEY,
    device_id TEXT NOT NULL REFERENCES kid_phone_devices(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0 CHECK (used IN (0, 1))
);

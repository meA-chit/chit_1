-- Stored enablement (docs/core/enablement-and-audiences.md layers 3 and 4).
-- modules_configured = 0: household never chose, platform defaults apply (all modules).
-- modules_restricted = 0: member inherits the household's modules.
ALTER TABLE households ADD COLUMN modules_configured INTEGER NOT NULL DEFAULT 0
    CHECK (modules_configured IN (0, 1));
ALTER TABLE household_members ADD COLUMN modules_restricted INTEGER NOT NULL DEFAULT 0
    CHECK (modules_restricted IN (0, 1));

CREATE TABLE household_modules (
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    module_id TEXT NOT NULL CHECK (length(module_id) > 0),
    PRIMARY KEY (household_id, module_id)
);

CREATE TABLE member_modules (
    member_id TEXT NOT NULL REFERENCES household_members(id) ON DELETE CASCADE,
    module_id TEXT NOT NULL CHECK (length(module_id) > 0),
    PRIMARY KEY (member_id, module_id)
);

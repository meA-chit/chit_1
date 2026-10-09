-- The household type (single, couple, family, shared flat) decides who a household may add: a single household has one
-- adult, a couple two, a flat adults only, and only a family has children. Existing households become 'family' when they
-- have a child, otherwise a type that fits their adults. The rules live in code (documents.py), so a new type needs no migration.
ALTER TABLE households ADD COLUMN household_type TEXT NOT NULL DEFAULT 'family';
UPDATE households SET household_type = CASE
    WHEN EXISTS (SELECT 1 FROM household_members m WHERE m.household_id = households.id AND m.role = 'child') THEN 'family'
    WHEN (SELECT COUNT(*) FROM household_members m WHERE m.household_id = households.id AND m.role = 'adult') = 1 THEN 'single'
    WHEN (SELECT COUNT(*) FROM household_members m WHERE m.household_id = households.id AND m.role = 'adult') = 2 THEN 'couple'
    ELSE 'shared' END;

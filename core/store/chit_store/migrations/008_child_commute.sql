-- How a child gets to school and to regular activities, and who goes along.
-- commute_mode: walk | cycle | car (NULL = not set; the timeline then falls back to the listed drop-off/pick-up adults).
-- escort: independent | parent (a parent goes along; escort_adult_id says which one, validated by the store).
ALTER TABLE child_settings ADD COLUMN commute_mode TEXT CHECK (commute_mode IS NULL OR commute_mode IN ('walk', 'cycle', 'car'));
ALTER TABLE child_activities ADD COLUMN commute_mode TEXT CHECK (commute_mode IS NULL OR commute_mode IN ('walk', 'cycle', 'car'));
ALTER TABLE child_activities ADD COLUMN travel_minutes INTEGER CHECK (travel_minutes IS NULL OR travel_minutes >= 0);
ALTER TABLE child_activities ADD COLUMN escort TEXT NOT NULL DEFAULT 'independent' CHECK (escort IN ('independent', 'parent'));
ALTER TABLE child_activities ADD COLUMN escort_adult_id TEXT;

-- Member identity on the dashboard (predefined illustrations only, never photos) and the
-- routine fields the family timeline needs. Household coordinates are optional and feed weather.
ALTER TABLE household_members ADD COLUMN avatar TEXT;
ALTER TABLE household_members ADD COLUMN color TEXT;
ALTER TABLE households ADD COLUMN latitude REAL CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90);
ALTER TABLE households ADD COLUMN longitude REAL CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180);
ALTER TABLE child_settings ADD COLUMN dropoff_time TEXT;

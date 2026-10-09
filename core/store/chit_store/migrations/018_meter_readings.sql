-- Manually entered cumulative meter readings (energy module, Grid page). One row per household, meter and day.
-- `meter` is validated in code (water_total, water_garden today) so a new meter needs no migration. Values are the number
-- the meter shows (cubic metres for water), always counting up; usage is the difference between two readings.
CREATE TABLE meter_readings (
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    meter TEXT NOT NULL CHECK (length(meter) > 0),
    read_on TEXT NOT NULL,
    value REAL NOT NULL CHECK (value >= 0),
    note TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (household_id, meter, read_on)
);

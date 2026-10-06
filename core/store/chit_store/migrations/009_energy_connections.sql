-- Credentials and settings for external energy providers (Tibber, SolarEdge), one row per household and provider.
-- `secret` is a credential (data class: secret). It is only ever read by the hub's own server-side code, never
-- returned by any API, never exported, never part of seed documents. Under SQLCipher it is encrypted at rest;
-- in the unencrypted dev mode (ADR-0010) it is plain, so use a throw-away or read-only key there.
CREATE TABLE energy_connections (
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('tibber', 'solaredge')),
    secret TEXT NOT NULL CHECK (length(secret) > 0),
    config TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (household_id, provider)
);

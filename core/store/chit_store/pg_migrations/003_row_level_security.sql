-- Row-level security (ADR-0015). A connection serves ONE household, named by the session setting app.household_id, which
-- the server sets per request from the authenticated user (never from request data). Every tenant table then shows and
-- accepts only that household's rows, whatever the query says.
--
--   * Policies bind PUBLIC, so every non-owner role (the application role) is confined. The table owner (migrations,
--     the import tool, admin tasks) is deliberately NOT forced, so it still sees everything.
--   * An unset or empty setting matches nothing: the default is fail-closed.
--   * USING filters reads/updates/deletes; WITH CHECK refuses writes into another household, including moving a row.

DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT table_name FROM information_schema.columns
        WHERE table_schema = current_schema() AND column_name = 'household_id'
          AND table_name IN (SELECT table_name FROM information_schema.tables
                             WHERE table_schema = current_schema() AND table_type = 'BASE TABLE')
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format($p$CREATE POLICY tenant_isolation ON %I
            USING (household_id = current_setting('app.household_id', true))
            WITH CHECK (household_id = current_setting('app.household_id', true))$p$, t);
    END LOOP;
END $$;

ALTER TABLE households ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON households
    USING (id = current_setting('app.household_id', true))
    WITH CHECK (id = current_setting('app.household_id', true));

-- Lookups that must happen BEFORE the household is known. They run as the table owner, return nothing but a household id,
-- and have a fixed search_path (a SECURITY DEFINER function must not trust the caller's).
SELECT set_config('search_path', current_schema(), true);

-- A kid phone presents a credential (device token, handoff, pairing secret or link code); only its hash is stored.
CREATE FUNCTION chit_household_for_phone_credential(p_kind TEXT, p_hash TEXT) RETURNS TEXT
LANGUAGE sql STABLE SECURITY DEFINER SET search_path FROM CURRENT AS $$
    SELECT CASE p_kind
        WHEN 'device'         THEN (SELECT household_id FROM kid_phone_devices  WHERE token_hash  = p_hash AND revoked_at IS NULL)
        WHEN 'handoff'        THEN (SELECT household_id FROM kid_phone_handoffs WHERE token_hash  = p_hash AND used = 0)
        WHEN 'pairing_secret' THEN (SELECT household_id FROM kid_phone_pairings WHERE secret_hash = p_hash AND status = 'pending')
        WHEN 'pairing_link'   THEN (SELECT household_id FROM kid_phone_pairings WHERE link_hash   = p_hash AND status = 'pending')
    END
$$;

-- Single-household mode (local hub and the current pilot, before accounts exist): "the latest household". It answers only
-- when the connection announces that mode, so a multi-household deployment never gets an answer from it.
CREATE FUNCTION chit_latest_household_id() RETURNS TEXT
LANGUAGE sql STABLE SECURITY DEFINER SET search_path FROM CURRENT AS $$
    SELECT CASE WHEN current_setting('app.single_household', true) = 'on'
                THEN (SELECT id FROM households ORDER BY created_at DESC, seq DESC LIMIT 1) END
$$;

REVOKE ALL ON FUNCTION chit_household_for_phone_credential(TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION chit_latest_household_id() FROM PUBLIC;

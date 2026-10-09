-- Accounts, pairings, email codes and sessions (ADR-0014). These tables describe PEOPLE and their access, not household
-- content, so they are not under the household row-level policy: a sign-in happens before any household is chosen. Only
-- chit_store.accounts reads or writes them, and every secret (pairing link, codes, session token) is stored as a hash.

CREATE TABLE auth_accounts (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL CHECK (length(email) BETWEEN 3 AND 254),
    created_at TEXT NOT NULL,
    disabled_at TEXT
);
CREATE UNIQUE INDEX auth_accounts_by_email ON auth_accounts (lower(email));

-- One account can belong to several households (split families); one household member belongs to at most one account.
CREATE TABLE auth_memberships (
    account_id TEXT NOT NULL REFERENCES auth_accounts(id) ON DELETE CASCADE,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'adult')),
    created_at TEXT NOT NULL,
    PRIMARY KEY (account_id, household_id),
    UNIQUE (household_id, member_id),
    FOREIGN KEY (member_id, household_id) REFERENCES household_members(id, household_id) ON DELETE CASCADE
);
-- exactly one owner account per household
CREATE UNIQUE INDEX auth_memberships_one_owner ON auth_memberships (household_id) WHERE role = 'owner';

-- An invitation for a household member: a link token plus a 6-digit code, shared on different channels.
CREATE TABLE auth_pairings (
    id TEXT PRIMARY KEY,
    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'adult')),
    link_hash TEXT NOT NULL UNIQUE,
    code_salt TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'used', 'cancelled', 'locked')),
    created_by TEXT NOT NULL,                 -- 'operator' or the inviting account id
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (member_id, household_id) REFERENCES household_members(id, household_id) ON DELETE CASCADE
);
CREATE INDEX auth_pairings_by_member ON auth_pairings (household_id, member_id, status);

-- Issued after the pairing code is accepted; carries the person through the Terms and email steps.
CREATE TABLE auth_enrolments (
    token_hash TEXT PRIMARY KEY,
    pairing_id TEXT NOT NULL REFERENCES auth_pairings(id) ON DELETE CASCADE,
    terms_version TEXT,                       -- set when the person ticks the Terms box
    expires_at TEXT NOT NULL
);

CREATE TABLE auth_email_codes (
    id TEXT PRIMARY KEY,
    purpose TEXT NOT NULL CHECK (purpose IN ('enrol', 'login', 'reauth')),
    email TEXT NOT NULL,
    context TEXT,                             -- enrolment token hash (enrol) or session id (reauth)
    code_salt TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT
);
CREATE INDEX auth_email_codes_by_email ON auth_email_codes (lower(email), purpose, created_at);

CREATE TABLE auth_sessions (
    id TEXT PRIMARY KEY,
    token_hash TEXT NOT NULL UNIQUE,
    account_id TEXT NOT NULL REFERENCES auth_accounts(id) ON DELETE CASCADE,
    household_id TEXT REFERENCES households(id) ON DELETE SET NULL,   -- the household this session serves
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    reauth_at TEXT,                           -- last fresh email-code confirmation, for sensitive actions
    revoked_at TEXT,
    user_agent TEXT
);
CREATE INDEX auth_sessions_by_account ON auth_sessions (account_id);

CREATE TABLE auth_terms_acceptances (
    account_id TEXT NOT NULL REFERENCES auth_accounts(id) ON DELETE CASCADE,
    terms_version TEXT NOT NULL,
    accepted_at TEXT NOT NULL,
    PRIMARY KEY (account_id, terms_version)
);

-- Attempt log for rate limits that hold across restarts and instances. `key` is a hash, never a raw address.
CREATE TABLE auth_events (
    kind TEXT NOT NULL,
    key TEXT NOT NULL,
    at TEXT NOT NULL
);
CREATE INDEX auth_events_lookup ON auth_events (kind, key, at);

-- The household picker needs the names of an account's households, which sit behind the household policy.
SELECT set_config('search_path', current_schema(), true);
CREATE FUNCTION chit_households_for_account(p_account TEXT) RETURNS TABLE (household_id TEXT, name TEXT, role TEXT)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path FROM CURRENT AS $$
    SELECT m.household_id, h.name, m.role FROM auth_memberships m JOIN households h ON h.id = m.household_id
    WHERE m.account_id = p_account ORDER BY h.name
$$;
REVOKE ALL ON FUNCTION chit_households_for_account(TEXT) FROM PUBLIC;

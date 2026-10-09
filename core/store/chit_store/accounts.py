"""Accounts, pairing enrolment, email-code sign-in and sessions (ADR-0014). Postgres backend only.

Who may do what is decided here and nowhere else:
  * a person is enrolled by a PAIRING (link + 6-digit code, shared on different channels) issued by the operator or the
    household owner, then accepts the Terms and verifies an email address with a code;
  * afterwards they sign in with an email code (15 minutes, single use); there are no passwords;
  * a session names the household it serves, and the server turns that into the row-level-security scope.
Every secret (pairing link, codes, session token) is stored only as a hash. Rate limits live in the database so they hold
across restarts and instances.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

PAIRING_TTL = timedelta(minutes=30)
CODE_TTL = timedelta(minutes=15)
SESSION_TTL = timedelta(days=30)
TOUCH_EVERY = timedelta(hours=1)
REAUTH_WINDOW = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=30)
MAX_ATTEMPTS = 5            # wrong guesses per pairing or per emailed code
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,}$")


class AuthError(Exception):
    def __init__(self, status: int, code: str, message: str, **extra: Any):
        super().__init__(message)
        self.status, self.code, self.message, self.extra = status, code, message, extra


@dataclass
class Session:
    id: str
    account_id: str
    email: str
    household_id: "str | None"
    role: "str | None"             # 'owner' | 'adult' in the active household
    member_id: "str | None"
    terms_ok: bool
    reauth_at: "datetime | None"


def _iso(moment: datetime) -> str:
    """Fixed-width UTC text, so string comparison in SQL is time comparison."""
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def _parse(text: str) -> datetime:
    return datetime.fromisoformat(text)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _six_digits() -> str:
    return "%06d" % secrets.randbelow(1_000_000)


def normalize_email(value: Any) -> str:
    email = str(value or "").strip().lower()
    if len(email) > 254 or not EMAIL.match(email):
        raise AuthError(400, "invalid_email", "Please enter a valid email address.")
    return email


class Accounts:
    def __init__(self, store: Any, mailer: Any, terms_version: str, clock: "Callable[[], datetime] | None" = None,
                 pepper: str = "", log: "Callable[[str], None] | None" = None):
        if getattr(store, "backend", None) != "postgres":
            raise ValueError("accounts need the postgres backend (ADR-0014)")
        self.store, self.mailer, self.terms_version, self.pepper = store, mailer, terms_version, pepper
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.log = log or (lambda message: None)
        # Mail goes out on a background thread so a known address and an unknown one answer equally fast (no account probing).
        self.async_mail = True

    # ------------------------------------------------------------------ limits
    def _limit(self, kind: str, key: str, maximum: int, window: timedelta = timedelta(hours=1)) -> None:
        digest, now = _hash(self.pepper + key), self.clock()
        with self.store._connection() as c:
            used = c.execute("SELECT count(*) FROM auth_events WHERE kind = ? AND key = ? AND at > ?",
                             (kind, digest, _iso(now - window))).fetchone()[0]
            if used >= maximum:
                raise AuthError(429, "rate_limited", "Too many tries. Please wait a while and try again.")
            c.execute("INSERT INTO auth_events(kind, key, at) VALUES (?, ?, ?)", (kind, digest, _iso(now)))
            if secrets.randbelow(100) == 0:
                c.execute("DELETE FROM auth_events WHERE at < ?", (_iso(now - timedelta(days=2)),))

    # ---------------------------------------------------------------- pairings
    def issue_pairing(self, household_id: str, member_id: str, role: str, created_by: str) -> dict[str, Any]:
        """Invite the person behind an adult household member. Returns the link token and the code, to be shared separately."""
        if role not in ("owner", "adult"):
            raise ValueError("role must be owner or adult")
        now = self.clock()
        link, code, salt = secrets.token_urlsafe(24), _six_digits(), secrets.token_hex(8)
        pairing_id = secrets.token_urlsafe(12)
        with self.store._connection() as c:
            member = c.execute("SELECT role FROM household_members WHERE id = ? AND household_id = ?", (member_id, household_id)).fetchone()
            if not member or member[0] != "adult":
                raise AuthError(404, "no_such_member", "That person is not an adult in this household.")
            c.execute("BEGIN IMMEDIATE")
            try:
                c.execute("UPDATE auth_pairings SET status = 'cancelled' WHERE household_id = ? AND member_id = ? AND status IN ('pending', 'verified')",
                          (household_id, member_id))
                c.execute("INSERT INTO auth_pairings(id, household_id, member_id, role, link_hash, code_salt, code_hash, created_by, created_at, expires_at) "
                          "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (pairing_id, household_id, member_id, role, _hash(link), salt, _hash(salt + code), created_by, _iso(now), _iso(now + PAIRING_TTL)))
                c.commit()
            except Exception:
                c.rollback()
                raise
        return {"pairing_id": pairing_id, "link": link, "code": code, "expires_at": _iso(now + PAIRING_TTL)}

    def redeem_pairing(self, link: str, code: str, ip: str) -> str:
        """Check the link and its code. Returns an enrolment token for the Terms and email steps."""
        self._limit("pair_ip", ip, 20)
        now = self.clock()
        invalid = AuthError(410, "pairing_invalid", "This invitation has expired or was already used. Ask for a new one.")
        with self.store._connection() as c:
            c.execute("BEGIN IMMEDIATE")
            try:
                row = c.execute("SELECT id, code_salt, code_hash, attempts, status, expires_at FROM auth_pairings WHERE link_hash = ? FOR UPDATE",
                                (_hash(str(link or "")),)).fetchone()
                if not row or row[4] not in ("pending", "verified") or _parse(row[5]) <= now:
                    c.commit()
                    raise invalid
                pairing_id, salt, code_hash, attempts = row[0], row[1], row[2], row[3]
                if not hmac.compare_digest(_hash(salt + str(code or "").replace(" ", "")), code_hash):
                    attempts += 1
                    locked = attempts >= MAX_ATTEMPTS
                    c.execute("UPDATE auth_pairings SET attempts = ?, status = ? WHERE id = ?", (attempts, "locked" if locked else row[4], pairing_id))
                    c.commit()
                    if locked:
                        raise AuthError(423, "pairing_locked", "Too many wrong codes. Ask for a new invitation.")
                    raise AuthError(403, "wrong_code", "That code is not right.", attempts_left=MAX_ATTEMPTS - attempts)
                token = secrets.token_urlsafe(32)
                c.execute("DELETE FROM auth_enrolments WHERE pairing_id = ?", (pairing_id,))
                c.execute("UPDATE auth_pairings SET status = 'verified' WHERE id = ?", (pairing_id,))
                c.execute("INSERT INTO auth_enrolments(token_hash, pairing_id, expires_at) VALUES (?, ?, ?)", (_hash(token), pairing_id, row[5]))
                c.commit()
                return token
            except AuthError:
                raise
            except Exception:
                c.rollback()
                raise

    def _enrolment(self, c: Any, token: str, now: datetime) -> tuple:
        row = c.execute("SELECT e.pairing_id, e.terms_version, p.household_id, p.member_id, p.role, p.status FROM auth_enrolments e "
                        "JOIN auth_pairings p ON p.id = e.pairing_id WHERE e.token_hash = ? AND e.expires_at > ?",
                        (_hash(str(token or "")), _iso(now))).fetchone()
        if not row or row[5] != "verified":
            raise AuthError(410, "enrolment_expired", "This sign-up has expired. Start again from your invitation.")
        return row

    # --------------------------------------------------------------- email codes
    def _send_code(self, c: Any, purpose: str, email: str, context: "str | None") -> None:
        now = self.clock()
        last = c.execute("SELECT created_at FROM auth_email_codes WHERE purpose = ? AND lower(email) = ? AND coalesce(context, '') = ? "
                         "ORDER BY created_at DESC LIMIT 1", (purpose, email, context or "")).fetchone()
        if last and now - _parse(last[0]) < RESEND_COOLDOWN:
            return                                  # a code was just sent; do not let the form be used to flood a mailbox
        code, salt = _six_digits(), secrets.token_hex(8)
        c.execute("UPDATE auth_email_codes SET used_at = ? WHERE purpose = ? AND lower(email) = ? AND coalesce(context, '') = ? AND used_at IS NULL",
                  (_iso(now), purpose, email, context or ""))
        c.execute("INSERT INTO auth_email_codes(id, purpose, email, context, code_salt, code_hash, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (secrets.token_urlsafe(12), purpose, email, context, salt, _hash(salt + code), _iso(now), _iso(now + CODE_TTL)))
        self._deliver(email, purpose, code)

    def _deliver(self, email: str, purpose: str, code: str) -> None:
        def send() -> None:
            try:
                self.mailer.send_code(email, purpose, code)
            except Exception as error:              # the caller learns nothing either way; the operator sees it in the log
                self.log("mail not sent (%s): %s" % (purpose, type(error).__name__))
        if self.async_mail:
            threading.Thread(target=send, daemon=True).start()
        else:
            send()

    def _check_code(self, c: Any, purpose: str, email: str, context: "str | None", code: str) -> bool:
        """Inside a transaction: spend one attempt, and consume the code when it matches. Atomic: a code works once."""
        now = self.clock()
        row = c.execute("SELECT id, code_salt, code_hash, attempts FROM auth_email_codes WHERE purpose = ? AND lower(email) = ? "
                        "AND coalesce(context, '') = ? AND used_at IS NULL AND expires_at > ? ORDER BY created_at DESC LIMIT 1 FOR UPDATE",
                        (purpose, email, context or "", _iso(now))).fetchone()
        if not row or row[3] >= MAX_ATTEMPTS:
            return False
        c.execute("UPDATE auth_email_codes SET attempts = attempts + 1 WHERE id = ?", (row[0],))
        if not hmac.compare_digest(_hash(row[1] + str(code or "").replace(" ", "")), row[2]):
            return False
        return c.execute("UPDATE auth_email_codes SET used_at = ? WHERE id = ? AND used_at IS NULL RETURNING id", (_iso(now), row[0])).fetchone() is not None

    def _verify(self, purpose: str, email: str, context: "str | None", code: str, then: "Callable[[Any], Any]") -> Any:
        """Run `then(connection)` in the same transaction as a successful code check; failures keep the spent attempt."""
        with self.store._connection() as c:
            c.execute("BEGIN IMMEDIATE")
            try:
                if not self._check_code(c, purpose, email, context, code):
                    c.commit()
                    raise AuthError(403, "wrong_code", "That code is not right or has expired.")
                result = then(c)
                c.commit()
                return result
            except AuthError:
                c.rollback()                        # (a no-op after the wrong-code commit above)
                raise
            except Exception:
                c.rollback()
                raise

    # ----------------------------------------------------------------- enrolment
    def enrol_send_code(self, enrolment: str, email: str, accept_terms: Any, terms_version: Any, ip: str) -> None:
        email = normalize_email(email)
        if accept_terms is not True or terms_version != self.terms_version:
            raise AuthError(400, "terms_required", "Please accept the Terms of Use to continue.", terms_version=self.terms_version)
        self._limit("code_send_ip", ip, 20)
        self._limit("code_send_email", email, 5)
        now = self.clock()
        with self.store._connection() as c:
            self._enrolment(c, enrolment, now)
            c.execute("UPDATE auth_enrolments SET terms_version = ? WHERE token_hash = ?", (self.terms_version, _hash(enrolment)))
            self._send_code(c, "enrol", email, _hash(enrolment))

    def enrol_complete(self, enrolment: str, email: str, code: str, ip: str, user_agent: str = "") -> tuple[str, dict[str, Any]]:
        email = normalize_email(email)
        self._limit("code_verify_ip", ip, 40)
        self._limit("code_verify_email", email, 20)
        now = self.clock()

        def finish(c: Any) -> tuple[str, dict[str, Any]]:
            pairing_id, terms, household_id, member_id, role, _ = self._enrolment(c, enrolment, now)
            if terms != self.terms_version:
                raise AuthError(400, "terms_required", "Please accept the Terms of Use to continue.", terms_version=self.terms_version)
            if c.execute("UPDATE auth_pairings SET status = 'used' WHERE id = ? AND status = 'verified' RETURNING id", (pairing_id,)).fetchone() is None:
                raise AuthError(410, "pairing_invalid", "This invitation was already used.")
            account = c.execute("SELECT id, disabled_at FROM auth_accounts WHERE lower(email) = ?", (email,)).fetchone()
            if account and account[1]:
                raise AuthError(403, "account_disabled", "This account is not active.")
            account_id = account[0] if account else secrets.token_urlsafe(12)
            if not account:
                c.execute("INSERT INTO auth_accounts(id, email, created_at) VALUES (?, ?, ?)", (account_id, email, _iso(now)))
            if c.execute("SELECT 1 FROM auth_memberships WHERE account_id = ? AND household_id = ? AND member_id <> ?",
                         (account_id, household_id, member_id)).fetchone():
                raise AuthError(409, "email_in_use", "This email already belongs to someone else in this household.")
            # re-pairing a member (lost mailbox, new address) replaces whoever held that seat before
            old = c.execute("SELECT account_id FROM auth_memberships WHERE household_id = ? AND member_id = ? AND account_id <> ?",
                            (household_id, member_id, account_id)).fetchone()
            if old:
                c.execute("DELETE FROM auth_memberships WHERE household_id = ? AND member_id = ?", (household_id, member_id))
                c.execute("UPDATE auth_sessions SET household_id = NULL WHERE account_id = ? AND household_id = ?", (old[0], household_id))
            c.execute("INSERT INTO auth_memberships(account_id, household_id, member_id, role, created_at) VALUES (?, ?, ?, ?, ?) "
                      "ON CONFLICT (account_id, household_id) DO NOTHING", (account_id, household_id, member_id, role, _iso(now)))
            c.execute("INSERT INTO auth_terms_acceptances(account_id, terms_version, accepted_at) VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                      (account_id, terms, _iso(now)))
            c.execute("DELETE FROM auth_enrolments WHERE pairing_id = ?", (pairing_id,))
            token = self._new_session(c, account_id, household_id, user_agent)
            return token, {"household_id": household_id}

        return self._verify("enrol", email, _hash(enrolment), code, finish)

    # ------------------------------------------------------------------- sign-in
    def login_send_code(self, email: str, ip: str) -> None:
        """Always succeeds from the caller's point of view, whether or not the address has an account."""
        email = normalize_email(email)
        self._limit("code_send_ip", ip, 20)
        self._limit("code_send_email", email, 5)
        with self.store._connection() as c:
            if c.execute("SELECT 1 FROM auth_accounts WHERE lower(email) = ? AND disabled_at IS NULL", (email,)).fetchone():
                self._send_code(c, "login", email, None)

    def login_verify(self, email: str, code: str, ip: str, user_agent: str = "") -> str:
        email = normalize_email(email)
        self._limit("code_verify_ip", ip, 40)
        self._limit("code_verify_email", email, 20)

        def finish(c: Any) -> str:
            account = c.execute("SELECT id FROM auth_accounts WHERE lower(email) = ? AND disabled_at IS NULL", (email,)).fetchone()
            if not account:
                raise AuthError(403, "wrong_code", "That code is not right or has expired.")
            households = c.execute("SELECT household_id FROM auth_memberships WHERE account_id = ?", (account[0],)).fetchall()
            return self._new_session(c, account[0], households[0][0] if len(households) == 1 else None, user_agent)

        return self._verify("login", email, None, code, finish)

    # ------------------------------------------------------------------ sessions
    def _new_session(self, c: Any, account_id: str, household_id: "str | None", user_agent: str) -> str:
        now, token = self.clock(), secrets.token_urlsafe(32)
        c.execute("INSERT INTO auth_sessions(id, token_hash, account_id, household_id, created_at, last_seen_at, expires_at, user_agent) "
                  "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (secrets.token_urlsafe(12), _hash(token), account_id, household_id, _iso(now), _iso(now), _iso(now + SESSION_TTL), (user_agent or "")[:200]))
        return token

    def authenticate(self, token: "str | None") -> "Session | None":
        if not token:
            return None
        now = self.clock()
        with self.store._connection() as c:
            row = c.execute("SELECT s.id, s.account_id, a.email, s.household_id, s.reauth_at, s.last_seen_at FROM auth_sessions s "
                            "JOIN auth_accounts a ON a.id = s.account_id WHERE s.token_hash = ? AND s.revoked_at IS NULL AND s.expires_at > ? "
                            "AND a.disabled_at IS NULL", (_hash(token), _iso(now))).fetchone()
            if not row:
                return None
            role = member_id = None
            if row[3]:
                membership = c.execute("SELECT role, member_id FROM auth_memberships WHERE account_id = ? AND household_id = ?", (row[1], row[3])).fetchone()
                if membership:
                    role, member_id = membership
            household_id = row[3] if role else None
            terms_ok = c.execute("SELECT 1 FROM auth_terms_acceptances WHERE account_id = ? AND terms_version = ?",
                                 (row[1], self.terms_version)).fetchone() is not None
            if now - _parse(row[5]) > TOUCH_EVERY:                     # sliding expiry, written at most once an hour
                c.execute("UPDATE auth_sessions SET last_seen_at = ?, expires_at = ? WHERE id = ?", (_iso(now), _iso(now + SESSION_TTL), row[0]))
            return Session(row[0], row[1], row[2], household_id, role, member_id, terms_ok, _parse(row[4]) if row[4] else None)

    def logout(self, session: Session) -> None:
        with self.store._connection() as c:
            c.execute("UPDATE auth_sessions SET revoked_at = ? WHERE id = ?", (_iso(self.clock()), session.id))

    def list_sessions(self, session: Session) -> list[dict[str, Any]]:
        with self.store._connection() as c:
            rows = c.execute("SELECT id, created_at, last_seen_at, user_agent FROM auth_sessions WHERE account_id = ? AND revoked_at IS NULL "
                             "AND expires_at > ? ORDER BY created_at", (session.account_id, _iso(self.clock()))).fetchall()
        return [{"id": r[0], "created_at": r[1], "last_seen_at": r[2], "device": r[3], "current": r[0] == session.id} for r in rows]

    def revoke_session(self, session: Session, session_id: str) -> None:
        with self.store._connection() as c:
            if c.execute("UPDATE auth_sessions SET revoked_at = ? WHERE id = ? AND account_id = ? AND revoked_at IS NULL RETURNING id",
                         (_iso(self.clock()), session_id, session.account_id)).fetchone() is None:
                raise AuthError(404, "no_such_session", "No such session.")

    def select_household(self, session: Session, household_id: str) -> None:
        with self.store._connection() as c:
            if not c.execute("SELECT 1 FROM auth_memberships WHERE account_id = ? AND household_id = ?", (session.account_id, household_id)).fetchone():
                raise AuthError(403, "not_a_member", "You are not a member of that household.")
            c.execute("UPDATE auth_sessions SET household_id = ? WHERE id = ?", (household_id, session.id))

    def accept_terms(self, session: Session, version: Any) -> None:
        if version != self.terms_version:
            raise AuthError(400, "terms_version", "These are not the current Terms.", terms_version=self.terms_version)
        with self.store._connection() as c:
            c.execute("INSERT INTO auth_terms_acceptances(account_id, terms_version, accepted_at) VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                      (session.account_id, version, _iso(self.clock())))

    def me(self, session: Session) -> dict[str, Any]:
        with self.store._connection() as c:
            households = c.execute("SELECT household_id, name, role FROM chit_households_for_account(?)", (session.account_id,)).fetchall()
        return {"email": session.email, "household_id": session.household_id, "role": session.role,
                "households": [{"id": h[0], "name": h[1], "role": h[2]} for h in households],
                "terms": {"version": self.terms_version, "accepted": session.terms_ok}}

    # -------------------------------------------------------- sensitive actions
    def reauth_send_code(self, session: Session, ip: str) -> None:
        self._limit("code_send_ip", ip, 20)
        self._limit("code_send_email", session.email, 5)
        with self.store._connection() as c:
            self._send_code(c, "reauth", session.email, session.id)

    def reauth_verify(self, session: Session, code: str, ip: str) -> None:
        self._limit("code_verify_ip", ip, 40)
        self._limit("code_verify_email", session.email, 20)
        now = self.clock()
        self._verify("reauth", session.email, session.id, code,
                     lambda c: c.execute("UPDATE auth_sessions SET reauth_at = ? WHERE id = ?", (_iso(now), session.id)))

    def require_owner(self, session: Session, fresh: bool = False) -> None:
        if session.role != "owner":
            raise AuthError(403, "owner_only", "Only the household owner can do this.")
        if fresh and (not session.reauth_at or self.clock() - session.reauth_at > REAUTH_WINDOW):
            raise AuthError(403, "reauth_required", "Please confirm it is you with a fresh email code first.")

    def invite_adult(self, session: Session, member_id: str) -> dict[str, Any]:
        self.require_owner(session)
        with self.store._connection() as c:
            row = c.execute("SELECT 1 FROM auth_memberships WHERE household_id = ? AND member_id = ? AND role = 'owner'", (session.household_id, member_id)).fetchone()
        if row:
            raise AuthError(400, "is_owner", "That is you.")
        return self.issue_pairing(session.household_id, member_id, "adult", session.account_id)

    def members(self, session: Session) -> list[dict[str, Any]]:
        self.require_owner(session)
        with self.store._connection() as c:
            rows = c.execute("SELECT m.id, m.name, m.role, a.role, a.account_id IS NOT NULL FROM household_members m "
                             "LEFT JOIN auth_memberships a ON a.household_id = m.household_id AND a.member_id = m.id "
                             "WHERE m.household_id = ? ORDER BY m.seq", (session.household_id,)).fetchall()
        return [{"id": r[0], "name": r[1], "role": r[2], "access": r[3], "has_account": bool(r[4])} for r in rows]

    def transfer_ownership(self, session: Session, member_id: str) -> None:
        self.require_owner(session, fresh=True)
        with self.store._connection() as c:
            c.execute("BEGIN IMMEDIATE")
            try:
                target = c.execute("SELECT account_id FROM auth_memberships WHERE household_id = ? AND member_id = ?", (session.household_id, member_id)).fetchone()
                if not target or target[0] == session.account_id:
                    raise AuthError(400, "cannot_transfer", "Ownership can only go to another adult who has already signed in.")
                c.execute("UPDATE households SET owner_member_id = ? WHERE id = ?", (member_id, session.household_id))   # trigger: must be an adult here
                c.execute("UPDATE auth_memberships SET role = 'adult' WHERE household_id = ? AND account_id = ?", (session.household_id, session.account_id))
                c.execute("UPDATE auth_memberships SET role = 'owner' WHERE household_id = ? AND account_id = ?", (session.household_id, target[0]))
                c.execute("UPDATE auth_sessions SET reauth_at = NULL WHERE account_id = ?", (session.account_id,))
                c.commit()
            except Exception:
                c.rollback()
                raise

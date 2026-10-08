"""A child's own phone: enablement, what it may show, QR + code pairing and device tokens (kids/kid-view, ADR-0012).

Nothing secret is stored in clear: the QR secret, the pairing code and the device token are kept as sha256 hashes.
The QR secret and device token carry 128+ bits, so a plain hash is enough; the 6-digit code is only ever checked
together with the secret and is locked after MAX_ATTEMPTS wrong tries.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Any

from .common import _member_id, _now

PAIRING_TTL = timedelta(minutes=10)
HANDOFF_TTL = timedelta(minutes=15)
MAX_ATTEMPTS = 5
SHARE_KEYS = ("timetable", "stars", "reminders", "homework", "activities", "bag", "grades", "health")
LINK_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # no 0/O/1/I: it is typed by hand
MAX_FAILURES = 20                                    # wrong pairing tries per FAILURE_WINDOW across all pairings
FAILURE_WINDOW = timedelta(minutes=10)
_SEEN_EVERY = timedelta(minutes=1)


class PairingError(Exception):
    """`reason` is invalid (unknown, expired, used or cancelled: deliberately not told apart), wrong_code or locked."""

    def __init__(self, reason: str, message: str, attempts_left: "int | None" = None):
        super().__init__(message)
        self.reason = reason
        self.attempts_left = attempts_left


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")


def _parse(text: str) -> datetime:
    return datetime.fromisoformat(text)


def _utc(now: "datetime | None") -> datetime:
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc)


class KidPhone:
    PairingError = PairingError

    # ---------- enablement and sharing ----------
    def _child_of(self, connection: Any, household_id: str, member_id: str) -> None:
        if not connection.execute("SELECT 1 FROM household_members WHERE id = ? AND household_id = ? AND role = 'child'",
                                  (member_id, household_id)).fetchone():
            raise LookupError("no such child in this household")

    def phone_settings(self, household_id: str, member_id: str) -> "dict[str, Any]":
        with self._connection() as connection:
            row = connection.execute(
                "SELECT enabled, share_timetable, share_stars, share_reminders, share_homework, share_activities, share_bag, share_grades, share_health FROM kid_phone_access "
                "WHERE member_id = ? AND household_id = ?", (member_id, household_id)).fetchone()
        if not row:
            return {"enabled": False, "share": {"timetable": True, "stars": True, "reminders": True, "homework": True, "activities": True, "bag": True, "grades": False, "health": False}}
        return {"enabled": bool(row[0]), "share": {key: bool(value) for key, value in zip(SHARE_KEYS, row[1:])}}

    def set_phone_settings(self, household_id: str, member_id: str, enabled: "bool | None" = None,
                           share: "dict[str, bool] | None" = None, now: "datetime | None" = None) -> "dict[str, Any]":
        """Switching a child's phone view off is a kill switch: every paired phone is revoked and open pairings are cancelled."""
        current = self.phone_settings(household_id, member_id)
        if enabled is not None and not isinstance(enabled, bool):
            raise ValueError("enabled must be true or false")
        merged = dict(current["share"])
        for key, value in (share or {}).items():
            if key not in SHARE_KEYS or not isinstance(value, bool):
                raise ValueError("share keys are %s and values true or false" % ", ".join(SHARE_KEYS))
            merged[key] = value
        turn_on = current["enabled"] if enabled is None else enabled
        stamp = _iso(_utc(now))
        with self._connection() as connection:
            self._child_of(connection, household_id, member_id)
            connection.execute(
                "INSERT INTO kid_phone_access(member_id, household_id, enabled, share_timetable, share_stars, share_reminders, share_homework, share_activities, share_bag, share_grades, share_health, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(member_id) DO UPDATE SET enabled = excluded.enabled, "
                "share_timetable = excluded.share_timetable, share_stars = excluded.share_stars, share_reminders = excluded.share_reminders, share_homework = excluded.share_homework, share_activities = excluded.share_activities, share_bag = excluded.share_bag, "
                "share_grades = excluded.share_grades, share_health = excluded.share_health, updated_at = excluded.updated_at",
                (member_id, household_id, int(turn_on), *(int(merged[key]) for key in SHARE_KEYS), stamp))
            if not turn_on:
                connection.execute("UPDATE kid_phone_devices SET revoked_at = ? WHERE member_id = ? AND revoked_at IS NULL", (stamp, member_id))
                connection.execute("UPDATE kid_phone_pairings SET status = 'cancelled' WHERE member_id = ? AND status = 'pending'", (member_id,))
        return {"enabled": turn_on, "share": merged}

    # ---------- pairing ----------
    def create_phone_pairing(self, household_id: str, member_id: str, now: "datetime | None" = None) -> "dict[str, str]":
        """-> {secret, link_code, code, expires_at}. Shown once; only hashes are stored. A new pairing cancels the previous open one.

        The secret rides in the QR; the link code (8 characters) is the same thing typed by hand, for an installed Home Screen app
        that cannot scan. Either way the 6-digit code from the parent's screen is also required."""
        if not self.phone_settings(household_id, member_id)["enabled"]:
            raise ValueError("turn the phone view on for this child first")
        moment = _utc(now)
        secret, code, salt = secrets.token_urlsafe(16), "%06d" % secrets.randbelow(1_000_000), secrets.token_hex(8)
        link = "".join(secrets.choice(LINK_ALPHABET) for _ in range(8))
        with self._connection() as connection:
            self._child_of(connection, household_id, member_id)
            connection.execute("UPDATE kid_phone_pairings SET status = 'cancelled' WHERE member_id = ? AND status = 'pending'", (member_id,))
            connection.execute(
                "INSERT INTO kid_phone_pairings(id, household_id, member_id, secret_hash, link_hash, code_salt, code_hash, expires_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (_member_id(), household_id, member_id, _hash(secret), _hash(link), salt, _hash(salt + code), _iso(moment + PAIRING_TTL), _iso(moment)))
        return {"secret": secret, "link_code": "%s-%s" % (link[:4], link[4:]), "code": code, "expires_at": _iso(moment + PAIRING_TTL)}

    def active_phone_pairing(self, household_id: str, member_id: str, now: "datetime | None" = None) -> "dict[str, Any] | None":
        with self._connection() as connection:
            row = connection.execute(
                "SELECT expires_at, attempts FROM kid_phone_pairings WHERE household_id = ? AND member_id = ? AND status = 'pending' "
                "ORDER BY created_at DESC LIMIT 1", (household_id, member_id)).fetchone()
        if not row or _parse(row[0]) <= _utc(now):
            return None
        return {"expires_at": row[0], "attempts_left": MAX_ATTEMPTS - row[1]}

    def cancel_phone_pairing(self, household_id: str, member_id: str) -> None:
        with self._connection() as connection:
            connection.execute("UPDATE kid_phone_pairings SET status = 'cancelled' WHERE household_id = ? AND member_id = ? AND status = 'pending'",
                               (household_id, member_id))

    def _throttled(self, moment: datetime) -> bool:
        recent = [t for t in KidPhone._failures if moment - t < FAILURE_WINDOW]
        KidPhone._failures[:] = recent
        return len(recent) >= MAX_FAILURES

    _failures: "list[datetime]" = []     # process-wide: wrong pairing tries, so a stranger cannot grind through link codes

    def complete_phone_pairing(self, secret: "str | None", code: str, label: "str | None" = None, now: "datetime | None" = None,
                               link: "str | None" = None) -> "dict[str, str]":
        """The phone presents the QR secret (or the typed link code) and the 6-digit code from the parent's screen. -> {token, device_id, member_id}."""
        moment = _utc(now)
        invalid = PairingError("invalid", "These codes have expired or were already used. Ask a parent for a new one.")
        if self._throttled(moment):
            raise PairingError("throttled", "Too many tries. Wait a few minutes and ask a parent to start again.")
        if secret:
            column, presented = "secret_hash", _hash(str(secret))
        else:
            column, presented = "link_hash", _hash("".join(ch for ch in str(link or "").upper() if ch.isalnum()))
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT id, household_id, member_id, code_salt, code_hash, attempts, expires_at FROM kid_phone_pairings "
                    "WHERE %s = ? AND status = 'pending'" % column, (presented,)).fetchone()
                if not row or _parse(row[6]) <= moment:
                    connection.commit()
                    KidPhone._failures.append(moment)
                    raise invalid
                pairing_id, household_id, member_id, salt, code_hash, attempts, _ = row
                if not hmac.compare_digest(_hash(salt + str(code).replace(" ", "")), code_hash):
                    attempts += 1
                    locked = attempts >= MAX_ATTEMPTS
                    connection.execute("UPDATE kid_phone_pairings SET attempts = ?, status = ? WHERE id = ?",
                                       (attempts, "locked" if locked else "pending", pairing_id))
                    connection.commit()
                    KidPhone._failures.append(moment)
                    if locked:
                        raise PairingError("locked", "Too many wrong codes. Ask a parent to start again.")
                    raise PairingError("wrong_code", "That code is not right. Check the screen and try again.", MAX_ATTEMPTS - attempts)
                access = connection.execute("SELECT enabled FROM kid_phone_access WHERE member_id = ?", (member_id,)).fetchone()
                if not access or not access[0]:
                    connection.commit()
                    raise invalid
                token, device_id = secrets.token_urlsafe(32), _member_id()
                connection.execute("UPDATE kid_phone_pairings SET status = 'used' WHERE id = ?", (pairing_id,))
                connection.execute(
                    "INSERT INTO kid_phone_devices(id, household_id, member_id, token_hash, label, paired_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (device_id, household_id, member_id, _hash(token), (label or "").strip()[:60] or None, _iso(moment), _iso(moment)))
                connection.commit()
            except PairingError:
                raise
            except Exception:
                connection.rollback()
                raise
        return {"token": token, "device_id": device_id, "member_id": member_id}

    # ---------- devices ----------
    def phone_device_for_token(self, token: str, now: "datetime | None" = None) -> "dict[str, str] | None":
        """The live device behind a bearer token, or None (unknown, revoked, or the child's phone view is off)."""
        if not token:
            return None
        moment = _utc(now)
        with self._connection() as connection:
            row = connection.execute(
                "SELECT d.id, d.household_id, d.member_id, d.last_seen_at FROM kid_phone_devices d "
                "JOIN kid_phone_access a ON a.member_id = d.member_id "
                "WHERE d.token_hash = ? AND d.revoked_at IS NULL AND a.enabled = 1", (_hash(token),)).fetchone()
            if not row:
                return None
            if not row[3] or moment - _parse(row[3]) > _SEEN_EVERY:
                connection.execute("UPDATE kid_phone_devices SET last_seen_at = ? WHERE id = ?", (_iso(moment), row[0]))
        return {"device_id": row[0], "household_id": row[1], "member_id": row[2]}

    def list_phone_devices(self, household_id: str, member_id: str) -> "list[dict[str, Any]]":
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, label, paired_at, last_seen_at FROM kid_phone_devices WHERE household_id = ? AND member_id = ? AND revoked_at IS NULL "
                "ORDER BY paired_at", (household_id, member_id)).fetchall()
        return [{"id": r[0], "label": r[1], "paired_at": r[2], "last_seen_at": r[3]} for r in rows]

    def revoke_phone_device(self, household_id: str, device_id: str, now: "datetime | None" = None) -> None:
        with self._connection() as connection:
            cursor = connection.execute("UPDATE kid_phone_devices SET revoked_at = ? WHERE id = ? AND household_id = ? AND revoked_at IS NULL",
                                        (_iso(_utc(now)), device_id, household_id))
            if cursor.rowcount != 1:
                raise LookupError("no such phone")

    # ---------- Safari to Home Screen ----------
    def create_phone_handoff(self, device_id: str, now: "datetime | None" = None) -> str:
        moment, token = _utc(now), secrets.token_urlsafe(24)
        with self._connection() as connection:
            connection.execute("DELETE FROM kid_phone_handoffs WHERE device_id = ?", (device_id,))
            connection.execute("INSERT INTO kid_phone_handoffs(token_hash, device_id, expires_at) VALUES (?, ?, ?)",
                               (_hash(token), device_id, _iso(moment + HANDOFF_TTL)))
        return token

    def exchange_phone_handoff(self, handoff: str, now: "datetime | None" = None) -> "str | None":
        """Burn a handoff and rotate the device's token: the new token is returned, the old one stops working."""
        moment = _utc(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT h.device_id, h.expires_at FROM kid_phone_handoffs h JOIN kid_phone_devices d ON d.id = h.device_id "
                    "WHERE h.token_hash = ? AND h.used = 0 AND d.revoked_at IS NULL", (_hash(str(handoff)),)).fetchone()
                if not row or _parse(row[1]) <= moment:
                    connection.commit()
                    return None
                token = secrets.token_urlsafe(32)
                connection.execute("UPDATE kid_phone_handoffs SET used = 1 WHERE token_hash = ?", (_hash(str(handoff)),))
                connection.execute("UPDATE kid_phone_devices SET token_hash = ?, last_seen_at = ? WHERE id = ?", (_hash(token), _iso(moment), row[0]))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return token

from __future__ import annotations

from contextlib import contextmanager
import threading
from datetime import date, datetime, timezone
import os
from pathlib import Path
import re
import sys
import secrets
from typing import Any, Iterator, Mapping, Sequence
from urllib.parse import urlsplit

try:
    from sqlcipher3 import dbapi2 as sqlite
except ImportError as error:
    raise RuntimeError(
        "Encrypted storage requires sqlcipher3-wheels. Install requirements.txt."
    ) from error


from .common import (  # noqa: E402
    LATEST_HOUSEHOLD_ORDER, SOURCE_CATEGORIES, WEEKDAY_ALIASES, WEEKDAY_NAMES, WEEKDAYS,
    _commute_mode, _member_id, _now, _optional_date, _required_text, _safe_url, _travel_minutes,
)
from .chore_series import ChoreSeries  # noqa: E402
from .documents import HouseholdDocuments  # noqa: E402
from .energy_connections import EnergyConnections  # noqa: E402
from .kid_bag import KidBag  # noqa: E402
from .kid_phone import KidPhone  # noqa: E402
from .kid_privacy import KidPrivacy  # noqa: E402
from .kid_tasks import KidTasks  # noqa: E402
from .kids import Kids  # noqa: E402
from .meter_readings import MeterReadings  # noqa: E402
from .reminders import Reminders  # noqa: E402
from .skips import Skips  # noqa: E402

MIGRATIONS = Path(__file__).parent / "migrations"
class EncryptedHouseholdStore(HouseholdDocuments, ChoreSeries, Reminders, Skips, EnergyConnections, MeterReadings, Kids, KidPhone, KidPrivacy, KidTasks, KidBag):
    """Encrypted SQLite persistence; access policy belongs to the application layer."""

    def __init__(self, path: str | Path | None = None, key_hex: str | None = None, plain: bool | None = None):
        self.plain = plain if plain is not None else os.environ.get("CHIT_STORAGE") == "plain"
        if self.plain and os.environ.get("CHIT_ENV") == "production":
            raise ValueError("unencrypted storage is not allowed when CHIT_ENV=production")
        default_path = "data/dev.db" if self.plain else "data/chit.db"
        self.path = Path(path or os.environ.get("CHIT_DB_PATH", default_path)).expanduser()
        self.key_hex = None if self.plain else (key_hex or os.environ.get("CHIT_DB_KEY_HEX"))
        if not self.plain and (not self.key_hex or not re.fullmatch(r"[0-9a-fA-F]{64}", self.key_hex)):
            raise ValueError("CHIT_DB_KEY_HEX must be a 64-character hex-encoded 32-byte key")
        if self.plain:
            print("WARNING: Chit is using an UNENCRYPTED development database at %s (ADR-0010)" % self.path, file=sys.stderr)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass
        self._initialize()

    # The hub serves requests on many threads. Opening and closing SQLite connections to one WAL file from many
    # threads at once can wedge the whole process inside SQLite's file locking (seen on macOS with the dashboard's
    # parallel requests), so database access is serialised. Network calls never happen inside this lock.
    _access = threading.RLock()

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        with self._access:
            with self._open() as connection:
                yield connection

    @contextmanager
    def _open(self) -> Iterator[Any]:
        connection = sqlite.connect(str(self.path), timeout=10, isolation_level=None)
        try:
            if not self.plain:
                connection.execute("PRAGMA key = \"x'%s'\"" % self.key_hex)
                cipher = connection.execute("PRAGMA cipher_version").fetchone()
                if not cipher or not cipher[0]:
                    raise RuntimeError("SQLite library does not provide SQLCipher encryption")
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA secure_delete = ON")
            connection.execute("PRAGMA busy_timeout = 10000")
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            applied = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
            for migration_path in sorted(MIGRATIONS.glob("*.sql")):
                if migration_path.name in applied:
                    continue
                connection.execute("BEGIN IMMEDIATE")
                try:
                    for statement in _statements(migration_path.read_text(encoding="utf-8")):
                        connection.execute(statement)
                    connection.execute(
                        "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                        (migration_path.name, _now()),
                    )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def create_household(
        self,
        name: str,
        owner_name: str,
        timezone_name: str = "Europe/Berlin",
        country_code: str | None = None,
        region: str | None = None,
        owner_birth_date: str | None = None,
    ) -> dict[str, str]:
        household_id = _member_id()
        owner_id = _member_id()
        now = _now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT INTO households(id, name, timezone, country_code, region, owner_member_id, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (household_id, _required_text(name, "household name"),
                     _required_text(timezone_name, "time zone"), country_code, region,
                     owner_id, now, now),
                )
                connection.execute(
                    "INSERT INTO household_members(id, household_id, role, name, birth_date, created_at, updated_at) "
                    "VALUES (?, ?, 'adult', ?, ?, ?, ?)",
                    (owner_id, household_id, _required_text(owner_name, "owner name"),
                     _optional_date(owner_birth_date), now, now),
                )
                connection.execute("INSERT INTO adult_settings(member_id) VALUES (?)", (owner_id,))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {"household_id": household_id, "owner_member_id": owner_id}

    @staticmethod
    def _resolve_member_ids(
        client_ids: Any,
        members: Mapping[str, Mapping[str, Any]],
        member_ids: Mapping[str, str],
        field_name: str,
    ) -> list[str]:
        if not isinstance(client_ids, list):
            raise ValueError("%s assignments must be a list" % field_name)
        resolved = []
        for client_id in client_ids:
            member = members.get(str(client_id))
            if member is None:
                raise ValueError("%s must refer to a household member" % field_name)
            if field_name in {"pickup adult", "drop-off adult"} and member.get("role") != "adult":
                raise ValueError("%s must refer to an adult" % field_name)
            resolved.append(member_ids[str(client_id)])
        return resolved

    def add_member(
        self,
        household_id: str,
        role: str,
        name: str,
        profile: Mapping[str, Any] | None = None,
    ) -> str:
        if role not in {"adult", "child", "helper"}:
            raise ValueError("role must be adult, child or helper")
        profile = dict(profile or {})
        member_id = _member_id()
        now = _now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT INTO household_members(id, household_id, role, name, birth_date, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (member_id, household_id, role, _required_text(name, "member name"),
                     _optional_date(profile.get("birth_date")), now, now),
                )
                if role == "adult":
                    self._insert_adult_settings(connection, member_id, profile)
                elif role == "child":
                    self._insert_child_settings(connection, member_id, profile)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return member_id

    def _insert_adult_settings(self, connection: Any, member_id: str, profile: Mapping[str, Any]) -> None:
        connection.execute(
            "INSERT INTO adult_settings(member_id, work_start, work_end, commute_minutes, "
            "evening_weekend_availability, focus_start, focus_end, babysitting_max_evenings, babysitting_notice) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (member_id, profile.get("work_start"), profile.get("work_end"),
             profile.get("commute_minutes"), profile.get("evening_weekend_availability", "not_set"),
             profile.get("focus_start"), profile.get("focus_end"),
             profile.get("babysitting_max_evenings"), profile.get("babysitting_notice", "not_set")),
        )
        self._insert_weekdays(connection, "adult_work_days", "member_id", member_id,
                               profile.get("work_days", {}), "location")

    def _insert_child_settings(self, connection: Any, member_id: str, profile: Mapping[str, Any]) -> None:
        connection.execute(
            "INSERT INTO child_settings(member_id, school_or_care_name, school_type_or_year, "
            "after_school_care, pickup_time, supervision_policy, travel_minutes, dropoff_time, commute_mode) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (member_id, profile.get("school_or_care_name"), profile.get("school_type_or_year"),
             profile.get("after_school_care", "not_set"), profile.get("pickup_time"),
             profile.get("supervision_policy", "not_set"), profile.get("travel_minutes"),
             profile.get("dropoff_time"), _commute_mode(profile.get("commute_mode"))),
        )
        self._insert_weekdays(connection, "child_care_days", "member_id", member_id,
                               profile.get("care_days", {}), None)
        household_id = connection.execute(
            "SELECT household_id FROM household_members WHERE id = ?", (member_id,)
        ).fetchone()[0]
        for adult_id in profile.get("pickup_adult_ids", []):
            connection.execute(
                "INSERT INTO child_pickup_adults(child_id, adult_id, household_id) VALUES (?, ?, ?)",
                (member_id, adult_id, household_id),
            )
        for adult_id in profile.get("dropoff_adult_ids", []):
            connection.execute(
                "INSERT INTO child_dropoff_adults(child_id, adult_id, household_id) VALUES (?, ?, ?)",
                (member_id, adult_id, household_id),
            )
        for activity in profile.get("activities", []):
            activity_id = _member_id()
            mode = _commute_mode(activity.get("commute_mode"))
            escort = activity.get("escort") or "independent"
            if escort not in ("independent", "parent"):
                raise ValueError("activity escort must be independent or parent")
            escort_adult = activity.get("escort_adult_id") if escort == "parent" else None
            if escort_adult is not None and not connection.execute(
                    "SELECT 1 FROM household_members WHERE id = ? AND household_id = ? AND role = 'adult'",
                    (escort_adult, household_id)).fetchone():
                raise ValueError("activity escort must be an adult in the household")
            connection.execute(
                "INSERT INTO child_activities(id, member_id, name, location, start_time, end_time, "
                "commute_mode, travel_minutes, escort, escort_adult_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (activity_id, member_id, _required_text(activity["name"], "activity name"),
                 activity.get("location"), activity.get("start_time"), activity.get("end_time"),
                 mode, _travel_minutes(activity.get("travel_minutes")), escort, escort_adult),
            )
            self._insert_weekdays(connection, "child_activity_days", "activity_id", activity_id,
                                   {day: True for day in activity.get("days", [])}, None)

    @staticmethod
    def _insert_weekdays(
        connection: Any,
        table: str,
        id_column: str,
        record_id: str,
        values: Mapping[str, Any],
        value_column: str | None,
    ) -> None:
        entries = values.items() if isinstance(values, Mapping) else ((day, True) for day in values)
        for day, value in entries:
            normalized_day = str(day).lower()
            weekday = WEEKDAYS.get(WEEKDAY_ALIASES.get(normalized_day, normalized_day))
            if weekday is None:
                raise ValueError("unknown weekday: %s" % day)
            if table == "adult_work_days":
                if value not in {"office", "home", "off"}:
                    raise ValueError("work day location must be office, home or off")
                connection.execute(
                    "INSERT INTO adult_work_days(member_id, weekday, location) VALUES (?, ?, ?)",
                    (record_id, weekday, value),
                )
            else:
                connection.execute(
                    "INSERT INTO %s(%s, weekday) VALUES (?, ?)" % (table, id_column),
                    (record_id, weekday),
                )

    def set_household_owner(self, household_id: str, member_id: str) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    "UPDATE households SET owner_member_id = ?, updated_at = ? WHERE id = ?",
                    (member_id, _now(), household_id),
                )
                if cursor.rowcount != 1:
                    raise ValueError("household does not exist")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def add_calendar_source(
        self,
        household_id: str,
        name: str,
        category: str,
        subscription_url: str,
        member_ids: Sequence[str] = (),
    ) -> str:
        normalized_category = SOURCE_CATEGORIES.get(category, category)
        if normalized_category not in set(SOURCE_CATEGORIES.values()):
            raise ValueError("unsupported calendar category")
        source_id = _member_id()
        now = _now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT INTO calendar_sources(id, household_id, name, category, subscription_url, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (source_id, household_id, _required_text(name, "calendar name"),
                     normalized_category, _safe_url(subscription_url), now, now),
                )
                for member_id in member_ids:
                    connection.execute(
                        "INSERT INTO calendar_source_members(source_id, household_id, member_id) VALUES (?, ?, ?)",
                        (source_id, household_id, member_id),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return source_id

    def add_chore_rule(
        self,
        household_id: str,
        source_id: str,
        title_template: str,
        assignee_ids: Sequence[str] = (),
    ) -> str:
        rule_id = _member_id()
        now = _now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT INTO chore_generation_rules(id, household_id, source_id, title_template, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (rule_id, household_id, source_id, _required_text(title_template, "chore title"), now, now),
                )
                for member_id in assignee_ids:
                    connection.execute(
                        "INSERT INTO chore_rule_assignees(rule_id, source_id, member_id, household_id) VALUES (?, ?, ?, ?)",
                        (rule_id, source_id, member_id, household_id),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return rule_id

    def upsert_generated_chore(
        self,
        household_id: str,
        source_id: str,
        rule_id: str,
        source_occurrence_ref: str,
        title: str,
        due_at: str | None,
        source_observed_at: str | None = None,
    ) -> str:
        chore_id = _member_id()
        now = _now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                existing = connection.execute(
                    "SELECT id FROM chores WHERE source_id = ? AND source_occurrence_ref = ? AND generation_rule_id = ?",
                    (source_id, source_occurrence_ref, rule_id),
                ).fetchone()
                connection.execute(
                    "INSERT INTO chores(id, household_id, title, due_at, data_state, availability_status, "
                    "source_observed_at, ingested_at, source_id, source_occurrence_ref, generation_rule_id, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, 'measured', 'available', ?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(source_id, source_occurrence_ref, generation_rule_id) DO UPDATE SET "
                    "title = CASE WHEN chores.state = 'open' AND chores.manually_modified = 0 THEN excluded.title ELSE chores.title END, "
                    "due_at = CASE WHEN chores.state = 'open' AND chores.manually_modified = 0 THEN excluded.due_at ELSE chores.due_at END, "
                    "source_observed_at = COALESCE(excluded.source_observed_at, chores.source_observed_at), "
                    "ingested_at = excluded.ingested_at, "
                    "updated_at = excluded.updated_at",
                    (chore_id, household_id, _required_text(title, "chore title"), due_at,
                     source_observed_at, now, source_id,
                     _required_text(source_occurrence_ref, "source occurrence reference"), rule_id, now, now),
                )
                row = connection.execute(
                    "SELECT id FROM chores WHERE source_id = ? AND source_occurrence_ref = ? AND generation_rule_id = ?",
                    (source_id, source_occurrence_ref, rule_id),
                ).fetchone()
                if existing is None:
                    connection.execute(
                        "INSERT INTO chore_assignees(chore_id, member_id, household_id) "
                        "SELECT ?, member_id, household_id FROM chore_rule_assignees WHERE rule_id = ?",
                        (row[0], rule_id),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return row[0]

    def update_chore(
        self,
        household_id: str,
        chore_id: str,
        title: str,
        due_at: str | None,
        state: str = "open",
        manually_modified: bool = True,
    ) -> None:
        if state not in {"open", "completed", "cancelled"}:
            raise ValueError("state must be open, completed or cancelled")
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE chores SET title = ?, due_at = ?, state = ?, manually_modified = ?, "
                "data_state = CASE WHEN ? = 1 THEN 'manual' ELSE data_state END, updated_at = ? "
                "WHERE id = ? AND household_id = ?",
                (_required_text(title, "chore title"), due_at, state, int(manually_modified),
                 int(manually_modified), _now(), chore_id, household_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("chore does not exist in this household")

    def list_household(self, household_id: str) -> dict[str, Any]:
        with self._connection() as connection:
            household = connection.execute(
                "SELECT id, name, timezone, country_code, region, owner_member_id FROM households WHERE id = ?",
                (household_id,),
            ).fetchone()
            if not household:
                raise ValueError("household does not exist")
            members: list[dict[str, Any]] = []
            for row in connection.execute(
                "SELECT id, role, name, birth_date FROM household_members WHERE household_id = ? ORDER BY role, name",
                (household_id,),
            ):
                member = {"id": row[0], "role": row[1], "name": row[2], "birth_date": row[3]}
                if member["role"] == "adult":
                    settings = connection.execute(
                        "SELECT work_start, work_end, commute_minutes, evening_weekend_availability, focus_start, focus_end, babysitting_max_evenings, babysitting_notice FROM adult_settings WHERE member_id = ?",
                        (member["id"],),
                    ).fetchone()
                    member["settings"] = dict(zip(
                        ("work_start", "work_end", "commute_minutes", "evening_weekend_availability", "focus_start", "focus_end", "babysitting_max_evenings", "babysitting_notice"), settings
                    ))
                    member["work_days"] = {WEEKDAY_NAMES[day]: location for day, location in connection.execute(
                        "SELECT weekday, location FROM adult_work_days WHERE member_id = ? ORDER BY weekday", (member["id"],)
                    )}
                elif member["role"] == "child":
                    settings = connection.execute(
                        "SELECT school_or_care_name, school_type_or_year, after_school_care, pickup_time, supervision_policy, travel_minutes FROM child_settings WHERE member_id = ?",
                        (member["id"],),
                    ).fetchone()
                    member["settings"] = dict(zip(
                        ("school_or_care_name", "school_type_or_year", "after_school_care", "pickup_time", "supervision_policy", "travel_minutes"), settings
                    ))
                    member["care_days"] = [WEEKDAY_NAMES[day] for (day,) in connection.execute(
                        "SELECT weekday FROM child_care_days WHERE member_id = ? ORDER BY weekday", (member["id"],)
                    )]
                    member["pickup_adult_ids"] = [adult_id for (adult_id,) in connection.execute(
                        "SELECT adult_id FROM child_pickup_adults WHERE child_id = ? ORDER BY adult_id", (member["id"],)
                    )]
                    member["dropoff_adult_ids"] = [adult_id for (adult_id,) in connection.execute(
                        "SELECT adult_id FROM child_dropoff_adults WHERE child_id = ? ORDER BY adult_id", (member["id"],)
                    )]
                    member["activities"] = self._list_child_activities(connection, member["id"])
                members.append(member)
            sources = []
            for row in connection.execute(
                "SELECT id, name, category, access_mode, connection_state, last_checked_at FROM calendar_sources WHERE household_id = ? ORDER BY name",
                (household_id,),
            ):
                source = {"id": row[0], "name": row[1], "category": row[2], "access_mode": row[3],
                          "connection_state": row[4], "last_checked_at": row[5]}
                source["member_ids"] = [member_id for (member_id,) in connection.execute(
                    "SELECT member_id FROM calendar_source_members WHERE source_id = ? ORDER BY member_id", (source["id"],)
                )]
                sources.append(source)
            chores = []
            for row in connection.execute(
                "SELECT id, title, due_at, state, data_state, availability_status, availability_reason, "
                "source_id, source_occurrence_ref, generation_rule_id, source_observed_at, ingested_at "
                "FROM chores WHERE household_id = ? ORDER BY due_at, created_at",
                (household_id,),
            ):
                chore = dict(zip(
                    ("id", "title", "due_at", "state", "data_state", "availability_status",
                     "availability_reason", "source_id", "source_occurrence_ref", "generation_rule_id",
                     "source_observed_at", "ingested_at"), row
                ))
                chore["assignee_ids"] = [member_id for (member_id,) in connection.execute(
                    "SELECT member_id FROM chore_assignees WHERE chore_id = ? ORDER BY member_id", (chore["id"],)
                )]
                chores.append(chore)
            return {
                "household": dict(zip(("id", "name", "timezone", "country_code", "region", "owner_member_id"), household)),
                "members": members,
                "calendar_sources": sources,
                "chores": chores,
            }

    def latest_household_calendar_sources(self) -> dict[str, Any] | None:
        with self._connection() as connection:
            household = connection.execute(
                "SELECT id, name, timezone FROM households " + LATEST_HOUSEHOLD_ORDER + " LIMIT 1"
            ).fetchone()
            if not household:
                return None
            sources = []
            for row in connection.execute(
                "SELECT id, name, category, subscription_url, connection_state, last_checked_at "
                "FROM calendar_sources WHERE household_id = ? ORDER BY name",
                (household[0],),
            ):
                sources.append({
                    "id": row[0], "name": row[1], "category": row[2], "subscription_url": row[3],
                    "connection_state": row[4], "last_checked_at": row[5],
                    "members": [name for (name,) in connection.execute(
                        "SELECT hm.name FROM calendar_source_members csm "
                        "JOIN household_members hm ON hm.id = csm.member_id "
                        "WHERE csm.source_id = ? ORDER BY hm.name", (row[0],)
                    )],
                    "member_ids": [member for (member,) in connection.execute(
                        "SELECT member_id FROM calendar_source_members WHERE source_id = ? ORDER BY member_id", (row[0],))],
                })
            return {"id": household[0], "name": household[1], "timezone": household[2], "sources": sources}
    def latest_household_summary(self) -> dict[str, Any] | None:
        with self._connection() as connection:
            household = connection.execute(
                "SELECT id, name FROM households " + LATEST_HOUSEHOLD_ORDER + " LIMIT 1"
            ).fetchone()
            if not household:
                return None
            members = []
            for row in connection.execute(
                "SELECT id, name, role FROM household_members WHERE household_id = ? ORDER BY role, name",
                (household[0],),
            ):
                members.append({"id": row[0], "name": row[1], "role": row[2]})
            return {"id": household[0], "name": household[1], "members": members}
    def record_calendar_check(self, source_id: str, state: str) -> None:
        if state not in {"available", "unavailable", "stale", "unknown"}:
            raise ValueError("invalid calendar connection state")
        now = _now()
        with self._connection() as connection:
            connection.execute(
                "UPDATE calendar_sources SET connection_state = ?, last_checked_at = ?, updated_at = ? WHERE id = ?",
                (state, now, now, source_id),
            )

    @staticmethod
    def _list_child_activities(connection: Any, member_id: str) -> list[dict[str, Any]]:
        activities = []
        for row in connection.execute(
            "SELECT id, name, location, start_time, end_time, commute_mode, travel_minutes, escort, escort_adult_id "
            "FROM child_activities WHERE member_id = ? ORDER BY name",
            (member_id,),
        ):
            activity = {"id": row[0], "name": row[1], "location": row[2], "start_time": row[3], "end_time": row[4],
                        "commute_mode": row[5], "travel_minutes": row[6], "escort": row[7],
                        "escort_adult_client_id": row[8]}
            activity["days"] = [WEEKDAY_NAMES[day] for (day,) in connection.execute(
                "SELECT weekday FROM child_activity_days WHERE activity_id = ? ORDER BY weekday", (activity["id"],)
            )]
            activities.append(activity)
        return activities



def _statements(script: str) -> Iterator[str]:
    statement = ""
    for line in script.splitlines():
        statement += line + "\n"
        if sqlite.complete_statement(statement):
            if statement.strip():
                yield statement
            statement = ""
    if statement.strip():
        raise ValueError("incomplete SQL migration")

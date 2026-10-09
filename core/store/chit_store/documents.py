"""Household documents: create, edit and read a whole household as one JSON-shaped document.

The document is the setup payload (see docs/decisions/0010-*.md). The same shape is used by the
HTTP API, seed fixtures and exports. On edit, `client_id` values that match an existing member or
calendar id keep that record (so generated chores, assignments and ids survive); anything else is new.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .common import (
    LATEST_HOUSEHOLD_ORDER, PERSON_COLORS, SOURCE_CATEGORIES, WEEKDAY_NAMES, _member_id, _now, _optional_date,
    _required_text, _safe_url, default_avatar, optional_coordinate, valid_avatar, valid_color,
)

_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_MODULE_ID = re.compile(r"^[a-z][a-z0-9-]{0,40}$")


def _module_list(value: Any, field: str) -> "list[str] | None":
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) and _MODULE_ID.match(item) for item in value):
        raise ValueError("%s must be a list of module ids" % field)
    return sorted(set(value))


HOUSEHOLD_TYPES = ("single", "couple", "family", "shared")


def default_household_type(members: "list[Mapping[str, Any]]") -> str:
    """For documents that do not say: what the members already are."""
    adults = sum(1 for m in members if m.get("role") == "adult")
    if any(m.get("role") == "child" for m in members):
        return "family"
    return "single" if adults == 1 else "couple" if adults == 2 else "shared"


def check_household_shape(kind: str, members: "list[Mapping[str, Any]]") -> None:
    """Who each household type may contain. Only a family has children."""
    adults = sum(1 for m in members if m.get("role") == "adult")
    children = len(members) - adults
    if kind == "single" and (adults != 1 or children):
        raise ValueError("a single household has exactly one adult and no children")
    if kind == "couple" and (adults != 2 or children):
        raise ValueError("a couple household has exactly two adults and no children")
    if kind == "shared" and (adults < 2 or children):
        raise ValueError("a shared flat has two or more adults and no children")
    if kind == "family" and adults < 1:
        raise ValueError("a family needs at least one adult")


class HouseholdDocuments:
    # ---------- create ----------
    def save_household_setup(self, setup: Mapping[str, Any], preserve_ids: bool = False) -> dict[str, Any]:
        """Create a household. With preserve_ids (seed fixtures) client ids and household.id become real ids."""
        parsed = self._parse_setup(setup)
        household = parsed["household"]
        if preserve_ids:
            household_id = str(household.get("id") or _member_id())
            if not _ID.match(household_id):
                raise ValueError("household id may only contain letters, digits, - and _")
            for client_id in list(parsed["members"]) + [c["client_id"] for c in parsed["calendars"]]:
                if not _ID.match(client_id):
                    raise ValueError("ids may only contain letters, digits, - and _")
            member_ids = {client_id: client_id for client_id in parsed["members"]}
            source_ids = {c["client_id"]: c["client_id"] for c in parsed["calendars"]}
        else:
            household_id = _member_id()
            member_ids = {client_id: _member_id() for client_id in parsed["members"]}
            source_ids = {c["client_id"]: _member_id() for c in parsed["calendars"]}
        now = _now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if connection.execute("SELECT 1 FROM households WHERE id = ?", (household_id,)).fetchone():
                    raise ValueError("household already exists")
                connection.execute(
                    "INSERT INTO households(id, name, timezone, country_code, region, owner_member_id, created_at, updated_at, household_type) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (household_id, household["name"], household["timezone"], household["country_code"],
                     household["region"], member_ids[parsed["owner_client_id"]], now, now, household["type"]),
                )
                self._sync_household(connection, household_id, parsed, member_ids, source_ids, now)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {
            "household_id": household_id,
            "owner_member_id": member_ids[parsed["owner_client_id"]],
            "member_ids": member_ids,
            "calendar_source_ids": source_ids,
        }

    # ---------- edit ----------
    def update_household(self, household_id: str, setup: Mapping[str, Any]) -> dict[str, Any]:
        parsed = self._parse_setup(setup)
        now = _now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if not connection.execute("SELECT 1 FROM households WHERE id = ?", (household_id,)).fetchone():
                    raise LookupError("household does not exist")
                existing_members = {row[0] for row in connection.execute(
                    "SELECT id FROM household_members WHERE household_id = ?", (household_id,))}
                existing_sources = {row[0] for row in connection.execute(
                    "SELECT id FROM calendar_sources WHERE household_id = ?", (household_id,))}
                member_ids = {cid: (cid if cid in existing_members else _member_id()) for cid in parsed["members"]}
                source_ids = {c["client_id"]: (c["client_id"] if c["client_id"] in existing_sources else _member_id())
                              for c in parsed["calendars"]}
                self._sync_household(connection, household_id, parsed, member_ids, source_ids, now)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return {
            "household_id": household_id,
            "owner_member_id": member_ids[parsed["owner_client_id"]],
            "member_ids": member_ids,
            "calendar_source_ids": source_ids,
        }

    # ---------- shared validation ----------
    def _parse_setup(self, setup: Mapping[str, Any]) -> dict[str, Any]:
        household = setup.get("household")
        members = setup.get("members")
        calendars = setup.get("calendars", [])
        if not isinstance(household, Mapping) or not isinstance(members, list) or not isinstance(calendars, list):
            raise ValueError("household, members and calendars are required")
        if not members:
            raise ValueError("at least one adult member is required")
        member_by_client_id: dict[str, Mapping[str, Any]] = {}
        for member in members:
            if not isinstance(member, Mapping):
                raise ValueError("each member must be an object")
            client_id = _required_text(str(member.get("client_id", "")), "member client id")
            if client_id in member_by_client_id:
                raise ValueError("member client ids must be unique")
            if member.get("role") not in {"adult", "child"}:
                raise ValueError("member role must be adult or child")
            _required_text(str(member.get("name", "")), "member name")
            valid_avatar(member.get("avatar"), member["role"])
            valid_color(member.get("color"))
            member_by_client_id[client_id] = member
        member_list = list(member_by_client_id.values())
        household_type = household.get("type") or default_household_type(member_list)
        if household_type not in HOUSEHOLD_TYPES:
            raise ValueError("household type must be one of %s" % ", ".join(HOUSEHOLD_TYPES))
        check_household_shape(household_type, member_list)
        owner_client_id = _required_text(str(setup.get("owner_client_id", "")), "household owner")
        owner = member_by_client_id.get(owner_client_id)
        if owner is None or owner.get("role") != "adult":
            raise ValueError("household owner must be an adult in this setup")

        modules = _module_list(setup.get("modules"), "modules")
        member_modules = {}
        for client_id, member in member_by_client_id.items():
            listed = _module_list(member.get("modules"), "member modules")
            if listed is not None and modules is not None and not set(listed) <= set(modules):
                raise ValueError("a member cannot use a module the household has not enabled")
            member_modules[client_id] = listed

        seen: set[str] = set()
        parsed_calendars = []
        for calendar in calendars:
            if not isinstance(calendar, Mapping):
                raise ValueError("each calendar must be an object")
            client_id = _required_text(str(calendar.get("client_id", "")), "calendar client id")
            if client_id in seen:
                raise ValueError("calendar client ids must be unique")
            seen.add(client_id)
            category = SOURCE_CATEGORIES.get(str(calendar.get("category", "")), calendar.get("category"))
            if category not in set(SOURCE_CATEGORIES.values()):
                raise ValueError("unsupported calendar category")
            parsed_calendars.append({
                "client_id": client_id,
                "name": _required_text(str(calendar.get("name", "")), "calendar name"),
                "category": category,
                "subscription_url": _safe_url(str(calendar.get("subscription_url", ""))),
                "member_client_ids": calendar.get("member_client_ids", []),
                "chore_enabled": bool(calendar.get("chore_enabled")),
                "chore_title": calendar.get("chore_title"),
                "chore_assignee_client_ids": calendar.get("chore_assignee_client_ids", []),
            })
        return {
            "household": {
                "id": household.get("id"),
                "name": _required_text(str(household.get("name", "")), "household name"),
                "timezone": _required_text(str(household.get("timezone", "")), "time zone"),
                "country_code": household.get("country_code") or None,
                "region": household.get("region") or None,
                "latitude": optional_coordinate(household.get("latitude"), -90, 90, "latitude"),
                "longitude": optional_coordinate(household.get("longitude"), -180, 180, "longitude"),
                "type": household_type,
            },
            "owner_client_id": owner_client_id,
            "members": member_by_client_id,
            "member_modules": member_modules,
            "calendars": parsed_calendars,
            "modules": modules,
        }

    # ---------- shared writer (create + edit) ----------
    def _sync_household(self, connection: Any, household_id: str, parsed: dict[str, Any],
                        member_ids: Mapping[str, str], source_ids: Mapping[str, str], now: str) -> None:
        members = parsed["members"]
        existing_roles = dict(connection.execute(
            "SELECT id, role FROM household_members WHERE household_id = ?", (household_id,)).fetchall())

        # 1. member rows (insert or update); settings come after every member exists
        counts = {"adult": 0, "child": 0}
        for position, (client_id, member) in enumerate(members.items()):
            index_in_role = counts[member["role"]]
            counts[member["role"]] += 1
            member = {**member,
                      "avatar": valid_avatar(member.get("avatar"), member["role"]) or default_avatar(member["role"], index_in_role),
                      "color": valid_color(member.get("color")) or PERSON_COLORS[position % len(PERSON_COLORS)]}
            members[client_id] = member
            member_id = member_ids[client_id]
            profile = member.get("profile") or {}
            if not isinstance(profile, Mapping):
                raise ValueError("member profile must be an object")
            birth = _optional_date(profile.get("birth_date"))
            name = _required_text(str(member.get("name", "")), "member name")
            if member_id in existing_roles:
                if existing_roles[member_id] != member["role"]:
                    raise ValueError("a member's role cannot be changed; remove and add the member instead")
                connection.execute(
                    "UPDATE household_members SET name = ?, birth_date = ?, avatar = ?, color = ?, updated_at = ? WHERE id = ?",
                    (name, birth, member["avatar"], member["color"], now, member_id))
            else:
                connection.execute(
                    "INSERT INTO household_members(id, household_id, role, name, birth_date, avatar, color, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (member_id, household_id, member["role"], name, birth, member["avatar"], member["color"], now, now))

        # 2. household row (owner must already exist as an adult), then drop removed members
        household = parsed["household"]
        connection.execute(
            "UPDATE households SET name = ?, timezone = ?, country_code = ?, region = ?, latitude = ?, longitude = ?, "
            "owner_member_id = ?, modules_configured = ?, updated_at = ?, household_type = ? WHERE id = ?",
            (household["name"], household["timezone"], household["country_code"], household["region"],
             household["latitude"], household["longitude"],
             member_ids[parsed["owner_client_id"]], int(parsed["modules"] is not None), now, household["type"], household_id))
        for removed in set(existing_roles) - set(member_ids.values()):
            connection.execute("DELETE FROM household_members WHERE id = ?", (removed,))

        # 3. member settings (replace)
        for client_id, member in members.items():
            member_id = member_ids[client_id]
            profile = member.get("profile") or {}
            if member["role"] == "adult":
                connection.execute("DELETE FROM adult_settings WHERE member_id = ?", (member_id,))
                self._insert_adult_settings(connection, member_id, profile)
            else:
                for table in ("child_pickup_adults", "child_dropoff_adults"):
                    connection.execute("DELETE FROM %s WHERE child_id = ?" % table, (member_id,))
                connection.execute("DELETE FROM child_settings WHERE member_id = ?", (member_id,))
                child_profile = dict(profile)
                child_profile["pickup_adult_ids"] = self._resolve_member_ids(
                    profile.get("pickup_adult_client_ids", []), members, member_ids, "pickup adult")
                child_profile["dropoff_adult_ids"] = self._resolve_member_ids(
                    profile.get("dropoff_adult_client_ids", []), members, member_ids, "drop-off adult")
                child_profile["activities"] = []
                for activity in profile.get("activities") or []:
                    escort = activity.get("escort_adult_client_id")
                    resolved = self._resolve_member_ids([escort] if escort else [], members, member_ids, "pickup adult")
                    child_profile["activities"].append({**activity, "escort_adult_id": resolved[0] if resolved else None})
                self._insert_child_settings(connection, member_id, child_profile)

        # 4. calendars: upsert so generated chores survive; removed sources cascade
        existing_sources = {row[0] for row in connection.execute(
            "SELECT id FROM calendar_sources WHERE household_id = ?", (household_id,))}
        for calendar in parsed["calendars"]:
            source_id = source_ids[calendar["client_id"]]
            if source_id in existing_sources:
                connection.execute(
                    "UPDATE calendar_sources SET name = ?, category = ?, "
                    "connection_state = CASE WHEN subscription_url != ? THEN 'not_checked' ELSE connection_state END, "
                    "subscription_url = ?, updated_at = ? WHERE id = ?",
                    (calendar["name"], calendar["category"], calendar["subscription_url"],
                     calendar["subscription_url"], now, source_id))
            else:
                connection.execute(
                    "INSERT INTO calendar_sources(id, household_id, name, category, subscription_url, "
                    "access_mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'read_only', ?, ?)",
                    (source_id, household_id, calendar["name"], calendar["category"],
                     calendar["subscription_url"], now, now))
            connection.execute("DELETE FROM calendar_source_members WHERE source_id = ?", (source_id,))
            for member_id in self._resolve_member_ids(calendar["member_client_ids"], members, member_ids, "calendar member"):
                connection.execute(
                    "INSERT INTO calendar_source_members(source_id, household_id, member_id) VALUES (?, ?, ?)",
                    (source_id, household_id, member_id))
            self._sync_chore_rule(connection, household_id, source_id, calendar, members, member_ids, now)
        for removed in existing_sources - set(source_ids.values()):
            connection.execute("DELETE FROM calendar_sources WHERE id = ?", (removed,))

        # 5. stored enablement (layers 3 and 4)
        connection.execute("DELETE FROM household_modules WHERE household_id = ?", (household_id,))
        for module_id in parsed["modules"] or []:
            connection.execute("INSERT INTO household_modules(household_id, module_id) VALUES (?, ?)",
                               (household_id, module_id))
        for client_id, listed in parsed["member_modules"].items():
            member_id = member_ids[client_id]
            connection.execute("DELETE FROM member_modules WHERE member_id = ?", (member_id,))
            connection.execute("UPDATE household_members SET modules_restricted = ? WHERE id = ?",
                               (int(listed is not None), member_id))
            for module_id in listed or []:
                connection.execute("INSERT INTO member_modules(member_id, module_id) VALUES (?, ?)",
                                   (member_id, module_id))

    def _sync_chore_rule(self, connection: Any, household_id: str, source_id: str, calendar: Mapping[str, Any],
                         members: Mapping[str, Any], member_ids: Mapping[str, str], now: str) -> None:
        rule = connection.execute(
            "SELECT id FROM chore_generation_rules WHERE source_id = ? ORDER BY created_at, rowid LIMIT 1",
            (source_id,)).fetchone()
        if not calendar["chore_enabled"]:
            if rule:  # keep the rule and its chores; just stop generating
                connection.execute("UPDATE chore_generation_rules SET enabled = 0, updated_at = ? WHERE id = ?",
                                   (now, rule[0]))
            return
        assignee_ids = self._resolve_member_ids(
            calendar["chore_assignee_client_ids"], members, member_ids, "chore assignee")
        title = _required_text(str(calendar["chore_title"] or "Prepare for " + calendar["name"]), "chore title")
        if rule:
            rule_id = rule[0]
            connection.execute(
                "UPDATE chore_generation_rules SET title_template = ?, enabled = 1, updated_at = ? WHERE id = ?",
                (title, now, rule_id))
            connection.execute("DELETE FROM chore_rule_assignees WHERE rule_id = ?", (rule_id,))
        else:
            rule_id = _member_id()
            connection.execute(
                "INSERT INTO chore_generation_rules(id, household_id, source_id, title_template, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)", (rule_id, household_id, source_id, title, now, now))
        for member_id in assignee_ids:
            connection.execute(
                "INSERT INTO chore_rule_assignees(rule_id, source_id, member_id, household_id) VALUES (?, ?, ?, ?)",
                (rule_id, source_id, member_id, household_id))

    # ---------- read ----------
    def latest_household_id(self) -> "str | None":
        with self._connection() as connection:
            row = connection.execute("SELECT id FROM households " + LATEST_HOUSEHOLD_ORDER + " LIMIT 1").fetchone()
            return row[0] if row else None

    def get_household_document(self, household_id: str) -> dict[str, Any]:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT id, name, timezone, country_code, region, owner_member_id, modules_configured, "
                "created_at, updated_at, latitude, longitude, household_type FROM households WHERE id = ?", (household_id,)).fetchone()
            if not row:
                raise LookupError("household does not exist")
            modules = [m for (m,) in connection.execute(
                "SELECT module_id FROM household_modules WHERE household_id = ? ORDER BY module_id", (household_id,))]
            members = []
            for member in connection.execute(
                "SELECT id, role, name, birth_date, modules_restricted, avatar, color FROM household_members "
                "WHERE household_id = ? ORDER BY CASE role WHEN 'adult' THEN 0 ELSE 1 END, created_at, rowid",
                (household_id,)).fetchall():
                member_id, role = member[0], member[1]
                profile: dict[str, Any] = {"birth_date": member[3]}
                if role == "adult":
                    settings = connection.execute(
                        "SELECT work_start, work_end, commute_minutes, evening_weekend_availability, focus_start, "
                        "focus_end, babysitting_max_evenings, babysitting_notice FROM adult_settings WHERE member_id = ?",
                        (member_id,)).fetchone()
                    keys = ("work_start", "work_end", "commute_minutes", "evening_weekend_availability",
                            "focus_start", "focus_end", "babysitting_max_evenings", "babysitting_notice")
                    profile.update(dict(zip(keys, settings)) if settings else {})
                    profile["work_days"] = {WEEKDAY_NAMES[d]: loc for d, loc in connection.execute(
                        "SELECT weekday, location FROM adult_work_days WHERE member_id = ? ORDER BY weekday", (member_id,))}
                elif role == "child":
                    settings = connection.execute(
                        "SELECT school_or_care_name, school_type_or_year, after_school_care, pickup_time, "
                        "supervision_policy, travel_minutes, dropoff_time, commute_mode FROM child_settings WHERE member_id = ?", (member_id,)).fetchone()
                    keys = ("school_or_care_name", "school_type_or_year", "after_school_care", "pickup_time",
                            "supervision_policy", "travel_minutes", "dropoff_time", "commute_mode")
                    profile.update(dict(zip(keys, settings)) if settings else {})
                    profile["care_days"] = [WEEKDAY_NAMES[d] for (d,) in connection.execute(
                        "SELECT weekday FROM child_care_days WHERE member_id = ? ORDER BY weekday", (member_id,))]
                    profile["pickup_adult_client_ids"] = [a for (a,) in connection.execute(
                        "SELECT adult_id FROM child_pickup_adults WHERE child_id = ? ORDER BY rowid", (member_id,))]
                    profile["dropoff_adult_client_ids"] = [a for (a,) in connection.execute(
                        "SELECT adult_id FROM child_dropoff_adults WHERE child_id = ? ORDER BY rowid", (member_id,))]
                    profile["activities"] = [
                        {k: v for k, v in activity.items() if k != "id"}
                        for activity in self._list_child_activities(connection, member_id)]
                member_modules = [m for (m,) in connection.execute(
                    "SELECT module_id FROM member_modules WHERE member_id = ? ORDER BY module_id", (member_id,))]
                members.append({
                    "client_id": member_id, "role": role, "name": member[2], "profile": profile,
                    "avatar": member[5], "color": member[6],
                    "modules": member_modules if member[4] else None,
                })
            calendars = []
            for source in connection.execute(
                "SELECT id, name, category, subscription_url, connection_state, last_checked_at FROM calendar_sources "
                "WHERE household_id = ? ORDER BY created_at, rowid", (household_id,)).fetchall():
                rule = connection.execute(
                    "SELECT id, title_template, enabled FROM chore_generation_rules WHERE source_id = ? "
                    "ORDER BY created_at, rowid LIMIT 1", (source[0],)).fetchone()
                calendars.append({
                    "client_id": source[0], "name": source[1], "category": source[2],
                    "subscription_url": source[3], "connection_state": source[4], "last_checked_at": source[5],
                    "member_client_ids": [m for (m,) in connection.execute(
                        "SELECT member_id FROM calendar_source_members WHERE source_id = ? ORDER BY rowid", (source[0],))],
                    "chore_enabled": bool(rule and rule[2]),
                    "chore_title": rule[1] if rule else None,
                    "chore_assignee_client_ids": [m for (m,) in connection.execute(
                        "SELECT member_id FROM chore_rule_assignees WHERE rule_id = ? ORDER BY rowid", (rule[0],))] if rule else [],
                })
            return {
                "id": row[0],
                "created_at": row[7],
                "updated_at": row[8],
                "household": {"name": row[1], "timezone": row[2], "country_code": row[3], "region": row[4],
                              "latitude": row[9], "longitude": row[10], "type": row[11]},
                "owner_client_id": row[5],
                "modules": modules if row[6] else None,
                "members": members,
                "calendars": calendars,
            }

    def household_enablement(self, household_id: str) -> dict[str, Any]:
        """Stored layers 3-4: which modules the household enabled and which members are narrowed."""
        with self._connection() as connection:
            configured = connection.execute(
                "SELECT modules_configured FROM households WHERE id = ?", (household_id,)).fetchone()
            if not configured:
                raise LookupError("household does not exist")
            modules = {m for (m,) in connection.execute(
                "SELECT module_id FROM household_modules WHERE household_id = ?", (household_id,))}
            members = {}
            for member_id, role, restricted in connection.execute(
                "SELECT id, role, modules_restricted FROM household_members WHERE household_id = ?", (household_id,)):
                listed = {m for (m,) in connection.execute(
                    "SELECT module_id FROM member_modules WHERE member_id = ?", (member_id,))}
                members[member_id] = {"role": role, "modules": listed if restricted else None}
            return {"household_id": household_id, "modules": modules if configured[0] else None, "members": members}

"""Bag items per subject or activity, and the per-day ticks of the derived checklist (kids/school)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .common import _member_id, _now, _required_text


class KidBag:
    def add_bag_item(self, household_id: str, member_id: str, subject: str, label: str, created_by: str) -> str:
        if created_by not in ("parent", "child"):
            raise ValueError("created_by must be parent or child")
        subject, label = _required_text(str(subject or ""), "subject")[:60], _required_text(str(label or ""), "item")[:60]
        item_id = _member_id()
        with self._connection() as connection:
            if not connection.execute("SELECT 1 FROM household_members WHERE id = ? AND household_id = ? AND role = 'child'",
                                      (member_id, household_id)).fetchone():
                raise LookupError("no such child in this household")
            if connection.execute("SELECT COUNT(*) FROM kid_bag_items WHERE member_id = ?", (member_id,)).fetchone()[0] >= 200:
                raise ValueError("too many bag items: remove some first")
            if connection.execute("SELECT 1 FROM kid_bag_items WHERE member_id = ? AND lower(subject) = lower(?) AND lower(label) = lower(?)",
                                  (member_id, subject, label)).fetchone():
                raise ValueError("that item is already on the list")
            connection.execute("INSERT INTO kid_bag_items(id, household_id, member_id, subject, label, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (item_id, household_id, member_id, subject, label, created_by, _now()))
        return item_id

    def list_bag_items(self, household_id: str, member_id: str) -> "list[dict[str, Any]]":
        with self._connection() as connection:
            rows = connection.execute("SELECT id, subject, label, created_by FROM kid_bag_items WHERE household_id = ? AND member_id = ? "
                                      "ORDER BY subject, created_at", (household_id, member_id)).fetchall()
        return [{"id": r[0], "subject": r[1], "label": r[2], "by": r[3]} for r in rows]

    def delete_bag_item(self, household_id: str, item_id: str, member_id: "str | None" = None) -> None:
        """A parent may remove any item; a child (member_id given) only the ones they added."""
        with self._connection() as connection:
            query, args = "SELECT created_by FROM kid_bag_items WHERE id = ? AND household_id = ?", [item_id, household_id]
            if member_id:
                query += " AND member_id = ?"
                args.append(member_id)
            row = connection.execute(query, args).fetchone()
            if not row:
                raise LookupError("no such bag item")
            if member_id and row[0] != "child":
                raise PermissionError("a parent added this one, so only a parent can remove it")
            connection.execute("DELETE FROM kid_bag_items WHERE id = ?", (item_id,))

    def set_bag_tick(self, member_id: str, day: date, key: str, ticked: bool) -> None:
        key = str(key or "").strip().lower()[:80]
        if not key:
            raise ValueError("key is required")
        with self._connection() as connection:
            if ticked:
                connection.execute("INSERT INTO kid_bag_ticks(member_id, day, key, ticked_at) VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING",
                                   (member_id, day.isoformat(), key, _now()))
            else:
                connection.execute("DELETE FROM kid_bag_ticks WHERE member_id = ? AND day = ? AND key = ?", (member_id, day.isoformat(), key))
            connection.execute("DELETE FROM kid_bag_ticks WHERE member_id = ? AND day < ?", (member_id, (day - timedelta(days=14)).isoformat()))

    def list_bag_ticks(self, member_id: str, days: "list[date]") -> "dict[str, set[str]]":
        out: "dict[str, set[str]]" = {d.isoformat(): set() for d in days}
        with self._connection() as connection:
            for day, key in connection.execute("SELECT day, key FROM kid_bag_ticks WHERE member_id = ? AND day IN (%s)" % ",".join("?" * len(days)),
                                               [member_id, *[d.isoformat() for d in days]]) if days else []:
                out[day].add(key)
        return out

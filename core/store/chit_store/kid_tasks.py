"""Homework and tests (kids/learning). Written by the child or a parent; a test is a task with a date that counts down."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .common import _member_id, _now, _required_text

TASK_KINDS = ("homework", "test")
_KEYS = ("id", "kind", "subject", "title", "due_on", "note", "done_at", "created_by", "dismissed_at")


def _clean(value: Any, limit: int) -> "str | None":
    text = str(value).strip() if value is not None else ""
    return text[:limit] or None


class KidTasks:
    def _resolve_subject(self, connection: Any, household_id: str, member_id: str, subject: Any) -> "str | None":
        """Homework is for one of the child's subjects (a lesson in their plan) or for none. The subject's own name is stored, whether it was given by name or by code."""
        wanted = _clean(subject, 60)
        if wanted is None:
            return None
        self._sync_subjects(connection, household_id, member_id)
        row = connection.execute("SELECT name FROM kid_subjects WHERE household_id = ? AND member_id = ? AND archived = 0 AND (lower(name) = lower(?) OR lower(code) = lower(?))",
                                 (household_id, member_id, wanted, wanted)).fetchone()
        if not row:
            raise ValueError("choose one of the child's subjects (they come from the school-day plan)")
        return row[0]

    def _task_fields(self, kind: str, subject: Any, title: str, due_on: Any, note: Any, today: date) -> tuple:
        if kind not in TASK_KINDS:
            raise ValueError("kind must be homework or test")
        try:
            due = date.fromisoformat(str(due_on))
        except ValueError:
            raise ValueError("the date must look like 2026-10-07") from None
        if not today - timedelta(days=30) <= due <= today + timedelta(days=400):
            raise ValueError("the date is too far from today")
        return kind, _clean(subject, 60), _required_text(str(title or ""), "title")[:200], due.isoformat(), _clean(note, 500)

    def add_task(self, household_id: str, member_id: str, kind: str, subject: Any, title: str, due_on: Any, note: Any,
                 created_by: str, today: date) -> str:
        if created_by not in ("parent", "child"):
            raise ValueError("created_by must be parent or child")
        fields = self._task_fields(kind, subject, title, due_on, note, today)
        task_id = _member_id()
        with self._connection() as connection:
            if not connection.execute("SELECT 1 FROM household_members WHERE id = ? AND household_id = ? AND role = 'child'",
                                      (member_id, household_id)).fetchone():
                raise LookupError("no such child in this household")
            if connection.execute("SELECT COUNT(*) FROM kid_tasks WHERE member_id = ? AND done_at IS NULL", (member_id,)).fetchone()[0] >= 300:
                raise ValueError("too many open tasks: tick some off first")
            subject_name = self._resolve_subject(connection, household_id, member_id, fields[1])
            connection.execute(
                "INSERT INTO kid_tasks(id, household_id, member_id, kind, subject, title, due_on, note, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (task_id, household_id, member_id, fields[0], subject_name, fields[2], fields[3], fields[4], created_by, _now()))
        return task_id

    def list_tasks(self, household_id: str, member_id: str, today: date, done_days: int = 14) -> "list[dict[str, Any]]":
        """Open tasks plus the ones finished or dismissed in the last `done_days`, soonest first."""
        since = (today - timedelta(days=done_days)).isoformat()
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, kind, subject, title, due_on, note, done_at, created_by, dismissed_at FROM kid_tasks WHERE household_id = ? AND member_id = ? "
                "AND ((done_at IS NULL AND dismissed_at IS NULL) OR substr(COALESCE(done_at, dismissed_at), 1, 10) >= ?) ORDER BY due_on, created_at", (household_id, member_id, since)).fetchall()
        return [dict(zip(_KEYS, row)) for row in rows]

    def _task(self, connection: Any, household_id: str, task_id: str, member_id: "str | None") -> tuple:
        query, args = "SELECT created_by, member_id FROM kid_tasks WHERE id = ? AND household_id = ?", [task_id, household_id]
        if member_id:                                   # a phone only ever reaches its own child's tasks
            query += " AND member_id = ?"
            args.append(member_id)
        row = connection.execute(query, args).fetchone()
        if not row:
            raise LookupError("no such task")
        return row

    def set_task_done(self, household_id: str, task_id: str, done: bool, member_id: "str | None" = None) -> None:
        with self._connection() as connection:
            self._task(connection, household_id, task_id, member_id)
            # done and dismissed exclude each other: finishing a task that was marked not relevant makes it relevant again
            connection.execute("UPDATE kid_tasks SET done_at = ?, dismissed_at = NULL WHERE id = ?", (_now() if done else None, task_id))

    def set_task_dismissed(self, household_id: str, task_id: str, dismissed: bool, member_id: "str | None" = None) -> None:
        """Mark a task not relevant (the teacher cancelled it) or bring it back. It never counts as done."""
        with self._connection() as connection:
            self._task(connection, household_id, task_id, member_id)
            connection.execute("UPDATE kid_tasks SET dismissed_at = ?, done_at = NULL WHERE id = ?", (_now() if dismissed else None, task_id))

    def update_task(self, household_id: str, task_id: str, kind: str, subject: Any, title: str, due_on: Any, note: Any, today: date) -> None:
        fields = self._task_fields(kind, subject, title, due_on, note, today)
        with self._connection() as connection:
            _, member_id = self._task(connection, household_id, task_id, None)
            fields = (fields[0], self._resolve_subject(connection, household_id, member_id, fields[1]), *fields[2:])
            connection.execute("UPDATE kid_tasks SET kind = ?, subject = ?, title = ?, due_on = ?, note = ? WHERE id = ?", (*fields, task_id))

    def delete_task(self, household_id: str, task_id: str, member_id: "str | None" = None) -> None:
        """A parent may remove any task; a child (member_id given) only the ones they wrote themselves."""
        with self._connection() as connection:
            created_by, _ = self._task(connection, household_id, task_id, member_id)
            if member_id and created_by != "child":
                raise PermissionError("a parent added this one, so only a parent can remove it")
            connection.execute("DELETE FROM kid_tasks WHERE id = ?", (task_id,))

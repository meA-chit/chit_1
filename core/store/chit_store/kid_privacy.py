"""A child's own privacy (kids/kid-view): which sections a child has taken private from their parents, and from what age they may.

Grades and health are the two sections. The parents set the age per household; the child decides, on their own phone, only once they are
at or above it. Privacy never hides anything from the child. The parent screens show a section as private instead of its content.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .common import _now

SECTIONS = ("grades", "health")
DEFAULT_MIN_AGE = {"grades": 10, "health": 14}


def _age(birth_date: "str | None", today: date) -> "int | None":
    if not birth_date:
        return None
    try:
        born = date.fromisoformat(birth_date)
    except ValueError:
        return None
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


class KidPrivacy:
    def privacy_policy(self, household_id: str) -> "dict[str, int]":
        with self._connection() as connection:
            rows = dict(connection.execute("SELECT section, min_age FROM kid_privacy_policy WHERE household_id = ?", (household_id,)).fetchall())
        return {section: int(rows.get(section, DEFAULT_MIN_AGE[section])) for section in SECTIONS}

    def set_privacy_policy(self, household_id: str, section: str, min_age: Any) -> "dict[str, int]":
        if section not in SECTIONS:
            raise ValueError("section must be grades or health")
        if isinstance(min_age, bool) or not isinstance(min_age, int) or not 0 <= min_age <= 18:
            raise ValueError("the age must be a whole number from 0 to 18")
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO kid_privacy_policy(household_id, section, min_age) VALUES (?, ?, ?) "
                "ON CONFLICT(household_id, section) DO UPDATE SET min_age = excluded.min_age", (household_id, section, min_age))
        return self.privacy_policy(household_id)

    def kid_privacy(self, household_id: str, member_id: str, today: date) -> "dict[str, dict[str, Any]]":
        """Per section: the child's age, the age they may choose from, whether they may, and whether it is private right now."""
        policy = self.privacy_policy(household_id)
        with self._connection() as connection:
            born = connection.execute("SELECT birth_date FROM household_members WHERE id = ? AND household_id = ? AND role = 'child'",
                                      (member_id, household_id)).fetchone()
            if born is None:
                raise LookupError("no such child in this household")
            chosen = dict(connection.execute("SELECT section, private FROM kid_privacy WHERE member_id = ?", (member_id,)).fetchall())
        age = _age(born[0], today)
        out = {}
        for section in SECTIONS:
            eligible = age is not None and age >= policy[section]
            out[section] = {"min_age": policy[section], "age": age, "eligible": eligible,
                            "chosen": bool(chosen.get(section)), "private": eligible and bool(chosen.get(section))}
        return out

    def is_private(self, household_id: str, member_id: str, section: str, today: date) -> bool:
        try:
            return self.kid_privacy(household_id, member_id, today)[section]["private"]
        except LookupError:
            return False

    def set_kid_privacy(self, household_id: str, member_id: str, section: str, private: Any, today: date) -> "dict[str, dict[str, Any]]":
        """Only the child's own phone calls this. Taking a section private needs the child to be old enough; giving it back is always allowed."""
        if section not in SECTIONS:
            raise ValueError("section must be grades or health")
        if not isinstance(private, bool):
            raise ValueError("private must be true or false")
        current = self.kid_privacy(household_id, member_id, today)
        if private and not current[section]["eligible"]:
            raise ValueError("Your parents keep this until you are %d." % current[section]["min_age"])
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO kid_privacy(member_id, section, private, updated_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(member_id, section) DO UPDATE SET private = excluded.private, updated_at = excluded.updated_at",
                (member_id, section, int(private), _now()))
        return self.kid_privacy(household_id, member_id, today)

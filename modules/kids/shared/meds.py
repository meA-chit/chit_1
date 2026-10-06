"""Medication helpers. Pure functions."""
from __future__ import annotations

REFILL_WARNING_DAYS = 10


def due_on(weekdays, day):
    return not weekdays or day.weekday() in weekdays


def days_left(supply, weekdays):
    """Days the supply lasts at one dose per scheduled day; None when no supply is tracked."""
    if supply is None:
        return None
    per_week = len(weekdays) or 7
    return int(supply * 7 / per_week)

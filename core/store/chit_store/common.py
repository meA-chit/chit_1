from __future__ import annotations

from datetime import date, datetime, timezone
import secrets
from urllib.parse import urlsplit

WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6}
WEEKDAY_ALIASES = {"mon": "monday", "tue": "tuesday", "wed": "wednesday",
                   "thu": "thursday", "fri": "friday", "sat": "saturday", "sun": "sunday"}
SOURCE_CATEGORIES = {
    "Waste collection": "waste_collection",
    "School / care": "school_care",
    "Sport / activity": "sport_activity",
    "Work": "work",
    "Family": "family",
    "Other": "other",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _required_text(value: str, field: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("%s is required" % field)
    return text


def _optional_date(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return date.fromisoformat(value).isoformat()


COMMUTE_MODES = ("walk", "cycle", "car")


def _commute_mode(value: "str | None") -> "str | None":
    if value in (None, ""):
        return None
    if value not in COMMUTE_MODES:
        raise ValueError("commute mode must be walk, cycle or car")
    return value


def _travel_minutes(value: "int | None") -> "int | None":
    if value in (None, ""):
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 600:
        raise ValueError("travel minutes must be a whole number between 0 and 600")
    return value


def _member_id() -> str:
    return secrets.token_urlsafe(18)


def _safe_url(value: str) -> str:
    url = _required_text(value, "subscription URL")
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"https", "webcal"} or not parsed.netloc:
        raise ValueError("subscription URL must use https or webcal")
    return url

WEEKDAY_NAMES = {value: key for key, value in WEEKDAYS.items()}

# "Latest household" is defined here once: greatest created_at (rowid breaks ties). Editing never changes it.
LATEST_HOUSEHOLD_ORDER = "ORDER BY created_at DESC, rowid DESC"


ADULT_AVATARS = ("a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8")
CHILD_AVATARS = ("k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8")
# One colour per person on every surface (avatar ring, timeline, calendar, chores).
PERSON_COLORS = ("#b79cff", "#4df0ff", "#ff8fb8", "#ffc857", "#8dffb0", "#ff9d5c")
_DEFAULT_ADULT_ORDER = ("a2", "a1", "a4", "a3", "a6", "a5", "a8", "a7")
_DEFAULT_CHILD_ORDER = ("k2", "k3", "k4", "k1", "k6", "k5", "k8", "k7")


def valid_avatar(avatar: "str | None", role: str) -> "str | None":
    if avatar in (None, ""):
        return None
    allowed = ADULT_AVATARS if role == "adult" else CHILD_AVATARS
    if avatar not in allowed:
        raise ValueError("avatar %r is not available for %s members" % (avatar, role))
    return avatar


def valid_color(color: "str | None") -> "str | None":
    if color in (None, ""):
        return None
    import re
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(color)):
        raise ValueError("colour must look like #aabbcc")
    return str(color).lower()


def default_avatar(role: str, index_in_role: int) -> str:
    order = _DEFAULT_ADULT_ORDER if role == "adult" else _DEFAULT_CHILD_ORDER
    return order[index_in_role % len(order)]


def optional_coordinate(value: object, low: float, high: float, field: str) -> "float | None":
    if value in (None, ""):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ValueError("%s must be a number" % field) from None
    if not low <= number <= high:
        raise ValueError("%s must be between %s and %s" % (field, low, high))
    return number

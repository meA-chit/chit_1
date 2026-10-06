"""Read-only iCalendar feed reader (planner/calendar).

Known gaps carried over from the prototype (docs/core/current-implementation.md): RRULE recurrence
is ignored, floating times are treated as UTC, and feed URLs are not checked against private
addresses (SSRF). Fix through a calendar story before widening exposure.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from icalendar import Calendar

MAX_CALENDAR_BYTES = 2_000_000
CALENDAR_LOOKAHEAD_DAYS = 21


def read_calendar_events(subscription_url: str, timezone_name: str) -> list[dict[str, str | bool]]:
    local_zone = ZoneInfo(timezone_name)
    parts = urlsplit(subscription_url)
    if parts.scheme.lower() == "webcal":
        subscription_url = urlunsplit(("https", parts.netloc, parts.path, parts.query, ""))
    request = Request(subscription_url, headers={
        "User-Agent": "Chit-Calendar-Reader/1.0",
        "Accept": "text/calendar, application/ics, text/plain;q=0.8, */*;q=0.5",
    })
    with urlopen(request, timeout=12) as response:
        if response.status < 200 or response.status >= 300:
            raise ValueError("calendar provider returned an unsuccessful response")
        payload = response.read(MAX_CALENDAR_BYTES + 1)
    if len(payload) > MAX_CALENDAR_BYTES:
        raise ValueError("calendar response is larger than the 2 MB limit")
    calendar = Calendar.from_ical(payload)
    start_date = datetime.now(local_zone).date()
    end_date = start_date + timedelta(days=CALENDAR_LOOKAHEAD_DAYS)
    events = []
    for component in calendar.walk("VEVENT"):
        start_value = component.get("DTSTART")
        if start_value is None:
            continue
        start_value = start_value.dt
        is_all_day = isinstance(start_value, date) and not isinstance(start_value, datetime)
        if is_all_day:
            event_date = start_value
            if event_date < start_date or event_date > end_date:
                continue
            start_at = datetime.combine(event_date, time.min)
            end_value = component.get("DTEND")
            end_at = datetime.combine(end_value.dt, time.min) if end_value else start_at + timedelta(days=1)
        else:
            event_at = start_value
            if event_at.tzinfo is None:
                event_at = event_at.replace(tzinfo=timezone.utc)
            event_at = event_at.astimezone(local_zone)
            if event_at.date() < start_date or event_at.date() > end_date:
                continue
            start_at = event_at
            end_value = component.get("DTEND")
            end_at = end_value.dt if end_value else event_at
            if isinstance(end_at, date) and not isinstance(end_at, datetime):
                end_at = datetime.combine(end_at, time.min)
            elif end_at.tzinfo is None:
                end_at = end_at.replace(tzinfo=timezone.utc)
            end_at = end_at.astimezone(local_zone)
        summary = str(component.get("SUMMARY", "Untitled event")).strip()
        events.append({
            "title": summary or "Untitled event",
            "start": start_at.isoformat(),
            "end": end_at.isoformat(),
            "all_day": is_all_day,
        })
    events.sort(key=lambda event: (event["start"], event["title"]))
    return events[:100]

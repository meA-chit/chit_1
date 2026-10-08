"""Helpers for the kids routes: the latest household, its local date, request parsing."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from chit_server.router import HTTPError

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def latest(ctx):
    """-> (household_id, document, local now), or (None, None, None) when nothing is set up."""
    household_id = ctx.store.latest_household_id()
    if household_id is None:
        return None, None, None
    document = ctx.store.get_household_document(household_id)
    return household_id, document, datetime.now(ZoneInfo(document["household"]["timezone"]))


def need_household(ctx):
    household_id, document, now = latest(ctx)
    if household_id is None:
        raise HTTPError(404, "Set up a household first")
    return household_id, document, now


def children(document):
    return [m for m in document["members"] if m["role"] == "child"]


def adults(document):
    return [m for m in document["members"] if m["role"] == "adult"]


def body(request):
    data = request.json()
    if not isinstance(data, dict):
        raise HTTPError(400, "Request body must be a JSON object")
    return data


def parse_day(value, now, past_days=30, future_days=0):
    """A YYYY-MM-DD string within the allowed window around today; None means today."""
    if not value:
        return now.date()
    try:
        day = date.fromisoformat(str(value))
    except ValueError:
        raise HTTPError(400, "date must look like 2026-10-07") from None
    if not now.date() - timedelta(days=past_days) <= day <= now.date() + timedelta(days=future_days):
        raise HTTPError(400, "date is outside the allowed range")
    return day


def child_id(document, request, field="member"):
    """The child a request is about: ?member=<id> or the first child."""
    kids = children(document)
    wanted = request.query.get(field)
    if wanted:
        if not any(k["client_id"] == wanted for k in kids):
            raise HTTPError(404, "No such child in this household")
        return wanted
    return kids[0]["client_id"] if kids else None


def checked(call, *args, **kwargs):
    """Run a store call and turn its validation errors into HTTP errors."""
    try:
        return call(*args, **kwargs)
    except PermissionError as error:
        raise HTTPError(403, str(error)) from None
    except LookupError as error:
        raise HTTPError(404, str(error)) from None
    except ValueError as error:
        raise HTTPError(400, str(error)) from None

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from chit_server.icons import icon_for
from chit_server.loader import load_file_module

reader = load_file_module(Path(__file__).with_name("reader.py"))


def agenda(ctx, request):
    household = ctx.store.latest_household_calendar_sources()
    if household is None or not household["sources"]:
        payload = {"state": "unavailable", "reason": "unconfigured", "events": []}
        if household is not None:
            payload["household"] = household["name"]
        return 200, payload
    events, summaries, any_error = [], [], False
    for source in household["sources"]:
        try:
            source_events = reader.read_calendar_events(source["subscription_url"], household["timezone"])
            ctx.store.record_calendar_check(source["id"], "available")
            for event in source_events:
                event.update(source=source["name"], category=source["category"], members=source["members"], member_ids=source["member_ids"],
                             icon=icon_for(event["title"], source["category"]))
                events.append(event)
            summaries.append({"name": source["name"], "state": "available", "event_count": len(source_events)})
        except Exception as error:
            any_error = True
            state = "stale" if source["last_checked_at"] else "unavailable"
            ctx.store.record_calendar_check(source["id"], state)
            ctx.log("calendar read failed for source %s (%s)" % (source["id"], type(error).__name__))
            summaries.append({"name": source["name"], "state": state, "event_count": 0})
    events.sort(key=lambda event: (event["start"], event["title"]))
    state = "partial" if any_error and events else "unavailable" if any_error else "available"
    return 200, {
        "state": state,
        "household": household["name"],
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "range_days": reader.CALENDAR_LOOKAHEAD_DAYS,
        "sources": summaries,
        "events": events[:100],
    }


def register(router) -> None:
    router.get("/api/planner/calendar/agenda")(agenda)

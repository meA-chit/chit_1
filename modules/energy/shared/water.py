"""Water usage from manual meter readings: total meter, garden meter, household = total - garden.

A reading is the number on the meter. Usage over a period is the difference between the meter at its start and end; when a
period boundary falls between two readings the meter is interpolated linearly (a stated estimate, flagged `estimated`).
Nothing is extrapolated beyond the first or last reading: a period is clipped to the readings and flagged `partial`.
"""
from __future__ import annotations

from datetime import date, timedelta

Points = list  # of (date, value), oldest first


def _month_start(day: date) -> date:
    return day.replace(day=1)


def _next_month(day: date) -> date:
    return (day.replace(day=28) + timedelta(days=4)).replace(day=1)


def at(points: Points, day: date) -> "tuple[float, bool] | None":
    """Meter value on `day` -> (value, exact), or None when the day is outside the readings."""
    if not points or day < points[0][0] or day > points[-1][0]:
        return None
    for index, (d, v) in enumerate(points):
        if d == day:
            return v, True
        if d > day:
            (d0, v0) = points[index - 1]
            return v0 + (v - v0) * ((day - d0).days / (d - d0).days), False
    return None


def usage(points: Points, start: date, end: date) -> "dict | None":
    """Usage between `start` and `end` (end exclusive for calendar periods, but readings are on dates), clipped to the readings."""
    if len(points) < 2:
        return None
    a, b = max(start, points[0][0]), min(end, points[-1][0])
    if a >= b:
        return None
    first, last = at(points, a), at(points, b)
    return {"value": round(last[0] - first[0], 3), "from": a.isoformat(), "to": b.isoformat(),
            "estimated": not (first[1] and last[1]), "partial": (a, b) != (start, end)}


def household(total: Points, garden: Points, start: date, end: date) -> "dict | None":
    """total - garden over the window both meters cover."""
    if len(total) < 2 or len(garden) < 2:
        return None
    lo, hi = max(start, total[0][0], garden[0][0]), min(end, total[-1][0], garden[-1][0])
    t, g = usage(total, lo, hi), usage(garden, lo, hi)
    if not t or not g:
        return None
    return {"value": round(t["value"] - g["value"], 3), "from": t["from"], "to": t["to"],
            "estimated": t["estimated"] or g["estimated"], "partial": (lo, hi) != (start, end)}


def _row(label: str, total: Points, garden: Points, start: date, end: date) -> dict:
    t, g, h = usage(total, start, end), usage(garden, start, end), household(total, garden, start, end)
    return {"label": label, "total": t, "garden": g, "household": h}


def intervals(total: Points, garden: Points) -> dict:
    """Average use per day between consecutive readings: the trend basis. No interpolation, only the dates actually read.

    Household needs both meters read on the same days, so it uses the days both were read. With fewer than two such days it falls back
    to the total meter alone (`basis: total`). Each item: from, to, days, and per meter {m3, litres_per_day}.
    """
    both = sorted(set(dict(total)) & set(dict(garden)))
    basis = "household" if len(both) >= 2 else "total"
    days = both if basis == "household" else [d for d, _ in total]
    t, g = dict(total), dict(garden)
    items = []
    for a, b in zip(days, days[1:]):
        n = (b - a).days
        row = {"from": a.isoformat(), "to": b.isoformat(), "days": n}
        deltas = {"total": round(t[b] - t[a], 3)}
        if basis == "household":
            deltas["garden"] = round(g[b] - g[a], 3)
            deltas["household"] = round(deltas["total"] - deltas["garden"], 3)
        for key, m3 in deltas.items():
            row[key] = {"m3": m3, "litres_per_day": round(m3 * 1000 / n, 1)}
        items.append(row)
    return {"basis": basis, "items": items, "trend": trend(items, "household" if basis == "household" else "total")}


def trend(items: list, key: str) -> "dict | None":
    """Latest period against the one before and against the average of everything earlier. Needs two periods, else None."""
    if len(items) < 2:
        return None
    latest, earlier = items[-1], items[:-1]
    days = sum(i["days"] for i in earlier)
    baseline = sum(i[key]["m3"] for i in earlier) * 1000 / days
    before = earlier[-1][key]["litres_per_day"]
    now = latest[key]["litres_per_day"]
    ratio = lambda a, b: round((a - b) / b, 3) if b > 0 else None
    overall = sum(i[key]["m3"] for i in items) * 1000 / sum(i["days"] for i in items)
    return {"key": key, "from": latest["from"], "to": latest["to"], "litres_per_day": now, "previous": before, "baseline": round(baseline, 1),
            "overall": round(overall, 1), "vs_previous": ratio(now, before), "vs_baseline": ratio(now, baseline), "periods": len(items)}


def summarize(readings: "list[dict]", today: date) -> dict:  # `today` is reserved for rate-based figures later
    """readings: rows from the store. -> everything the Water card shows."""
    series = {"water_total": [], "water_garden": []}
    for r in readings:
        series[r["meter"]].append((date.fromisoformat(r["read_on"]), r["value"]))
    total, garden = series["water_total"], series["water_garden"]
    every = sorted({d for d, _ in total + garden})
    if not every:
        return {"months": [], "years": [], "rows": [], "warnings": [], "intervals": {"basis": "total", "items": [], "trend": None}}

    months, month = [], _month_start(every[0])
    while month <= every[-1]:
        row = _row(month.strftime("%Y-%m"), total, garden, month, _next_month(month))
        if row["total"] or row["garden"]:
            months.append(row)
        month = _next_month(month)
    years = []
    for year in range(every[0].year, every[-1].year + 1):
        row = _row(str(year), total, garden, date(year, 1, 1), date(year + 1, 1, 1))
        if row["total"] or row["garden"]:
            years.append(row)

    rows, last = [], {}
    for day in every:
        row = {"read_on": day.isoformat(), "note": next((r["note"] for r in readings if r["read_on"] == day.isoformat() and r["note"]), "")}
        for key, points in (("total", total), ("garden", garden)):
            value = dict(points).get(day)
            entry = None
            if value is not None:
                prev = last.get(key)
                entry = {"value": value, "since": None if prev is None else {"from": prev[0].isoformat(), "days": (day - prev[0]).days, "used": round(value - prev[1], 3)}}
                last[key] = (day, value)
            row[key] = entry
        rows.append(row)

    warnings = []
    for label, h in [(m["label"], m["household"]) for m in months]:
        if h and h["value"] < 0:
            warnings.append("%s: garden counted more than the total meter. Check both readings." % label)
    return {"months": months, "years": years, "rows": rows[::-1], "warnings": warnings, "intervals": intervals(total, garden),
            "first": every[0].isoformat(), "last": every[-1].isoformat()}

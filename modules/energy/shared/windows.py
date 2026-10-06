"""Pick the best windows for heavy workloads (washing, drying, dishwasher, EV top-up, oven batch cooking).

Pure functions, no I/O. Slots are whole clock hours. A window is `length` consecutive hours; its score is the mean
effective price, lower is better. Effective price = grid price x (1 - solar share), where the solar share of an hour is
the expected PV output divided by a typical heavy load (HEAVY_LOAD_KW), capped at 1: solar that the load can soak up
displaces bought power. Without PV data the score is the plain mean price.
"""
from __future__ import annotations

from datetime import datetime, timedelta

HEAVY_LOAD_KW = 2.0
MIN_GAP_HOURS = 1
FLAT_BAND = 0.05   # under 5 % better than the average: not worth moving a job for


def best_windows(slots, now: datetime, length: int = 2, count: int = 2):
    """slots: [{'start': datetime (naive, local, on the hour), 'price': float, 'solar_kw': float | None}], any order.

    Returns the `count` best windows, at least MIN_GAP_HOURS apart, that start at the next full hour or later.
    """
    horizon_start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    usable = sorted((s for s in slots if s["start"] >= horizon_start and s["price"] is not None), key=lambda s: s["start"])
    if not usable:
        return {"windows": [], "average_price": None}
    average = sum(s["price"] for s in usable) / len(usable)

    def effective(slot):
        share = min(1.0, (slot["solar_kw"] or 0) / HEAVY_LOAD_KW)
        return slot["price"] * (1 - share)

    candidates = []
    for index in range(len(usable) - length + 1):
        run = usable[index:index + length]
        contiguous = all(run[i + 1]["start"] - run[i]["start"] == timedelta(hours=1) for i in range(length - 1))
        if not contiguous:
            continue
        price = sum(s["price"] for s in run) / length
        score = sum(effective(s) for s in run) / length
        solar = [s["solar_kw"] for s in run if s["solar_kw"] is not None]
        candidates.append({
            "start": run[0]["start"], "end": run[-1]["start"] + timedelta(hours=1), "average_price": price,
            "score": score, "solar_kw": round(sum(solar) / len(solar), 2) if solar else None,
            "vs_average": (price - average) / average if average else 0.0,
        })
    chosen: list = []
    for candidate in sorted(candidates, key=lambda c: (c["score"], c["start"])):
        gap = timedelta(hours=MIN_GAP_HOURS)   # a second window that merely touches the first would be the same advice twice
        if all(candidate["end"] + gap <= taken["start"] or candidate["start"] >= taken["end"] + gap for taken in chosen):
            chosen.append(candidate)
        if len(chosen) == count:
            break
    return {"windows": chosen, "average_price": average}

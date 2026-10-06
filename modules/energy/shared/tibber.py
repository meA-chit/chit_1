"""Tibber: hourly prices and (with a Pulse or smart meter) hourly consumption, read through Tibber's GraphQL API.

Prices are published for today and, from about 13:00, tomorrow. Tibber may return hourly or quarter-hourly
prices; everything here is reduced to one value per local clock hour (the mean of the slots in that hour).
Timestamps keep the offset of the Tibber home, so the date and hour are read from the text itself; this
assumes the household time zone equals the Tibber home's, which is the normal case.
"""
from __future__ import annotations

from pathlib import Path

from chit_server.loader import load_file_module

net = load_file_module(Path(__file__).with_name("net.py"))

URL = "https://api.tibber.com/v1-beta/gql"
PRICE_TTL = 10 * 60
CONSUMPTION_TTL = 15 * 60


def _gql(token: str, query: str) -> dict:
    payload = net.request_json(URL, body={"query": query}, headers={"Authorization": "Bearer " + token})
    if payload.get("errors") and not payload.get("data"):
        text = " ".join(str(e.get("message", "")) for e in payload["errors"]).lower()
        kind = "auth" if "token" in text or "unauth" in text else "unavailable"
        raise net.ProviderError(kind, "Tibber reported an error")
    return payload.get("data") or {}


def verify(token: str) -> dict:
    """Check the token and pick the home to read: the first one with a running subscription."""
    data = _gql(token, "{ viewer { homes { id appNickname currentSubscription { status } } } }")
    homes = ((data.get("viewer") or {}).get("homes")) or []
    usable = [h for h in homes if (h.get("currentSubscription") or {}).get("status") in (None, "running")] or homes
    if not usable:
        raise net.ProviderError("unavailable", "this Tibber account has no home")
    return {"home_id": usable[0]["id"], "homes": len(homes)}


def hourly(entries, value_key: str) -> dict:
    """[{<time key>: ISO text with offset, value_key: number}] -> {(YYYY-MM-DD, hour): mean value}."""
    buckets: dict = {}
    for entry in entries or []:
        stamp = entry.get("startsAt") or entry.get("from")
        value = entry.get(value_key)
        if not stamp or value is None:
            continue
        buckets.setdefault((stamp[:10], int(stamp[11:13])), []).append(float(value))
    return {key: sum(values) / len(values) for key, values in buckets.items()}


def prices(token: str, home_id: str):
    """-> ({'currency', 'today': {hour: price}, 'tomorrow': {hour: price}, 'levels'}, fetched_at, stale)"""
    def produce():
        data = _gql(token, '{ viewer { home(id: "%s") { currentSubscription { priceInfo { '
                           'today { total startsAt level currency } tomorrow { total startsAt level currency } } } } } }' % home_id)
        info = ((((data.get("viewer") or {}).get("home") or {}).get("currentSubscription") or {}).get("priceInfo")) or {}
        today, tomorrow = info.get("today") or [], info.get("tomorrow") or []
        if not today:
            raise net.ProviderError("unavailable", "Tibber returned no prices")
        return {
            "currency": next((e.get("currency") for e in today if e.get("currency")), None),
            "by_hour": {**hourly(today, "total"), **hourly(tomorrow, "total")},
            "levels": {(e["startsAt"][:10], int(e["startsAt"][11:13])): e.get("level") for e in today + tomorrow if e.get("startsAt")},
        }
    return net.CACHE.fetch(("tibber-prices", net.fingerprint(token, home_id)), PRICE_TTL, produce)


def consumption(token: str, home_id: str):
    """-> ({(date, hour): kWh} or None when the home has no meter data, fetched_at, stale). Never raises for 'no meter'."""
    def produce():
        data = _gql(token, '{ viewer { home(id: "%s") { consumption(resolution: HOURLY, last: 48) { nodes { from consumption } } } } }' % home_id)
        nodes = ((((data.get("viewer") or {}).get("home") or {}).get("consumption") or {}).get("nodes")) or []
        return hourly(nodes, "consumption") or None
    return net.CACHE.fetch(("tibber-consumption", net.fingerprint(token, home_id)), CONSUMPTION_TTL, produce)


def monthly(token: str, home_id: str):
    """-> ({'YYYY-MM': {'kwh', 'cost'}} or None without meter data, fetched_at, stale). Last 12 months, as Tibber reports them.

    `cost` is the amount Tibber reports for the period, in the home's currency; it is None for months without it.
    """
    def produce():
        data = _gql(token, '{ viewer { home(id: "%s") { consumption(resolution: MONTHLY, last: 12) { nodes { from consumption cost } } } } }' % home_id)
        nodes = ((((data.get("viewer") or {}).get("home") or {}).get("consumption") or {}).get("nodes")) or []
        months = {n["from"][:7]: {"kwh": n.get("consumption"), "cost": n.get("cost")} for n in nodes if n.get("from")}
        return months or None
    return net.CACHE.fetch(("tibber-monthly", net.fingerprint(token, home_id)), 30 * 60, produce)

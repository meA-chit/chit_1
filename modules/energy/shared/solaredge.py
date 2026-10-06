"""SolarEdge monitoring API: site details, today's production and the hourly production curve.

Limits (SolarEdge): 300 requests per day per site and per account, so everything is cached (overview 10 min,
hourly curve 20 min) and one dashboard refresh costs at most two requests. Errors never include the URL,
because the API key travels in the query string.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, urlencode

from chit_server.loader import load_file_module

net = load_file_module(Path(__file__).with_name("net.py"))

BASE = "https://monitoringapi.solaredge.com/site/"
OVERVIEW_TTL = 10 * 60
CURVE_TTL = 20 * 60


def _get(site_id: str, path: str, api_key: str, **query) -> dict:
    return net.request_json("%s%s/%s?%s" % (BASE, quote(str(site_id), safe=""), path, urlencode({**query, "api_key": api_key})))


def verify(site_id: str, api_key: str) -> dict:
    details = (_get(site_id, "details", api_key).get("details")) or {}
    if not details:
        raise net.ProviderError("unavailable", "SolarEdge returned no site")
    return {"name": details.get("name"), "peak_kw": details.get("peakPower"), "status": details.get("status")}


def overview(site_id: str, api_key: str):
    """-> ({'current_kw', 'today_kwh', 'month_kwh', 'lifetime_kwh', 'last_update'}, fetched_at, stale)"""
    def produce():
        data = (_get(site_id, "overview", api_key).get("overview")) or {}
        if not data:
            raise net.ProviderError("unavailable", "SolarEdge returned no overview")
        kwh = lambda block: round(block["energy"] / 1000, 2) if isinstance(block, dict) and block.get("energy") is not None else None  # noqa: E731
        power = (data.get("currentPower") or {}).get("power")
        return {"current_kw": round(power / 1000, 2) if power is not None else None,
                "today_kwh": kwh(data.get("lastDayData")), "month_kwh": kwh(data.get("lastMonthData")),
                "lifetime_kwh": kwh(data.get("lifeTimeData")), "last_update": data.get("lastUpdateTime")}
    return net.CACHE.fetch(("solaredge-overview", net.fingerprint(site_id, api_key)), OVERVIEW_TTL, produce)


def hourly_production(site_id: str, api_key: str, day: str):
    """-> ({hour: kWh}, fetched_at, stale) for one local date (YYYY-MM-DD). Hours without data are absent, not zero."""
    def produce():
        values = ((_get(site_id, "energy", api_key, timeUnit="HOUR", startDate=day, endDate=day).get("energy")) or {}).get("values") or []
        return {int(v["date"][11:13]): round(v["value"] / 1000, 3) for v in values if v.get("value") is not None and v.get("date", "")[:10] == day}
    return net.CACHE.fetch(("solaredge-hourly", net.fingerprint(site_id, api_key), day), CURVE_TTL, produce)

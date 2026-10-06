"""Expected solar output for the next two days: Open-Meteo shortwave radiation scaled by the PV peak power.

This is an ESTIMATE (state `forecast`), never a measurement: kW = peak_kW x radiation / 1000 W/m2 x 0.8
(a typical system performance ratio). It only ranks hours for suggestions and is shown as such.
"""
from __future__ import annotations

from pathlib import Path

from chit_server.loader import load_file_module

net = load_file_module(Path(__file__).with_name("net.py"))

API = ("https://api.open-meteo.com/v1/forecast?latitude={lat:.4f}&longitude={lon:.4f}"
       "&hourly=shortwave_radiation&timezone=auto&forecast_days=2")
PERFORMANCE_RATIO = 0.8
TTL = 60 * 60


def expected_kw(latitude: float, longitude: float, peak_kw: float):
    """-> ({(date, hour): kW}, fetched_at, stale)"""
    def produce():
        hourly = (net.request_json(API.format(lat=latitude, lon=longitude)).get("hourly")) or {}
        times, radiation = hourly.get("time") or [], hourly.get("shortwave_radiation") or []
        if not times:
            raise net.ProviderError("unavailable", "no radiation forecast")
        return {(t[:10], int(t[11:13])): round(peak_kw * (r or 0) / 1000 * PERFORMANCE_RATIO, 3) for t, r in zip(times, radiation)}
    return net.CACHE.fetch(("solar-forecast", round(latitude, 2), round(longitude, 2), peak_kw), TTL, produce)

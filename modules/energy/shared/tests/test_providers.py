from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError as UrlHTTPError
import json
import unittest
from unittest.mock import patch

from chit_server.loader import load_file_module

shared = Path(__file__).parents[1]
net = load_file_module(shared / "net.py")
tibber = load_file_module(shared / "tibber.py")
solaredge = load_file_module(shared / "solaredge.py")
windows = load_file_module(shared / "windows.py")


class Response(BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def reply(payload):
    return Response(json.dumps(payload).encode())


def http_error(code, body=b"{}"):
    return UrlHTTPError("https://x.example/?api_key=SECRET", code, "x", {}, BytesIO(body))


class NetTests(unittest.TestCase):
    def setUp(self):
        net.CACHE.clear()

    def test_classifies_failures_and_never_leaks_the_url(self):
        for code, kind in ((401, "auth"), (403, "auth"), (429, "rate_limited"), (500, "unavailable")):
            with patch.object(net, "urlopen", side_effect=http_error(code)):
                with self.assertRaises(net.ProviderError) as raised:
                    net.request_json("https://x.example/?api_key=SECRET")
            self.assertEqual(raised.exception.kind, kind)
            self.assertNotIn("SECRET", str(raised.exception))
        with patch.object(net, "urlopen", side_effect=http_error(400, b'{"errors":[{"message":"invalid token"}]}')):
            with self.assertRaises(net.ProviderError) as raised:
                net.request_json("https://x.example")
        self.assertEqual(raised.exception.kind, "auth")        # Tibber answers a bad token with HTTP 400
        with patch.object(net, "urlopen", side_effect=OSError("boom")):
            with self.assertRaises(net.ProviderError) as raised:
                net.request_json("https://x.example")
        self.assertEqual(raised.exception.kind, "unavailable")

    def test_cache_serves_the_last_value_stale_when_the_provider_fails(self):
        calls = iter([1, net.ProviderError("unavailable", "down")])

        def producer():
            value = next(calls)
            if isinstance(value, Exception):
                raise value
            return value
        self.assertEqual(net.CACHE.fetch("k", 0, producer)[0::2], (1, False))
        value, _, stale = net.CACHE.fetch("k", 0, producer)    # ttl 0: refresh, which fails
        self.assertEqual((value, stale), (1, True))

    def test_a_rejected_key_is_never_served_from_cache(self):
        net.CACHE.fetch("k", 0, lambda: 1)

        def rejected():
            raise net.ProviderError("auth", "no")
        with self.assertRaises(net.ProviderError):
            net.CACHE.fetch("k", 0, rejected)


class TibberTests(unittest.TestCase):
    def setUp(self):
        net.CACHE.clear()

    def test_quarter_hours_are_averaged_into_clock_hours(self):
        slots = [{"startsAt": "2026-10-06T14:%02d:00.000+02:00" % m, "total": v} for m, v in ((0, 0.2), (15, 0.3), (30, 0.2), (45, 0.3))]
        self.assertEqual(tibber.hourly(slots, "total"), {("2026-10-06", 14): 0.25})

    def test_prices_today_and_tomorrow(self):
        data = {"data": {"viewer": {"home": {"currentSubscription": {"priceInfo": {
            "today": [{"total": 0.30, "startsAt": "2026-10-06T00:00:00.000+02:00", "level": "CHEAP", "currency": "EUR"}],
            "tomorrow": [{"total": 0.20, "startsAt": "2026-10-07T00:00:00.000+02:00", "level": "CHEAP", "currency": "EUR"}]}}}}}}
        with patch.object(net, "urlopen", return_value=reply(data)):
            prices, _, stale = tibber.prices("tok", "home")
        self.assertEqual((prices["currency"], stale), ("EUR", False))
        self.assertEqual(prices["by_hour"], {("2026-10-06", 0): 0.30, ("2026-10-07", 0): 0.20})

    def test_verify_picks_a_running_home(self):
        data = {"data": {"viewer": {"homes": [{"id": "old", "currentSubscription": {"status": "ended"}},
                                              {"id": "now", "currentSubscription": {"status": "running"}}]}}}
        with patch.object(net, "urlopen", return_value=reply(data)):
            self.assertEqual(tibber.verify("tok"), {"home_id": "now", "homes": 2})

    def test_no_meter_means_no_consumption_not_zeros(self):
        data = {"data": {"viewer": {"home": {"consumption": {"nodes": []}}}}}
        with patch.object(net, "urlopen", return_value=reply(data)):
            self.assertIsNone(tibber.consumption("tok", "home")[0])

    def test_graphql_errors_are_classified(self):
        with patch.object(net, "urlopen", return_value=reply({"errors": [{"message": "Context creation failed: invalid token"}], "data": None})):
            with self.assertRaises(net.ProviderError) as raised:
                tibber.verify("bad")
        self.assertEqual(raised.exception.kind, "auth")


class SolarEdgeTests(unittest.TestCase):
    def setUp(self):
        net.CACHE.clear()

    def test_overview_in_kwh_and_hourly_curve_leaves_gaps_empty(self):
        overview = {"overview": {"lastUpdateTime": "2026-10-06 12:41:00", "currentPower": {"power": 3200.0},
                                 "lastDayData": {"energy": 14500.0}, "lastMonthData": {"energy": 300000.0}, "lifeTimeData": {"energy": 9000000.0}}}
        with patch.object(net, "urlopen", return_value=reply(overview)):
            summary, _, _ = solaredge.overview("123", "KEY")
        self.assertEqual((summary["current_kw"], summary["today_kwh"], summary["lifetime_kwh"]), (3.2, 14.5, 9000.0))
        curve = {"energy": {"values": [{"date": "2026-10-06 09:00:00", "value": 800.0}, {"date": "2026-10-06 10:00:00", "value": None}]}}
        with patch.object(net, "urlopen", return_value=reply(curve)):
            hours, _, _ = solaredge.hourly_production("123", "KEY", "2026-10-06")
        self.assertEqual(hours, {9: 0.8})


def slot(day, hour, price, solar=None):
    return {"start": datetime(2026, 10, day, hour), "price": price, "solar_kw": solar}


class WindowTests(unittest.TestCase):
    NOW = datetime(2026, 10, 6, 10, 20)

    def test_two_best_non_overlapping_windows_from_the_next_full_hour(self):
        prices = [0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30,   # 00-11: 00-10 are past
                  0.28, 0.12, 0.10, 0.26, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.18, 0.15]    # 22 and 23 are cheap too
        slots = [slot(6, h, p) for h, p in enumerate(prices)]
        result = windows.best_windows(slots, self.NOW, length=2, count=2)
        starts = [w["start"].hour for w in result["windows"]]
        self.assertEqual(starts, [13, 22])
        self.assertTrue(result["windows"][0]["vs_average"] < -0.3)
        self.assertGreaterEqual(min(starts), 11)                  # nothing before the next full hour

    def test_the_second_window_is_a_real_alternative_not_the_neighbouring_hours(self):
        prices = {11: 0.10, 12: 0.10, 13: 0.10, 14: 0.10, 15: 0.10, 16: 0.10, 17: 0.30, 18: 0.30}
        result = windows.best_windows([slot(6, h, p) for h, p in prices.items()], self.NOW, length=2, count=2)
        first, second = result["windows"]
        self.assertGreaterEqual((second["start"] - first["end"]).total_seconds() / 3600 if second["start"] > first["start"] else (first["start"] - second["end"]).total_seconds() / 3600, 1)

    def test_windows_never_span_a_gap_in_prices(self):
        slots = [slot(6, 12, 0.1), slot(6, 14, 0.1), slot(6, 16, 0.5), slot(6, 17, 0.5)]
        result = windows.best_windows(slots, self.NOW, length=2, count=2)
        self.assertEqual([w["start"].hour for w in result["windows"]], [16])

    def test_sun_makes_a_sunny_window_win_over_a_slightly_cheaper_one(self):
        slots = [slot(6, 12, 0.20, 0.0), slot(6, 13, 0.20, 0.0), slot(6, 14, 0.22, 2.5), slot(6, 15, 0.22, 2.5)]
        self.assertEqual(windows.best_windows(slots, self.NOW)["windows"][0]["start"].hour, 14)
        no_sun = [slot(6, h, p) for h, p in ((12, 0.20), (13, 0.20), (14, 0.22), (15, 0.22))]
        self.assertEqual(windows.best_windows(no_sun, self.NOW)["windows"][0]["start"].hour, 12)

    def test_nothing_left_today_and_no_tomorrow_prices_gives_no_windows(self):
        slots = [slot(6, h, 0.2) for h in range(0, 11)]
        self.assertEqual(windows.best_windows(slots, self.NOW)["windows"], [])


if __name__ == "__main__":
    unittest.main()

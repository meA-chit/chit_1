from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chit_server.loader import load_file_module
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
DAY = "2026-10-06"


def prices(base=0.30):
    return {"currency": "EUR", "by_hour": {(DAY, h): base + (0.1 if 17 <= h <= 20 else (-0.1 if 12 <= h <= 14 else 0)) for h in range(24)},
            "levels": {(DAY, 13): "CHEAP"}}


class BuildDayTests(unittest.TestCase):
    def test_average_current_and_comparison(self):
        consumption = {(DAY, h): 0.5 for h in range(0, 15)}
        payload = routes.build_day(prices(), consumption, DAY, 13)
        self.assertEqual(len(payload["hours"]), 24)
        self.assertAlmostEqual(payload["average_price"], 0.3 + (4 * 0.1 - 3 * 0.1) / 24, places=3)
        self.assertEqual(payload["current"]["hour"], 13)
        self.assertLess(payload["current"]["vs_average"], 0)                    # 13:00 is cheaper than the day's average
        self.assertEqual((payload["cheapest_hour"] in (12, 13, 14), payload["priciest_hour"] in (17, 18, 19, 20)), (True, True))
        self.assertEqual(payload["consumption"]["hours_reported"], 15)
        self.assertEqual(payload["consumption"]["total_kwh"], 7.5)
        self.assertLess(payload["consumption"]["paid_average_price"], payload["average_price"])   # most use fell in cheap hours? 12-14 only
        self.assertIsNone(payload["hours"][20]["consumption"])                    # absent hours are None, never 0

    def test_no_meter_is_reported_not_zeroed(self):
        payload = routes.build_day(prices(), None, DAY, 9)
        self.assertEqual(payload["consumption"], {"state": "unavailable", "reason": "no_meter"})
        self.assertTrue(all(h["consumption"] is None for h in payload["hours"]))
        self.assertIsNone(routes.build_day(prices(), None, DAY, 9)["consumption"].get("paid_average_price"))


class TotalsTests(unittest.TestCase):
    MONTHS = {"2025-12": {"kwh": 400.0, "cost": 150.0}, "2026-01": {"kwh": 380.0, "cost": 140.0},
              "2026-02": {"kwh": 300.0, "cost": 100.5}, "2026-10": {"kwh": 90.0, "cost": 31.25}}

    def test_month_and_year_to_date_in_money(self):
        totals = routes.build_totals(self.MONTHS, "2026-10-06", "EUR")
        self.assertEqual(totals["month"], {"cost": 31.25, "kwh": 90.0})
        self.assertEqual(totals["year"], {"cost": 271.75, "kwh": 770.0})     # last year's December is not in this year
        self.assertIsNone(totals["year_from"])

    def test_year_starting_mid_year_says_where_it_starts(self):
        totals = routes.build_totals({"2026-08": {"kwh": 1.0, "cost": 1.0}, "2026-10": {"kwh": 2.0, "cost": 2.0}}, "2026-10-06", "EUR")
        self.assertEqual(totals["year_from"], "2026-08")

    def test_missing_figures_are_unavailable_not_zero(self):
        self.assertEqual(routes.build_totals(None, "2026-10-06", "EUR")["state"], "unavailable")
        self.assertEqual(routes.build_totals({"2026-10": {"kwh": 2.0, "cost": None}}, "2026-10-06", "EUR")["reason"], "no_cost")
        partial = routes.build_totals({"2026-09": {"kwh": 5.0, "cost": 2.0}}, "2026-10-06", "EUR")
        self.assertIsNone(partial["month"])                                    # this month has no figure yet


class DayViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "e.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)
        routes.net.CACHE.clear()

    def tearDown(self):
        self.temp.cleanup()

    def test_unconfigured_without_a_token(self):
        _, payload = routes.day_view(self.ctx, Request("GET", "/x", {}, ""))
        self.assertEqual((payload["state"], payload["reason"]), ("unconfigured", "no_tibber_token"))

    def test_available_with_a_token(self):
        self.store.set_energy_connection("hh-meyer", "tibber", "t" * 30, {"home_id": "h"})
        today = datetime.now(routes.household.ZoneInfo(self.store.get_household_document("hh-meyer")["household"]["timezone"])).date().isoformat()
        fake = {"currency": "EUR", "by_hour": {(today, h): 0.25 for h in range(24)}, "levels": {}}
        with patch.object(routes.tibber, "prices", return_value=(fake, "2026-10-06T10:00:00+00:00", False)), \
                patch.object(routes.tibber, "consumption", return_value=({(today, 0): 0.4}, "x", False)), \
                patch.object(routes.tibber, "monthly", return_value=({today[:7]: {"kwh": 90.0, "cost": 30.0}}, "x", False)):
            _, payload = routes.day_view(self.ctx, Request("GET", "/x", {}, ""))
        self.assertEqual((payload["state"], payload["source"], payload["currency"]), ("available", "Tibber", "EUR"))
        self.assertNotIn("t" * 30, repr(payload))
        self.assertEqual(payload["totals"]["month"]["cost"], 30.0)

    def test_rejected_token_and_provider_down_are_unavailable(self):
        self.store.set_energy_connection("hh-meyer", "tibber", "t" * 30, {"home_id": "h"})
        for kind, reason in (("auth", "token_rejected"), ("unavailable", "unavailable")):
            with patch.object(routes.tibber, "prices", side_effect=routes.net.ProviderError(kind, "x")):
                _, payload = routes.day_view(self.ctx, Request("GET", "/x", {}, ""))
            self.assertEqual((payload["state"], payload["reason"]), ("unavailable", reason))

    def test_date_is_validated(self):
        self.store.set_energy_connection("hh-meyer", "tibber", "t" * 30, {"home_id": "h"})
        with self.assertRaises(HTTPError):
            routes.day_view(self.ctx, Request("GET", "/x", {"date": "yesterday"}, ""))


if __name__ == "__main__":
    unittest.main()

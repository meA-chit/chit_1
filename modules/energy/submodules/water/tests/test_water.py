from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from chit_server.loader import load_file_module
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
water = routes.water


def post(readings):
    return Request("POST", "/x", {}, "application/json", json.dumps({"readings": readings}).encode())


class WaterMathTests(unittest.TestCase):
    TOTAL = [(date(2025, 12, 1), 100.0), (date(2026, 1, 1), 110.0), (date(2026, 2, 1), 125.0)]
    GARDEN = [(date(2025, 12, 1), 10.0), (date(2026, 1, 1), 12.0), (date(2026, 2, 1), 19.0)]

    def test_household_is_total_minus_garden(self):
        h = water.household(self.TOTAL, self.GARDEN, date(2026, 1, 1), date(2026, 2, 1))
        self.assertEqual((h["value"], h["estimated"], h["partial"]), (8.0, False, False))   # 15 total - 7 garden

    def test_boundary_between_readings_is_interpolated_and_flagged(self):
        t = water.usage(self.TOTAL, date(2025, 12, 16), date(2026, 1, 1))
        self.assertEqual((t["value"], t["estimated"]), (5.161, True))

    def test_periods_are_clipped_to_the_readings_never_extrapolated(self):
        t = water.usage(self.TOTAL, date(2026, 1, 1), date(2026, 3, 1))
        self.assertEqual((t["value"], t["to"], t["partial"]), (15.0, "2026-02-01", True))
        self.assertIsNone(water.usage(self.TOTAL, date(2026, 3, 1), date(2026, 4, 1)))
        self.assertIsNone(water.usage(self.TOTAL[:1], date(2025, 1, 1), date(2027, 1, 1)))   # one reading is no usage

    def test_household_needs_both_meters(self):
        self.assertIsNone(water.household(self.TOTAL, [], date(2026, 1, 1), date(2026, 2, 1)))

    def test_summary_has_months_years_and_warns_when_garden_exceeds_total(self):
        rows = [{"meter": "water_total", "read_on": "2026-01-01", "value": 10.0, "note": ""}, {"meter": "water_total", "read_on": "2026-02-01", "value": 12.0, "note": ""},
                {"meter": "water_garden", "read_on": "2026-01-01", "value": 1.0, "note": ""}, {"meter": "water_garden", "read_on": "2026-02-01", "value": 6.0, "note": ""}]
        summary = water.summarize(rows, date(2026, 2, 10))
        self.assertEqual([m["label"] for m in summary["months"]], ["2026-01"])
        self.assertEqual(summary["years"][0]["total"]["value"], 2.0)
        self.assertTrue(summary["warnings"])


class WaterTrendTests(unittest.TestCase):
    def rows(self, total, garden):
        out = [{"meter": "water_total", "read_on": d, "value": v, "note": ""} for d, v in total]
        return out + [{"meter": "water_garden", "read_on": d, "value": v, "note": ""} for d, v in garden]

    def test_per_day_average_between_readings_household_is_total_minus_garden(self):
        rows = self.rows([("2026-01-01", 100), ("2026-01-11", 103), ("2026-01-21", 109)], [("2026-01-01", 10), ("2026-01-11", 11), ("2026-01-21", 13)])
        iv = water.summarize(rows, date(2026, 2, 1))["intervals"]
        self.assertEqual(iv["basis"], "household")
        self.assertEqual([i["household"]["litres_per_day"] for i in iv["items"]], [200.0, 400.0])   # (3-1) m3 / 10 d, then (6-2) m3 / 10 d
        self.assertEqual(iv["trend"]["vs_previous"], 1.0)            # doubled
        self.assertEqual(iv["trend"]["vs_baseline"], 1.0)

    def test_no_trend_until_two_periods(self):
        rows = self.rows([("2026-01-01", 100), ("2026-01-11", 103)], [("2026-01-01", 10), ("2026-01-11", 11)])
        iv = water.summarize(rows, date(2026, 2, 1))["intervals"]
        self.assertEqual(len(iv["items"]), 1)
        self.assertIsNone(iv["trend"])

    def test_readings_on_different_days_use_only_days_both_meters_were_read(self):
        rows = self.rows([("2026-01-01", 100), ("2026-01-08", 102), ("2026-01-15", 105)], [("2026-01-01", 10), ("2026-01-15", 12)])
        iv = water.summarize(rows, date(2026, 2, 1))["intervals"]
        self.assertEqual([(i["from"], i["to"], i["household"]["m3"]) for i in iv["items"]], [("2026-01-01", "2026-01-15", 3.0)])

    def test_without_a_garden_meter_the_trend_is_the_total_meter(self):
        rows = self.rows([("2026-01-01", 100), ("2026-01-11", 103), ("2026-01-21", 106)], [])
        iv = water.summarize(rows, date(2026, 2, 1))["intervals"]
        self.assertEqual((iv["basis"], iv["trend"]["key"], iv["trend"]["vs_previous"]), ("total", "total", 0.0))


class WaterRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "w.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)

    def tearDown(self):
        self.temp.cleanup()

    def test_empty_until_a_reading_exists(self):
        self.assertEqual(routes.read(self.ctx, None)[1]["reason"], "no_readings")

    def test_batch_saves_both_meters_and_derives_usage(self):
        _, view = routes.save(self.ctx, post([
            {"read_on": "2025-01-01", "total": "812,5", "garden": 40}, {"read_on": "2025-02-01", "total": 830.5, "garden": 44}, {"read_on": "2025-03-01", "total": 845}]))
        self.assertEqual(view["state"], "manual")
        feb = next(m for m in view["months"] if m["label"] == "2025-01")
        self.assertEqual((feb["total"]["value"], feb["garden"]["value"], feb["household"]["value"]), (18.0, 4.0, 14.0))
        newest = view["rows"][0]
        self.assertEqual((newest["read_on"], newest["garden"]), ("2025-03-01", None))   # a missing garden reading stays missing, not zero
        self.assertEqual(newest["total"]["since"], {"from": "2025-02-01", "days": 28, "used": 14.5})

    def test_same_day_replaces_and_a_meter_cannot_go_backwards(self):
        routes.save(self.ctx, post([{"read_on": "2025-01-01", "total": 100}, {"read_on": "2025-02-01", "total": 110}]))
        routes.save(self.ctx, post([{"read_on": "2025-02-01", "total": 112}]))
        self.assertEqual(self.store.list_meter_readings("hh-meyer")[-1]["value"], 112.0)
        with self.assertRaises(HTTPError) as raised:
            routes.save(self.ctx, post([{"read_on": "2025-03-01", "total": 90}]))
        self.assertIn("only counts up", raised.exception.message)
        self.assertEqual(len(self.store.list_meter_readings("hh-meyer")), 2)   # nothing from the failed batch was kept

    def test_a_bad_row_rejects_the_whole_batch(self):
        for bad in ({"read_on": "2025-13-01", "total": 1}, {"read_on": "2999-01-01", "total": 1}, {"read_on": "2025-01-01"}, {"read_on": "2025-01-01", "total": "abc"}):
            with self.assertRaises(HTTPError):
                routes.save(self.ctx, post([{"read_on": "2025-01-01", "total": 5}, bad]))
        self.assertEqual(self.store.list_meter_readings("hh-meyer"), [])

    def test_delete_a_day(self):
        routes.save(self.ctx, post([{"read_on": "2025-01-01", "total": 1, "garden": 1}, {"read_on": "2025-02-01", "total": 2}]))
        _, view = routes.remove(self.ctx, Request("DELETE", "/x", {}, "", b"", {"day": "2025-01-01"}))
        self.assertEqual([r["read_on"] for r in view["rows"]], ["2025-02-01"])
        with self.assertRaises(HTTPError):
            routes.remove(self.ctx, Request("DELETE", "/x", {}, "", b"", {"day": "2025-01-01"}))


if __name__ == "__main__":
    unittest.main()

from datetime import date, datetime, timedelta
from pathlib import Path
import json
import tempfile
import unittest
from zoneinfo import ZoneInfo

from chit_server.loader import load_file_module
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
meds = load_file_module(Path(__file__).parents[3] / "shared" / "meds.py")


def req(body=None, params=None, query=None):
    return Request("POST", "/x", query or {}, "application/json", json.dumps(body or {}).encode(), params=params or {})


class SupplyTests(unittest.TestCase):
    def test_days_left_follow_the_schedule(self):
        self.assertEqual(meds.days_left(14, []), 14)              # every day
        self.assertEqual(meds.days_left(5, [0, 1, 2, 3, 4]), 7)   # weekdays only: 5 doses last a week
        self.assertIsNone(meds.days_left(None, []))


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "h.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)

    def tearDown(self):
        self.temp.cleanup()

    def meds(self):
        return {m["name"]: m for m in routes.overview(self.ctx, Request("GET", "/x", {}, ""))[1]["meds"]}

    def test_seeded_reminders_and_refill_warning(self):
        meds_ = self.meds()
        self.assertEqual(meds_["Vitamin D"]["time"], "07:30")
        self.assertFalse(meds_["Vitamin D"]["refill_soon"])
        self.assertTrue(meds_["Allergy tablet"]["refill_soon"])                    # 5 doses left on weekdays = 7 days
        self.assertEqual(meds_["Allergy tablet"]["remind_member_id"], "jonas")

    def test_giving_a_dose_uses_supply_and_undoing_returns_it(self):
        before = self.meds()["Vitamin D"]["supply"]
        med = self.meds()["Vitamin D"]["id"]
        routes.log(self.ctx, req({"status": "given"}, {"id": med}))
        self.assertEqual(self.meds()["Vitamin D"]["supply"], before - 1)
        routes.log(self.ctx, req({"status": "given"}, {"id": med}))                 # same again: no second unit used
        self.assertEqual(self.meds()["Vitamin D"]["supply"], before - 1)
        routes.log(self.ctx, req({"status": "missed"}, {"id": med}))
        self.assertEqual(self.meds()["Vitamin D"]["supply"], before)
        self.assertEqual(self.meds()["Vitamin D"]["today"]["status"], "missed")
        routes.log(self.ctx, req({"status": None}, {"id": med}))
        self.assertIsNone(self.meds()["Vitamin D"]["today"]["status"])

    def test_validation(self):
        base = {"member_id": "mila", "name": "Iron", "time": "08:00", "weekdays": [], "supply": 10}
        for change in ({"time": "8am"}, {"member_id": "nina"}, {"remind_member_id": "leo"}, {"weekdays": [9]}, {"supply": -1}, {"name": " "}):
            with self.assertRaises(HTTPError):
                routes.add(self.ctx, req({**base, **change}))
        with self.assertRaises(HTTPError):
            routes.log(self.ctx, req({"status": "given", "date": (date.today() - timedelta(days=30)).isoformat()}, {"id": self.meds()["Vitamin D"]["id"]}))

    def test_the_week_marks_days_that_are_not_due(self):
        week = self.meds()["Allergy tablet"]["week"]
        self.assertEqual([d["due"] for d in week], [True] * 5 + [False] * 2)


if __name__ == "__main__":
    unittest.main()

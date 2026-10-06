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


class WindowRouteTests(unittest.TestCase):
    NOW = datetime(2026, 10, 6, 10, 20)

    def prices(self):
        by_hour = {("2026-10-06", h): (0.12 if h in (13, 14) else 0.30) for h in range(24)}
        by_hour.update({("2026-10-07", h): (0.10 if h in (3, 4) else 0.28) for h in range(24)})
        return {"currency": "EUR", "by_hour": by_hour, "levels": {}}

    def test_two_windows_across_today_and_tomorrow(self):
        result = routes.build(self.prices(), None, self.NOW, 2)
        self.assertEqual([(w["day"], w["start"][11:16]) for w in result["windows"]], [("tomorrow", "03:00"), ("today", "13:00")])
        self.assertTrue(all(w["worth_moving"] for w in result["windows"]))

    def test_flat_prices_say_it_is_not_worth_moving(self):
        flat = {"currency": "EUR", "by_hour": {("2026-10-06", h): 0.25 for h in range(24)}, "levels": {}}
        result = routes.build(flat, None, self.NOW, 2)
        self.assertTrue(result["windows"])
        self.assertFalse(any(w["worth_moving"] for w in result["windows"]))

    def test_solar_estimate_is_reported_per_window(self):
        solar = {("2026-10-06", h): (3.0 if h in (11, 12) else 0.0) for h in range(24)}
        top = routes.build(self.prices(), solar, self.NOW, 2)["windows"]
        self.assertTrue(any(w["solar_kw"] == 3.0 for w in top))


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "w.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)

    def tearDown(self):
        self.temp.cleanup()

    def test_needs_tibber(self):
        self.assertEqual(routes.best(self.ctx, Request("GET", "/x", {}, ""))[1]["reason"], "no_tibber_token")

    def test_hours_are_validated(self):
        with self.assertRaises(HTTPError):
            routes.best(self.ctx, Request("GET", "/x", {"hours": "9"}, ""))

    def test_price_only_basis_without_solaredge(self):
        self.store.set_energy_connection("hh-meyer", "tibber", "t" * 30, {"home_id": "h"})
        now = routes.household.latest(self.ctx)[2]
        today = now.date().isoformat()
        prices = {"currency": "EUR", "by_hour": {(today, h): 0.2 + (h % 5) / 100 for h in range(24)}, "levels": {}}
        with patch.object(routes.tibber, "prices", return_value=(prices, "t", False)):
            _, payload = routes.best(self.ctx, Request("GET", "/x", {}, ""))
        self.assertEqual((payload["state"], payload["basis"]), ("available", "price"))


if __name__ == "__main__":
    unittest.main()

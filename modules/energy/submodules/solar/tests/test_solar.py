from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chit_server.loader import load_file_module
from chit_server.router import Context
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")


class SolarTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "s.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)

    def tearDown(self):
        self.temp.cleanup()

    def connect(self, peak=6.6):
        self.store.set_energy_connection("hh-meyer", "solaredge", "K" * 32, {"site_id": "4711", "site_name": "Roof", "peak_kw": peak})

    def test_unconfigured_without_a_connection(self):
        self.assertEqual(routes.day_view(self.ctx, None)[1]["reason"], "no_solaredge")

    def test_measured_past_and_expected_future_never_mix(self):
        self.connect()
        summary = {"current_kw": 3.2, "today_kwh": 14.5, "month_kwh": 300.0, "lifetime_kwh": 9000.0, "last_update": "x"}
        now_hour = routes.household.latest(self.ctx)[2].hour
        measured = {h: 1.0 for h in range(24)}
        with patch.object(routes.solaredge, "overview", return_value=(summary, "t", False)), \
                patch.object(routes.solaredge, "hourly_production", return_value=(measured, "t", False)), \
                patch.object(routes.forecast, "expected_kw", return_value=({(routes.household.latest(self.ctx)[2].date().isoformat(), h): 2.0 for h in range(24)}, "t", False)):
            _, payload = routes.day_view(self.ctx, None)
        self.assertEqual((payload["state"], payload["expected_state"], payload["today_kwh"]), ("available", "forecast", 14.5))
        for hour in payload["hours"]:
            if hour["hour"] < now_hour:
                self.assertEqual((hour["kwh"], hour["expected_kwh"]), (1.0, None))
            if hour["hour"] > now_hour:
                self.assertEqual((hour["kwh"], hour["expected_kwh"]), (None, 2.0))

    def test_rejected_key_and_outage(self):
        self.connect()
        with patch.object(routes.solaredge, "overview", side_effect=routes.net.ProviderError("auth", "x")):
            self.assertEqual(routes.day_view(self.ctx, None)[1]["reason"], "key_rejected")
        with patch.object(routes.solaredge, "overview", side_effect=routes.net.ProviderError("rate_limited", "x")):
            self.assertEqual(routes.day_view(self.ctx, None)[1]["reason"], "rate_limited")

    def test_forecast_needs_peak_power_and_location(self):
        self.connect(peak=None)
        summary = {"current_kw": 0.0, "today_kwh": 1.0, "month_kwh": None, "lifetime_kwh": None, "last_update": None}
        with patch.object(routes.solaredge, "overview", return_value=(summary, "t", False)), \
                patch.object(routes.solaredge, "hourly_production", return_value=({}, "t", False)):
            _, payload = routes.day_view(self.ctx, None)
        self.assertEqual(payload["expected_state"], "unconfigured")


if __name__ == "__main__":
    unittest.main()

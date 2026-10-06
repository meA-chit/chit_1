from io import BytesIO
from pathlib import Path
import json
import unittest
from unittest.mock import patch

from chit_server.loader import load_file_module

weather = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")

API_BODY = json.dumps({
    "current": {"time": "2026-10-06T12:00", "temperature_2m": 14.2, "weather_code": 2},
    "daily": {"temperature_2m_max": [17.4], "temperature_2m_min": [8.1], "precipitation_probability_max": [20]},
}).encode()


class Response(BytesIO):
    status = 200


class FakeStore:
    def __init__(self, place):
        self.place = place

    def latest_household_id(self):
        return "h"

    def get_household_document(self, _):
        return {"household": self.place}


class Ctx:
    def __init__(self, place):
        self.store = FakeStore(place)
        self.logged = []

    def log(self, message):
        self.logged.append(message)


class WeatherTests(unittest.TestCase):
    def setUp(self):
        weather._cache.clear()

    def test_unconfigured_without_coordinates(self):
        _, payload = weather.now(Ctx({"latitude": None, "longitude": None}), None)
        self.assertEqual((payload["state"], payload["reason"]), ("unconfigured", "no_location"))

    def test_reads_provider_and_maps_codes(self):
        with patch.object(weather, "urlopen", return_value=Response(API_BODY)) as opened:
            _, payload = weather.now(Ctx({"latitude": 48.1, "longitude": 11.6}), None)
        self.assertEqual((payload["state"], payload["temperature"], payload["condition"], payload["icon"]),
                         ("available", 14, "Partly cloudy", "partly"))
        self.assertEqual((payload["high"], payload["low"], payload["rain_pct"]), (17, 8, 20))
        self.assertEqual(payload["source"], "Open-Meteo")
        self.assertIn("api.open-meteo.com", opened.call_args[0][0].full_url)

    def test_second_call_uses_the_cache(self):
        place = {"latitude": 48.1, "longitude": 11.6}
        with patch.object(weather, "urlopen", return_value=Response(API_BODY)) as opened:
            weather.now(Ctx(place), None)
            weather.now(Ctx(place), None)
        self.assertEqual(opened.call_count, 1)

    def test_failure_is_unavailable_then_stale_never_invented(self):
        place = {"latitude": 48.1, "longitude": 11.6}
        with patch.object(weather, "urlopen", side_effect=OSError("down")):
            _, payload = weather.now(Ctx(place), None)
        self.assertEqual(payload["state"], "unavailable")
        with patch.object(weather, "urlopen", return_value=Response(API_BODY)):
            weather.now(Ctx(place), None)
        weather._cache[(48.1, 11.6)] = (-10_000, weather._cache[(48.1, 11.6)][1])  # expire
        with patch.object(weather, "urlopen", side_effect=OSError("down")):
            _, payload = weather.now(Ctx(place), None)
        self.assertEqual((payload["state"], payload["temperature"]), ("stale", 14))


if __name__ == "__main__":
    unittest.main()

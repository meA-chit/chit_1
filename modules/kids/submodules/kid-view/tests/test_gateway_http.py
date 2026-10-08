"""The phone gateway over real HTTP: the in-process read of the planner's public API works behind it, nothing else of the hub is reachable."""
from datetime import date
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from chit_server import gateway
from chit_server.app import build_router
from chit_server.registry import load_manifests
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

HH, KID = "hh-meyer", "mila"


class GatewayHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        EncryptedHouseholdStore._failures.clear()
        cls.temp = tempfile.TemporaryDirectory()
        cls.store = EncryptedHouseholdStore(Path(cls.temp.name) / "g.db", plain=True)
        seed_all(cls.store)
        full = build_router(load_manifests())
        today = date.today().isoformat()
        cls.agenda_calls = 0

        def fake_agenda(ctx, request):                      # the owner's public read API, without the network
            cls.agenda_calls += 1
            return 200, {"state": "available", "events": [{"title": "Swim meet", "start": today + "T16:30:00+02:00", "end": today + "T17:30:00+02:00", "all_day": False,
                                                           "category": "sport_activity", "source": "Club", "members": ["Mila"], "member_ids": [KID]}]}
        full.routes[("GET", "/api/planner/calendar/agenda")] = fake_agenda
        cls.store.set_phone_settings(HH, KID, True)
        pairing = cls.store.create_phone_pairing(HH, KID)
        cls.token = cls.store.complete_phone_pairing(pairing["secret"], pairing["code"])["token"]
        cls.server = gateway.make_gateway(cls.store, load_manifests(), full, host="127.0.0.1", port=0)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp.cleanup()

    def get(self, path, token=None):
        request = urllib.request.Request(self.base + path, headers={"Authorization": "Bearer " + token} if token else {})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, response.read(), dict(response.headers)
        except urllib.error.HTTPError as error:
            return error.code, error.read(), dict(error.headers)

    def test_the_calendar_reaches_the_phone_through_the_gateway(self):
        status, body, headers = self.get("/api/kids/phone/device/view", self.token)
        self.assertEqual(status, 200)
        view = json.loads(body)
        self.assertEqual([e["title"] for e in view["activities"]["events"]], ["Swim meet"])
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])

    def test_the_planner_api_itself_is_not_reachable_from_the_network(self):
        for path in ("/api/planner/calendar/agenda", "/api/kids/phone/settings", "/api/kids/bag?member=mila", "/api/household/current", "/api/shell"):
            self.assertEqual(self.get(path)[0], 404, path)
            self.assertEqual(self.get(path, self.token)[0], 404, path)          # a device token does not unlock them either

    def test_app_files_allow_tablets_and_zoom(self):
        status, html, _ = self.get("/")
        self.assertEqual(status, 200)
        self.assertNotIn(b"user-scalable", html)                                  # K8: pinch zoom must work
        self.assertNotIn(b"maximum-scale", html)
        manifest = json.loads(self.get("/manifest.webmanifest")[1])
        self.assertNotIn("orientation", manifest)                                 # K8: no portrait lock
        self.assertEqual(self.get("/README.md")[0], 404)                          # only the allow-listed files are served


if __name__ == "__main__":
    unittest.main()

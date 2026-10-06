from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chit_server.loader import load_file_module
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
TOKEN = "tibber-secret-token-0123456789"


def put(body):
    import json
    return Request("PUT", "/x", {}, "application/json", json.dumps(body).encode())


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "e.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)

    def tearDown(self):
        self.temp.cleanup()

    def test_nothing_is_connected_by_default(self):
        _, payload = routes.status(self.ctx, None)
        self.assertEqual((payload["tibber"]["connected"], payload["solaredge"]["connected"]), (False, False))

    def test_tibber_token_is_verified_stored_and_never_returned(self):
        with patch.object(routes.tibber, "verify", return_value={"home_id": "h1", "homes": 1}):
            _, payload = routes.connect_tibber(self.ctx, put({"token": TOKEN}))
        self.assertTrue(payload["tibber"]["connected"])
        self.assertEqual(payload["tibber"]["hint"], TOKEN[-4:])
        self.assertNotIn(TOKEN, repr(routes.status(self.ctx, None)))          # status never carries the secret
        self.assertEqual(self.store.get_energy_connection("hh-meyer", "tibber")["secret"], TOKEN)   # but the hub can read it

    def test_rejected_or_unreachable_keys_are_not_stored(self):
        for kind, status in (("auth", 400), ("unavailable", 502), ("rate_limited", 502)):
            with patch.object(routes.tibber, "verify", side_effect=routes.net.ProviderError(kind, "x")):
                with self.assertRaises(HTTPError) as raised:
                    routes.connect_tibber(self.ctx, put({"token": TOKEN}))
            self.assertEqual(raised.exception.status, status)
        self.assertIsNone(self.store.get_energy_connection("hh-meyer", "tibber"))

    def test_solaredge_needs_a_numeric_site_and_stores_plant_details(self):
        with self.assertRaises(HTTPError):
            routes.connect_solaredge(self.ctx, put({"site_id": "abc", "api_key": "K" * 32}))
        with patch.object(routes.solaredge, "verify", return_value={"name": "Roof", "peak_kw": 6.6, "status": "Active"}):
            _, payload = routes.connect_solaredge(self.ctx, put({"site_id": "4711", "api_key": "K" * 32}))
        self.assertEqual((payload["solaredge"]["site_id"], payload["solaredge"]["peak_kw"]), ("4711", 6.6))

    def test_disconnect_removes_the_secret(self):
        self.store.set_energy_connection("hh-meyer", "tibber", TOKEN, {})
        routes.disconnect(self.ctx, Request("DELETE", "/x", {}, "", params={"provider": "tibber"}))
        self.assertIsNone(self.store.get_energy_connection("hh-meyer", "tibber"))
        with self.assertRaises(HTTPError):
            routes.disconnect(self.ctx, Request("DELETE", "/x", {}, "", params={"provider": "nope"}))

    def test_secrets_never_reach_exports_or_the_household_document(self):
        from chit_store.cli import export_household
        self.store.set_energy_connection("hh-meyer", "tibber", TOKEN, {"home_id": "h1"})
        self.assertNotIn(TOKEN, repr(self.store.get_household_document("hh-meyer")))
        self.assertNotIn(TOKEN, repr(export_household(self.store, "hh-meyer")))


if __name__ == "__main__":
    unittest.main()

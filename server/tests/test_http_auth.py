from http.server import ThreadingHTTPServer
from http.client import HTTPConnection
from pathlib import Path
import json
import tempfile
from threading import Thread
import unittest

from chit_store import EncryptedHouseholdStore
from run import ChitHandler


TEST_KEY = "9b" * 32


class PublicAccessHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        store = EncryptedHouseholdStore(Path(self.temp_dir.name) / "http.db", TEST_KEY)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ChitHandler)
        self.server.store = store
        self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=2)
        self.temp_dir.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection(self.host, self.port, timeout=3)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = (response.status, response.getheaders(), response.read())
        connection.close()
        return result

    def test_setup_pages_and_household_api_are_public(self):
        status, _, _ = self.request("GET", "/dashboard/calendar-home.html")
        self.assertEqual(status, 200)

        status, _, _ = self.request("GET", "/dashboard/home.html")
        self.assertEqual(status, 200)

        payload = {
            "household": {"name": "Public household", "timezone": "Europe/Berlin"},
            "owner_client_id": "adult-1",
            "members": [{"client_id": "adult-1", "role": "adult", "name": "Owner", "profile": {}}],
            "calendars": [],
        }
        status, _, _ = self.request(
            "POST", "/api/households/setup",
            json.dumps(payload),
            {"Content-Type": "application/json"},
        )
        self.assertEqual(status, 201)

        status, _, _ = self.request("GET", "/api/home/summary")
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()

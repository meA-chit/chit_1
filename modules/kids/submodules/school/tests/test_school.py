from pathlib import Path
import json
import tempfile
import unittest

from chit_server.loader import load_file_module
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")


def req(method, body=None, params=None, query=None):
    return Request(method, "/x", query or {}, "application/json" if body is not None else "", json.dumps(body or {}).encode(), params=params or {})


class SchoolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "s.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)

    def tearDown(self):
        self.temp.cleanup()

    def day(self, weekday):
        return routes.plan(self.ctx, req("GET", query={"member": "mila", "weekday": str(weekday)}))[1]["slots"]

    def test_seeded_day_has_recess_and_is_copied_to_school_days(self):
        monday = self.day(0)
        self.assertEqual([s["title"] for s in monday if s["kind"] == "break"], ["Recess", "Short break"])
        self.assertEqual([s["title"] for s in self.day(3)], [s["title"] for s in monday])      # Thursday copied
        self.assertEqual(self.day(5), [])                                                       # weekend stays empty
        self.assertEqual(monday, sorted(monday, key=lambda s: s["start"]))

    def test_slot_validation(self):
        bad = ({"start": "9:00", "end": "10:00"}, {"start": "10:00", "end": "09:00"}, {"kind": "party"}, {"weekday": 7}, {"title": " "}, {"member_id": "nina"})
        for change in bad:
            body = {"member_id": "mila", "weekday": 5, "start": "10:00", "end": "11:00", "title": "Extra", "kind": "lesson", **change}
            with self.assertRaises(HTTPError):
                routes.add_slot(self.ctx, req("POST", body))

    def test_edit_remove_and_copy(self):
        _, created = routes.add_slot(self.ctx, req("POST", {"member_id": "mila", "weekday": 5, "start": "10:00", "end": "11:00", "title": "Make-up lesson", "kind": "lesson"}))
        routes.update_slot(self.ctx, req("PUT", {"start": "10:30", "end": "11:30", "title": "Make-up lesson", "kind": "lesson"}, {"id": created["id"]}))
        self.assertEqual(self.day(5)[0]["start"], "10:30")
        routes.copy_day(self.ctx, req("POST", {"member_id": "mila", "from_weekday": 5, "to_weekdays": [6]}))
        self.assertEqual(len(self.day(6)), 1)
        routes.remove_slot(self.ctx, req("DELETE", params={"id": created["id"]}))
        self.assertEqual(self.day(5), [])


if __name__ == "__main__":
    unittest.main()

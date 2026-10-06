from http.client import HTTPConnection
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest

from chit_server.app import make_server
from chit_store import EncryptedHouseholdStore

TEST_KEY = "9b" * 32


class HubHTTPTests(unittest.TestCase):
    """ADR-0007: the pilot hub is public on loopback. These tests pin that behaviour."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        store = EncryptedHouseholdStore(Path(self.temp_dir.name) / "http.db", TEST_KEY)
        self.server = make_server(store, "127.0.0.1", 0)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def seed(self):
        return json.loads((Path(__file__).parents[3] / "seed" / "households" / "meyer-family.json").read_text())

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection(self.host, self.port, timeout=3)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = (response.status, response.read())
        connection.close()
        return result

    def test_health_and_household_flow_are_public(self):
        self.assertEqual(self.request("GET", "/api/health")[0], 200)
        status, body = self.request("GET", "/api/household/summary")
        self.assertEqual(json.loads(body), {"state": "unconfigured"})
        payload = {
            "household": {"name": "Public household", "timezone": "Europe/Berlin"},
            "owner_client_id": "adult-1",
            "members": [{"client_id": "adult-1", "role": "adult", "name": "Owner", "profile": {}}],
            "calendars": [],
        }
        status, _ = self.request("POST", "/api/household/setup", json.dumps(payload),
                                 {"Content-Type": "application/json"})
        self.assertEqual(status, 201)
        status, body = self.request("GET", "/api/household/summary")
        self.assertEqual(json.loads(body)["state"], "configured")

    def test_agenda_reports_unconfigured_not_empty_free(self):
        status, body = self.request("GET", "/api/planner/calendar/agenda")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual((data["state"], data["reason"]), ("unavailable", "unconfigured"))

    def test_post_requires_json(self):
        status, _ = self.request("POST", "/api/household/setup", "x=1",
                                 {"Content-Type": "text/plain"})
        self.assertEqual(status, 415)

    def test_unknown_api_and_wrong_method(self):
        self.assertEqual(self.request("GET", "/api/nope")[0], 404)
        self.assertEqual(self.request("POST", "/api/health", "{}", {"Content-Type": "application/json"})[0], 405)

    def test_shell_with_no_household_only_offers_setup(self):
        shell = json.loads(self.request("GET", "/api/shell?surface=web")[1])
        self.assertIsNone(shell["household"])
        self.assertEqual({m["id"] for m in shell["modules"]}, {"household"})
        self.assertEqual(shell["cards"], [])

    def test_edit_flow_and_enablement_drive_the_shell(self):
        seed = self.seed()
        status, body = self.request("POST", "/api/household/setup", json.dumps(seed), {"Content-Type": "application/json"})
        self.assertEqual(status, 201)
        household_id = json.loads(body)["household_id"]
        current = json.loads(self.request("GET", "/api/household/current")[1])
        self.assertEqual(current["document"]["id"], household_id)

        shell = json.loads(self.request("GET", "/api/shell?surface=web")[1])
        self.assertEqual(shell["household"]["name"], "Meyer family")
        self.assertIn("calendar-agenda", {c["id"] for c in shell["cards"]})

        # edit: switch planner off for the household, rename it
        document = current["document"]
        document["household"]["name"] = "Meyer-Schmidt family"
        document["modules"] = ["household"]
        for member in document["members"]:
            member["modules"] = None
        status, _ = self.request("PUT", "/api/household/" + household_id, json.dumps(document), {"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        shell = json.loads(self.request("GET", "/api/shell?surface=web")[1])
        self.assertEqual(shell["household"]["name"], "Meyer-Schmidt family")
        self.assertNotIn("calendar-agenda", {c["id"] for c in shell["cards"]})

        self.assertEqual(self.request("PUT", "/api/household/does-not-exist", json.dumps(document),
                                      {"Content-Type": "application/json"})[0], 404)

    def test_module_selection_is_validated(self):
        seed = self.seed()
        headers = {"Content-Type": "application/json"}
        bad = dict(seed, modules=["household", "nonsense"])
        self.assertEqual(self.request("POST", "/api/household/setup", json.dumps(bad), headers)[0], 400)
        no_dep = dict(seed, modules=["household", "kids"])  # kids needs planner
        self.assertEqual(self.request("POST", "/api/household/setup", json.dumps(no_dep), headers)[0], 400)

    def test_member_view_narrows_the_shell(self):
        seed = self.seed()
        self.request("POST", "/api/household/setup", json.dumps(seed), {"Content-Type": "application/json"})
        shell = json.loads(self.request("GET", "/api/shell?surface=web&member=" + json.loads(
            self.request("GET", "/api/household/current")[1])["document"]["members"][2]["client_id"])[1])
        self.assertEqual(shell["member"]["name"], "Mila")
        self.assertEqual({m["id"] for m in shell["modules"]}, {"planner", "kids"})
        self.assertEqual(self.request("GET", "/api/shell?surface=web&member=nobody")[0], 400)

    def test_planner_endpoints_follow_the_latest_household(self):
        headers = {"Content-Type": "application/json"}
        self.assertEqual(json.loads(self.request("GET", "/api/planner/timeline/today")[1])["state"], "unconfigured")
        self.assertEqual(json.loads(self.request("GET", "/api/planner/chores/today")[1])["state"], "unconfigured")
        self.request("POST", "/api/household/setup", json.dumps(self.seed()), headers)

        timeline = json.loads(self.request("GET", "/api/planner/timeline/today")[1])
        self.assertEqual(timeline["state"], "manual")   # typed-in routines, never labelled measured
        self.assertEqual([lane["name"] for lane in timeline["lanes"]], ["Nina Meyer", "Jonas Meyer", "Mila", "Leo"])
        self.assertTrue(all(lane["avatar"] and lane["color"] for lane in timeline["lanes"]))

        status, body = self.request("POST", "/api/planner/chores", json.dumps({"title": "Feed the fish", "weekdays": []}), headers)
        self.assertEqual(status, 201)
        chore_id = json.loads(body)["id"]
        chores = json.loads(self.request("GET", "/api/planner/chores/today")[1])
        mine = next(c for c in chores["chores"] if c["id"] == chore_id)
        self.assertEqual((mine["done"], mine["streak"]), (False, 0))
        status, _ = self.request("POST", "/api/planner/chores/%s/toggle" % chore_id, json.dumps({"done": True}), headers)
        self.assertEqual(status, 200)
        chores = json.loads(self.request("GET", "/api/planner/chores/today")[1])
        mine = next(c for c in chores["chores"] if c["id"] == chore_id)
        self.assertEqual((mine["done"], mine["streak"]), (True, 1))
        self.assertEqual(self.request("POST", "/api/planner/chores/nope/toggle", json.dumps({"done": True}), headers)[0], 404)
        self.assertEqual(self.request("POST", "/api/planner/chores/%s/toggle" % chore_id, json.dumps({"done": "yes"}), headers)[0], 400)
        self.assertEqual(self.request("POST", "/api/planner/chores", json.dumps({"title": " "}), headers)[0], 400)

    def test_chore_and_reminder_settings_crud(self):
        headers = {"Content-Type": "application/json"}
        self.request("POST", "/api/household/setup", json.dumps(self.seed()), headers)
        options = json.loads(self.request("GET", "/api/planner/chores/options")[1])
        self.assertEqual([(p["id"], p["start"], p["end"]) for p in options["day_parts"]],
                         [("morning", "06:00", "10:00"), ("day", "10:00", "16:00"), ("evening", "16:00", "20:00")])
        nina = json.loads(self.request("GET", "/api/shell?surface=web")[1])["members"][0]["id"]

        status, body = self.request("POST", "/api/planner/chores", json.dumps(
            {"title": "Water the herbs", "assignee_id": nina, "weekdays": ["monday", "thursday"], "day_part": "morning"}), headers)
        self.assertEqual(status, 201)
        chore_id = json.loads(body)["id"]
        listed = json.loads(self.request("GET", "/api/planner/chores")[1])["chores"]
        mine = next(c for c in listed if c["id"] == chore_id)
        self.assertEqual((mine["weekdays"], mine["day_part"], mine["assignee_id"]), (["monday", "thursday"], "morning", nina))
        status, _ = self.request("PUT", "/api/planner/chores/" + chore_id, json.dumps(
            {"title": "Water the herbs", "assignee_id": None, "weekdays": [], "day_part": "evening"}), headers)
        self.assertEqual(status, 200)
        for bad in ({"title": "x", "day_part": "midnight"}, {"title": "x", "weekdays": ["funday"]}, {"title": ""}):
            self.assertEqual(self.request("PUT", "/api/planner/chores/" + chore_id, json.dumps(bad), headers)[0], 400)
        self.assertEqual(self.request("DELETE", "/api/planner/chores/" + chore_id)[0], 200)
        self.assertEqual(self.request("DELETE", "/api/planner/chores/" + chore_id)[0], 404)

        status, body = self.request("POST", "/api/planner/reminders", json.dumps(
            {"title": "Book flights", "member_id": nina, "weekdays": [], "day_part": "evening"}), headers)
        self.assertEqual(status, 201)
        rid = json.loads(body)["id"]
        today = json.loads(self.request("GET", "/api/planner/reminders/today")[1])
        self.assertIn("Book flights", [r["title"] for r in today["reminders"]])
        timeline = json.loads(self.request("GET", "/api/planner/timeline/today")[1])
        self.assertIn(("Book flights", nina, "evening"), [(r["title"], r["member_id"], r["day_part"]) for r in timeline["reminders"]])
        self.assertEqual([z["id"] for z in timeline["zones"]], ["morning", "day", "evening", "relax"])
        self.assertEqual((timeline["zones"][0]["start"], timeline["zones"][0]["end"]), ("06:00", "10:00"))
        self.assertEqual(self.request("POST", "/api/planner/reminders", json.dumps(
            {"title": "x", "on_date": "2030-01-01", "weekdays": ["monday"]}), headers)[0], 400)
        self.assertEqual(self.request("DELETE", "/api/planner/reminders/" + rid)[0], 200)

    def test_skip_for_today_and_undo(self):
        headers = {"Content-Type": "application/json"}
        self.request("POST", "/api/household/setup", json.dumps(self.seed()), headers)
        body = json.dumps({"title": "Water herbs", "weekdays": []})
        chore_id = json.loads(self.request("POST", "/api/planner/chores", body, headers)[1])["id"]
        rid = json.loads(self.request("POST", "/api/planner/reminders", json.dumps({"title": "Call mum", "on_date": __import__("datetime").date.today().isoformat(), "day_part": "day"}), headers)[1])["id"]

        def today():
            return json.loads(self.request("GET", "/api/planner/chores/today")[1]), json.loads(self.request("GET", "/api/planner/reminders/today")[1])

        chores, reminders = today()
        self.assertIn(chore_id, [c["id"] for c in chores["chores"]])
        self.assertEqual(self.request("POST", "/api/planner/chores/%s/skip" % chore_id, json.dumps({"skipped": True}), headers)[0], 200)
        self.assertEqual(self.request("POST", "/api/planner/reminders/%s/skip" % rid, json.dumps({"skipped": True}), headers)[0], 200)
        chores, reminders = today()
        self.assertNotIn(chore_id, [c["id"] for c in chores["chores"]])
        self.assertIn(chore_id, [c["id"] for c in chores["skipped"]])
        self.assertIn(rid, [r["id"] for r in reminders["skipped"]])
        timeline = json.loads(self.request("GET", "/api/planner/timeline/today")[1])
        self.assertNotIn(rid, [r["id"] for r in timeline["reminders"]])   # skipped reminders leave the timeline too
        self.request("POST", "/api/planner/chores/%s/skip" % chore_id, json.dumps({"skipped": False}), headers)
        self.assertIn(chore_id, [c["id"] for c in today()[0]["chores"]])
        self.assertEqual(self.request("POST", "/api/planner/chores/%s/skip" % chore_id, json.dumps({"skipped": "yes"}), headers)[0], 400)
        self.assertEqual(self.request("POST", "/api/planner/chores/nope/skip", json.dumps({"skipped": True}), headers)[0], 404)

    def test_timeline_for_a_chosen_day(self):
        import datetime
        headers = {"Content-Type": "application/json"}
        self.request("POST", "/api/household/setup", json.dumps(self.seed()), headers)
        today = json.loads(self.request("GET", "/api/planner/timeline/day")[1])
        self.assertTrue(today["is_today"])
        tomorrow_date = (datetime.date.fromisoformat(today["date"]) + datetime.timedelta(days=1)).isoformat()
        tomorrow = json.loads(self.request("GET", "/api/planner/timeline/day?date=" + tomorrow_date)[1])
        self.assertFalse(tomorrow["is_today"])
        self.assertEqual((tomorrow["date"], tomorrow["today"]), (tomorrow_date, today["date"]))
        past = (datetime.date.fromisoformat(today["date"]) - datetime.timedelta(days=1)).isoformat()
        far = (datetime.date.fromisoformat(today["date"]) + datetime.timedelta(days=99)).isoformat()
        for bad in (past, far, "not-a-date"):
            self.assertEqual(self.request("GET", "/api/planner/timeline/day?date=" + bad)[0], 400)

    def test_shell_lists_settings_sections_for_the_household_screen(self):
        self.request("POST", "/api/household/setup", json.dumps(self.seed()), {"Content-Type": "application/json"})
        shell = json.loads(self.request("GET", "/api/shell?surface=web")[1])
        self.assertEqual([(s["id"], s["target"]) for s in shell["settings_sections"]], [("chores", "household"), ("reminders", "household"), ("energy", "household")])
        document = json.loads(self.request("GET", "/api/household/current")[1])["document"]
        document["modules"] = ["household"]
        for member in document["members"]:
            member["modules"] = None
        self.assertEqual(self.request("PUT", "/api/household/" + document["id"], json.dumps(document), {"Content-Type": "application/json"})[0], 200)
        shell = json.loads(self.request("GET", "/api/shell?surface=web")[1])
        self.assertEqual(shell["settings_sections"], [])   # planner and energy switched off: their sections disappear

    def test_shell_exposes_slots_avatars_and_ordered_modules(self):
        self.request("POST", "/api/household/setup", json.dumps(self.seed()), {"Content-Type": "application/json"})
        shell = json.loads(self.request("GET", "/api/shell?surface=web")[1])
        self.assertTrue(all(c["slot"] in {"topbar", "timeline", "left", "center", "right"} for c in shell["cards"]))
        self.assertEqual([c["order"] for c in shell["cards"]], sorted(c["order"] for c in shell["cards"]))
        self.assertEqual({c["group"] for c in shell["cards"] if c["slot"] == "right"}, {"home"})
        self.assertEqual([m["id"] for m in shell["modules"]][:2], ["household", "planner"])
        self.assertEqual(shell["members"][2]["avatar"], "k2")
        mila = shell["members"][2]["id"]  # ids are generated on create; only seed loading preserves them
        kid = json.loads(self.request("GET", "/api/shell?surface=web&member=" + mila)[1])
        self.assertEqual({c["id"] for c in kid["cards"]} & {"energy-now", "climate-now"}, set())  # adult-only modules

    def test_catalog_lists_modules(self):
        catalog = json.loads(self.request("GET", "/api/modules")[1])["modules"]
        self.assertIn("planner", {m["id"] for m in catalog})
        self.assertTrue(next(m for m in catalog if m["id"] == "household")["required"])

    def test_shell_hides_sensitive_modules_on_tv(self):
        self.request("POST", "/api/household/setup", json.dumps(self.seed()), {"Content-Type": "application/json"})
        status, body = self.request("GET", "/api/shell?surface=tv")
        self.assertEqual(status, 200)
        shell = json.loads(body)
        self.assertTrue(shell["screen_safe"])
        ids = {card["id"] for card in shell["cards"]}
        self.assertIn("calendar-agenda", ids)
        self.assertNotIn("todo-today", ids)  # tv surface is not in the card's surfaces
        self.assertEqual(self.request("GET", "/api/shell?surface=bogus")[0], 400)

    def test_shell_web_includes_cards_and_legacy_view(self):
        shell = json.loads(self.request("GET", "/api/shell?surface=web")[1])
        self.assertEqual(shell["cards"], [])  # no household yet: the shell shows onboarding instead
        self.assertEqual([v["id"] for v in shell["views"]], ["household"])

    def test_static_traversal_blocked(self):
        for path in ("/..%2f..%2f..%2fREADME.md", "/../../../README.md", "/assets/..%2f..%2f..%2f..%2fREADME.md"):
            status, body = self.request("GET", path)
            self.assertNotIn(b"Chit is a personal", body)

    def test_unbuilt_client_is_a_clear_503_or_spa(self):
        status, _ = self.request("GET", "/some/route")
        self.assertIn(status, (200, 503))


if __name__ == "__main__":
    unittest.main()

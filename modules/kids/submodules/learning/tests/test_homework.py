from datetime import date, timedelta
import json
from pathlib import Path
import tempfile
import unittest

from chit_server.loader import load_file_module
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
homework = load_file_module(Path(__file__).parents[3] / "shared" / "homework.py")
HH, KID = "hh-meyer", "mila"
TODAY = date.today()


def req(body=None, params=None, query=None):
    return Request("POST", "/x", query or {}, "application/json", json.dumps(body or {}).encode(), params=params or {})


def iso(days):
    return (TODAY + timedelta(days=days)).isoformat()


class HomeworkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "h.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)

    def tearDown(self):
        self.temp.cleanup()

    def overview(self):
        return routes.homework_overview(self.ctx, Request("GET", "/x", {}, ""))[1]

    def titles(self):
        return {t["title"]: t for t in self.overview()["tasks"]}

    def test_seeded_tasks_and_summary(self):
        data = self.overview()
        summary = data["summary"]
        self.assertEqual(summary["due_tomorrow"], 1)       # the Maths worksheet
        self.assertEqual(summary["tests_soon"], 2)         # English in 6 days, Biology in 11
        self.assertEqual(summary["overdue"], 1)            # the Geography map
        self.assertEqual(len(summary["week"]), 5)
        self.assertEqual(data["tasks"][0]["due_on"], min(t["due_on"] for t in data["tasks"]))   # soonest first

    def test_a_parent_adds_edits_ticks_and_removes(self):
        status, body = routes.add_task(self.ctx, req({"member_id": KID, "kind": "test", "subject": "Maths", "title": "Fractions", "due_on": iso(4)}))
        self.assertEqual(status, 201)
        task = self.titles()["Fractions"]
        self.assertEqual((task["by"], task["days"], task["done"]), ("parent", 4, False))
        routes.update_task(self.ctx, req({"kind": "homework", "title": "Fractions, redo page 2", "due_on": iso(5)}, {"id": body["id"]}))
        self.assertEqual(self.titles()["Fractions, redo page 2"]["days"], 5)
        routes.update_task(self.ctx, req({"done": True}, {"id": body["id"]}))
        self.assertTrue(self.titles()["Fractions, redo page 2"]["done"])
        routes.update_task(self.ctx, req({"done": False}, {"id": body["id"]}))
        self.assertFalse(self.titles()["Fractions, redo page 2"]["done"])
        routes.remove_task(self.ctx, req(params={"id": body["id"]}))
        self.assertNotIn("Fractions, redo page 2", self.titles())

    def test_done_tasks_leave_the_open_tiles_and_count_this_week(self):
        task = self.titles()["Worksheet 4: fractions"]
        routes.update_task(self.ctx, req({"done": True}, {"id": task["id"]}))
        summary = self.overview()["summary"]
        self.assertEqual(summary["due_tomorrow"], 0)
        self.assertGreaterEqual(summary["done_this_week"], 1)

    def test_homework_subjects_come_from_the_list_and_are_offered_with_every_type(self):
        subjects = {x["name"]: x for x in self.overview()["subjects"]}
        self.assertEqual(sorted(subjects), ["Biology", "Geography", "German", "Maths", "Sport"])
        self.assertEqual((subjects["Maths"]["kind"], subjects["Biology"]["kind"]), ("core", "minor"))
        for bad in ("Quidditch", "Mathe"):                                                       # typed-in subjects are refused
            with self.assertRaises(HTTPError) as caught:
                routes.add_task(self.ctx, req({"member_id": KID, "kind": "homework", "subject": bad, "title": "x", "due_on": iso(1)}))
            self.assertEqual(caught.exception.status, 400)
        routes.add_task(self.ctx, req({"member_id": KID, "kind": "homework", "subject": subjects["German"]["code"].lower(), "title": "By code", "due_on": iso(1)}))
        self.assertEqual(self.titles()["By code"]["subject"], "German")                           # stored under the subject's name
        routes.add_task(self.ctx, req({"member_id": KID, "kind": "homework", "title": "No subject", "due_on": iso(1)}))
        self.assertIsNone(self.titles()["No subject"]["subject"])

    def test_editing_a_task_keeps_to_the_same_rule(self):
        task = self.titles()["Worksheet 4: fractions"]
        with self.assertRaises(HTTPError):
            routes.update_task(self.ctx, req({"kind": "homework", "subject": "Quidditch", "title": "Worksheet 4", "due_on": iso(1)}, {"id": task["id"]}))
        routes.update_task(self.ctx, req({"kind": "homework", "subject": "Biology", "title": "Worksheet 4", "due_on": iso(1)}, {"id": task["id"]}))
        self.assertEqual(self.titles()["Worksheet 4"]["subject"], "Biology")

    def test_validation(self):
        for body in ({"kind": "essay", "title": "x", "due_on": iso(1)}, {"kind": "test", "title": " ", "due_on": iso(1)},
                     {"kind": "test", "title": "x", "due_on": "tomorrow"}, {"kind": "test", "title": "x", "due_on": iso(900)}):
            with self.assertRaises(HTTPError) as caught:
                routes.add_task(self.ctx, req({"member_id": KID, **body}))
            self.assertEqual(caught.exception.status, 400, body)
        with self.assertRaises(HTTPError) as caught:
            routes.add_task(self.ctx, req({"member_id": "nina", "kind": "test", "title": "x", "due_on": iso(1)}))   # an adult
        self.assertEqual(caught.exception.status, 404)

    def test_a_child_can_only_remove_what_the_child_wrote(self):
        tasks = self.titles()
        mine, parents = tasks["Worksheet 4: fractions"], tasks["Read chapter 3 and write a summary"]
        with self.assertRaises(PermissionError):
            self.store.delete_task(HH, parents["id"], KID)
        self.store.delete_task(HH, mine["id"], KID)
        self.assertNotIn("Worksheet 4: fractions", self.titles())
        with self.assertRaises(LookupError):
            self.store.set_task_done(HH, parents["id"], True, "leo")        # a phone never reaches another child's task


class SummaryTests(unittest.TestCase):
    def test_summary_is_pure(self):
        today = date(2026, 10, 7)   # a Wednesday
        def task(kind, days, done=None):
            return homework.view({"id": "x", "kind": kind, "subject": None, "title": "t", "due_on": (today + timedelta(days=days)).isoformat(),
                                  "note": None, "done_at": done, "created_by": "child"}, today)
        tasks = [task("homework", 1), task("test", 14), task("test", 15), task("homework", -2), task("homework", 0, "2026-10-06T10:00:00+00:00"),
                 task("homework", 0, "2026-10-04T10:00:00+00:00")]
        summary = homework.summarize(tasks, today)
        self.assertEqual((summary["due_tomorrow"], summary["tests_soon"], summary["overdue"], summary["done_this_week"]), (1, 1, 1, 1))
        self.assertEqual([d["open"] for d in summary["week"]], [1, 0, 0, 1, 0])   # Mon..Fri: the overdue one (Mon) and tomorrow's (Thu)

"""Done and not relevant: per-child marks on reminders, and 'not relevant' on homework."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from chit_server.loader import load_file_module
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
learning = load_file_module(Path(__file__).parents[2] / "learning" / "server" / "routes.py")
HH, KID = "hh-meyer", "mila"


def req(method="POST", body=None, params=None, token=None):
    return Request(method, "/x", {}, "application/json", json.dumps(body or {}).encode(), params=params or {}, headers={"authorization": "Bearer " + token} if token else {})


class StateTests(unittest.TestCase):
    def setUp(self):
        EncryptedHouseholdStore._failures.clear()
        routes.clear_events_cache()
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "s.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store, read=lambda path, query=None: {"state": "available", "events": []})
        self.store.set_phone_settings(HH, KID, True)
        pairing = self.store.create_phone_pairing(HH, KID)
        self.token = self.store.complete_phone_pairing(pairing["secret"], pairing["code"])["token"]
        self.today = datetime.now().date()
        self.rid = self.store.add_reminder(HH, "Hand in the trip form", None, self.today.isoformat(), (), None)     # for everyone
        self.view = lambda: routes.view(self.ctx, req("GET", token=self.token))[1]

    def tearDown(self):
        self.temp.cleanup()

    def reminder(self, which="today"):
        return next(r for r in self.view()["reminders"][which] if r["id"] == self.rid)

    # ---- reminders ----
    def test_a_reminder_can_be_marked_done_or_not_relevant_and_cleared(self):
        self.assertIsNone(self.reminder()["state"])
        for state in ("done", "na", None):
            routes.reminder_state(self.ctx, req(body={"state": state}, params={"id": self.rid}, token=self.token))
            self.assertEqual(self.reminder()["state"], state)             # still listed, so it can be undone

    def test_a_childs_mark_is_private_to_that_child_and_the_dashboard_is_separate(self):
        routes.reminder_state(self.ctx, req(body={"state": "done"}, params={"id": self.rid}, token=self.token))
        self.assertEqual(self.store.reminder_states_for_day(HH, self.today, KID), {self.rid: "done"})
        self.assertEqual(self.store.reminder_states_for_day(HH, self.today, "leo"), {})            # another child
        self.assertEqual(self.store.reminder_states_for_day(HH, self.today, ""), {})               # the dashboard
        self.store.set_reminder_state(HH, self.rid, self.today, "done", "")                         # the dashboard marks it too
        self.store.set_reminder_state(HH, self.rid, self.today, None, KID)                          # ... and the child undoes theirs
        self.assertEqual(self.store.reminder_states_for_day(HH, self.today, ""), {self.rid: "done"})
        self.assertEqual(self.store.reminder_states_for_day(HH, self.today, KID), {})

    def test_the_bag_follows_the_reminder_state(self):
        def bag_entry():
            day = next((d for d in self.view()["bag"]["days"] if d["date"] == self.today.isoformat()), None)
            return None if day is None else next((e for e in day["items"] if e.get("rid") == self.rid), None)
        if bag_entry() is None:
            self.skipTest("today is not a school day in the seeded plan")
        self.assertEqual(bag_entry()["ticked"], False)
        routes.reminder_state(self.ctx, req(body={"state": "done"}, params={"id": self.rid}, token=self.token))
        self.assertEqual(bag_entry()["ticked"], True)                       # done in the card layout is ticked in the checklist
        routes.reminder_state(self.ctx, req(body={"state": "na"}, params={"id": self.rid}, token=self.token))
        self.assertIsNone(bag_entry())                                      # not relevant: not something to pack

    def test_reminder_state_rules(self):
        for body, status in (({"state": "maybe"}, 400), ({"state": "done", "date": (self.today - timedelta(days=1)).isoformat()}, 400),
                             ({"state": "done", "date": (self.today + timedelta(days=8)).isoformat()}, 400)):
            with self.assertRaises(HTTPError) as caught:
                routes.reminder_state(self.ctx, req(body=body, params={"id": self.rid}, token=self.token))
            self.assertEqual(caught.exception.status, status, body)
        routes.reminder_state(self.ctx, req(body={"state": "done", "date": (self.today + timedelta(days=1)).isoformat()}, params={"id": self.rid}, token=self.token))   # tomorrow is fine; so is the next school day a few days away
        with self.assertRaises(HTTPError) as caught:                         # a reminder that does not exist
            routes.reminder_state(self.ctx, req(body={"state": "done"}, params={"id": "nope"}, token=self.token))
        self.assertEqual(caught.exception.status, 404)
        self.store.set_phone_settings(HH, KID, None, {"reminders": False})
        with self.assertRaises(HTTPError) as caught:
            routes.reminder_state(self.ctx, req(body={"state": "done"}, params={"id": self.rid}, token=self.token))
        self.assertEqual(caught.exception.status, 403)
        with self.assertRaises(HTTPError) as caught:
            routes.reminder_state(self.ctx, req(body={"state": "done"}, params={"id": self.rid}))                 # no device token
        self.assertEqual(caught.exception.status, 401)

    def test_old_marks_are_cleaned_up(self):
        self.store.set_reminder_state(HH, self.rid, self.today - timedelta(days=1), "done", KID)
        self.store.set_reminder_state(HH, self.rid, self.today + timedelta(days=30), "done", KID)           # writing a far day prunes anything over 14 days older
        self.store.set_reminder_state(HH, self.rid, self.today, "done", KID)
        self.assertEqual(self.store.reminder_states_for_day(HH, self.today - timedelta(days=1), KID), {})

    # ---- homework: not relevant ----
    def task(self, title="Worksheet 4: fractions"):
        return next(t for t in self.view()["homework"]["tasks"] if t["title"] == title)

    def test_homework_can_be_dismissed_and_restored_and_never_counts_as_done(self):
        task = self.task()
        before = self.view()["homework"]["summary"]
        routes.dismiss_homework(self.ctx, req(body={"dismissed": True}, params={"id": task["id"]}, token=self.token))
        dismissed = self.task()
        self.assertEqual((dismissed["dismissed"], dismissed["done"]), (True, False))
        summary = self.view()["homework"]["summary"]
        self.assertEqual(summary["due_tomorrow"], before["due_tomorrow"] - 1)           # not open any more ...
        self.assertEqual(summary["done_this_week"], before["done_this_week"])           # ... and not counted as finished work
        routes.dismiss_homework(self.ctx, req(body={"dismissed": False}, params={"id": task["id"]}, token=self.token))
        self.assertEqual(self.task()["dismissed"], False)
        self.assertEqual(self.view()["homework"]["summary"]["due_tomorrow"], before["due_tomorrow"])

    def test_done_and_dismissed_exclude_each_other(self):
        task = self.task()
        routes.dismiss_homework(self.ctx, req(body={"dismissed": True}, params={"id": task["id"]}, token=self.token))
        routes.tick_homework(self.ctx, req(body={"done": True}, params={"id": task["id"]}, token=self.token))
        self.assertEqual((self.task()["done"], self.task()["dismissed"]), (True, False))   # finishing it makes it relevant again
        routes.dismiss_homework(self.ctx, req(body={"dismissed": True}, params={"id": task["id"]}, token=self.token))
        self.assertEqual((self.task()["done"], self.task()["dismissed"]), (False, True))

    def test_dismissing_is_validated_and_stays_within_the_childs_own_tasks(self):
        with self.assertRaises(HTTPError) as caught:
            routes.dismiss_homework(self.ctx, req(body={"dismissed": "yes"}, params={"id": self.task()["id"]}, token=self.token))
        self.assertEqual(caught.exception.status, 400)
        self.store.add_school_slot(HH, "leo", 1, "08:00", "08:45", "Maths", "lesson", None)
        other = self.store.add_task(HH, "leo", "homework", "Maths", "Leo's sheet", self.today.isoformat(), None, "child", self.today)
        with self.assertRaises(HTTPError) as caught:
            routes.dismiss_homework(self.ctx, req(body={"dismissed": True}, params={"id": other}, token=self.token))
        self.assertEqual(caught.exception.status, 404)                                      # another child's task
        mine = self.task()["id"]
        self.store.set_phone_settings(HH, KID, None, {"homework": False})
        with self.assertRaises(HTTPError) as caught:                                        # homework is not shared with this phone
            routes.dismiss_homework(self.ctx, req(body={"dismissed": True}, params={"id": mine}, token=self.token))
        self.assertEqual(caught.exception.status, 403)

    def test_a_parent_can_dismiss_from_the_web_and_old_dismissed_tasks_leave_the_list(self):
        task = self.task()
        status, _ = learning.update_task(self.ctx, req(body={"dismissed": True}, params={"id": task["id"]}))
        self.assertEqual(status, 200)
        self.assertTrue(self.task()["dismissed"])
        with self.assertRaises(HTTPError):
            learning.update_task(self.ctx, req(body={"dismissed": "no"}, params={"id": task["id"]}))
        with self.store._connection() as connection:       # backend-neutral: works on SQLite and Postgres
            connection.execute("UPDATE kid_tasks SET dismissed_at = ? WHERE id = ?", ((datetime.now(timezone.utc) - timedelta(days=30)).isoformat(), task["id"]))
        self.assertNotIn(task["id"], [t["id"] for t in self.view()["homework"]["tasks"]])      # dismissed a month ago: out of the list


if __name__ == "__main__":
    unittest.main()

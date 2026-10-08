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
plan = load_file_module(Path(__file__).parents[3] / "shared" / "plan.py")
HH, KID = "hh-meyer", "mila"
WED = date(2026, 10, 7)
SAT = date(2026, 10, 10)


def req(method="POST", body=None, params=None, token=None):
    return Request(method, "/x", {}, "application/json", json.dumps(body or {}).encode(), params=params or {}, headers={"authorization": "Bearer " + token} if token else {})


class PureTests(unittest.TestCase):
    def test_leave_by_only_when_a_commute_was_entered(self):
        activities = [{"name": "Swimming", "location": "Stadtbad", "start_time": "17:00", "end_time": "18:00", "days": ["wednesday"], "commute_mode": "cycle",
                       "travel_minutes": 10, "escort": "independent", "escort_adult_client_id": None},
                      {"name": "Football", "location": "Sportpark", "start_time": "10:00", "end_time": "11:30", "days": ["saturday", "sunday"], "commute_mode": "car",
                       "travel_minutes": 20, "escort": "parent", "escort_adult_client_id": "jonas"},
                      {"name": "Choir", "location": None, "start_time": "15:00", "end_time": "16:00", "days": ["monday"], "commute_mode": None, "travel_minutes": None,
                       "escort": "independent", "escort_adult_client_id": None},
                      {"name": "Broken", "start_time": None, "days": ["monday"]}]
        weekly = {a["name"]: a for a in plan.weekly_activities(activities, {"jonas": "Jonas"})}
        self.assertEqual((weekly["Swimming"]["leave_by"], weekly["Swimming"]["weekdays"]), ("16:50", [2]))
        self.assertEqual((weekly["Football"]["leave_by"], weekly["Football"]["escort_name"], weekly["Football"]["weekdays"]), ("09:40", "Jonas", [5, 6]))
        self.assertIsNone(weekly["Choir"]["leave_by"])                       # nothing is inferred
        self.assertNotIn("Broken", weekly)

    def test_only_the_childs_own_calendars_and_no_work_or_bins(self):
        def event(title, members, category, day=WED, all_day=False):
            return {"title": title, "start": "%sT16:30:00+02:00" % day, "end": "%sT17:30:00+02:00" % day, "all_day": all_day, "members": [], "member_ids": members,
                    "category": category, "source": "cal"}
        agenda = {"events": [event("Swim meet", [KID], "sport_activity"), event("Parents' evening", ["nina"], "school_care"), event("Bins", [KID], "waste_collection"),
                             event("Office party", [KID], "work"), event("Household BBQ", [], "family"), event("Trip day", [KID], "school_care", WED + timedelta(days=2), True),
                             event("Far away", [KID], "family", WED + timedelta(days=30))]}
        got = plan.child_events(agenda, KID, WED)
        self.assertEqual([e["title"] for e in got], ["Swim meet", "Trip day"])
        self.assertEqual((got[0]["start"], got[0]["end"]), ("16:30", "17:30"))
        self.assertIsNone(got[1]["start"])                                    # all-day event has no clock time

    def test_bag_merges_duplicates_and_adds_reminders_homework_and_activity_items(self):
        items = [{"subject": "Sport", "label": "Sports kit"}, {"subject": "Maths", "label": "Pencil case"}, {"subject": "German", "label": "pencil case"},
                 {"subject": "Swimming", "label": "Swim bag"}]
        tasks = [{"kind": "homework", "done": False, "due_on": WED.isoformat(), "subject": "Maths", "title": "Worksheet 4"},
                 {"kind": "homework", "done": True, "due_on": WED.isoformat(), "subject": "German", "title": "Essay"},
                 {"kind": "test", "done": False, "due_on": WED.isoformat(), "subject": "English", "title": "Vocab"},
                 {"kind": "homework", "done": False, "due_on": (WED + timedelta(days=1)).isoformat(), "subject": "Art", "title": "Drawing"}]
        got = plan.derive_bag(["Maths", "German", "Sport", "Maths"], items, [{"title": "Hand in the trip form"}], tasks, ["Swimming"], WED, {"sports kit"})
        labels = [e["label"] for e in got]
        self.assertEqual(labels, ["Pencil case", "Sports kit", "Hand in the trip form", "Maths: Worksheet 4", "Swim bag"])
        merged = got[0]
        self.assertEqual(merged["for"], ["Maths", "German"])
        self.assertEqual([e["ticked"] for e in got], [False, True, False, False, False])

    def test_next_school_day_skips_the_weekend(self):
        slots = [{"weekday": d, "kind": "lesson", "start": "08:00", "title": "Maths"} for d in range(5)]
        self.assertEqual(plan.next_school_day(slots, date(2026, 10, 9)), date(2026, 10, 12))   # Friday -> Monday
        self.assertEqual(plan.next_school_day([], WED), None)


class PhoneViewTests(unittest.TestCase):
    def setUp(self):
        EncryptedHouseholdStore._failures.clear()
        routes.clear_events_cache()
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "p.db", plain=True)
        seed_all(self.store)
        self.calls = 0
        self.agenda = {"state": "available", "checked_at": "2026-10-07T08:00:00+00:00", "events": [{
            "title": "Swim meet", "start": "%sT16:30:00+02:00" % date.today(), "end": "%sT17:30:00+02:00" % date.today(), "all_day": False, "category": "sport_activity",
            "source": "Swim club", "members": ["Mila"], "member_ids": [KID]}]}

        def read(path, query=None):
            self.calls += 1
            if isinstance(self.agenda, Exception):
                raise self.agenda
            return self.agenda
        self.ctx = Context(store=self.store, read=read)
        self.store.set_phone_settings(HH, KID, True)
        pairing = self.store.create_phone_pairing(HH, KID)
        self.token = self.store.complete_phone_pairing(pairing["secret"], pairing["code"])["token"]

    def tearDown(self):
        self.temp.cleanup()

    def view(self):
        return routes.view(self.ctx, req("GET", token=self.token))[1]

    def test_activities_and_the_childs_events_reach_the_phone(self):
        activities = self.view()["activities"]
        swimming = next(a for a in activities["weekly"] if a["name"] == "Swimming")
        self.assertEqual((swimming["start"], swimming["leave_by"], swimming["weekdays"]), ("17:00", "16:50", [2]))   # cycle, 10 minutes
        self.assertEqual((swimming["icon"], activities["weekly"][-1]["icon"]), ("🏊", "⚽"))        # Swimming, then Football (Saturday): each with its own icon
        self.assertEqual([(e["title"], e["icon"]) for e in activities["events"]], [("Swim meet", "🏊")])
        self.assertEqual(activities["events_state"], "available")

    def test_the_calendar_is_read_once_per_ten_minutes_not_per_refresh(self):
        self.view(); self.view(); self.view()
        self.assertEqual(self.calls, 1)

    def test_a_failing_calendar_is_reported_honestly_and_keeps_the_last_good_events(self):
        self.view()
        routes._EVENTS[HH] = (routes._EVENTS[HH][0] - 10_000, routes._EVENTS[HH][1])    # make the cache stale
        self.agenda = RuntimeError("feed down")
        stale = self.view()["activities"]                                                # served from cache at once
        self.assertEqual(len(stale["events"]), 1)
        import time as _t
        for _ in range(50):
            if HH not in routes._REFRESHING:
                break
            _t.sleep(0.05)
        after = self.view()["activities"]
        self.assertEqual((after["events_state"], len(after["events"])), ("stale", 1))

    def test_no_calendar_links_is_unconfigured_not_empty(self):
        self.agenda = {"state": "unavailable", "reason": "unconfigured", "events": []}
        self.assertEqual(self.view()["activities"]["events_state"], "unconfigured")

    def test_not_sharing_removes_the_sections(self):
        self.store.set_phone_settings(HH, KID, None, {"activities": False, "bag": False})
        payload = self.view()
        self.assertNotIn("activities", payload)
        self.assertNotIn("bag", payload)

    def test_bag_for_a_school_day_uses_lessons_and_marks_ticks(self):
        document = self.store.get_household_document(HH)
        bag = routes._bag(self.ctx, HH, KID, WED, True, True, document)
        today = next(d for d in bag["days"] if d["date"] == WED.isoformat())
        labels = [e["label"] for e in today["items"]]
        self.assertIn("Sports kit", labels)                      # Sport is on the seeded timetable
        self.assertIn("Swim bag", labels)                        # Wednesday swimming
        self.assertFalse(today["ready"])
        for entry in today["items"]:
            self.store.set_bag_tick(KID, WED, entry["key"], True)
        again = routes._bag(self.ctx, HH, KID, WED, True, True, document)
        self.assertTrue(again["days"][0]["ready"])

    def test_the_weekend_packs_for_monday(self):
        bag = routes._bag(self.ctx, HH, KID, SAT, True, True, self.store.get_household_document(HH))
        self.assertEqual([d["date"] for d in bag["days"]], [date(2026, 10, 12).isoformat()])

    def test_without_the_timetable_the_bag_says_so_and_guesses_nothing(self):
        bag = routes._bag(self.ctx, HH, KID, WED, False, True, self.store.get_household_document(HH))
        self.assertEqual((bag["available"], bag["reason"], bag["days"]), (False, "timetable_not_shared", []))

    def test_phone_can_tick_add_and_remove_its_own_items_but_not_a_parents(self):
        day = date.today().isoformat()
        routes.tick_bag(self.ctx, req(body={"date": day, "key": "Sports Kit", "done": True}, token=self.token))
        self.assertIn("sports kit", self.store.list_bag_ticks(KID, [date.today()])[day])
        status, body = routes.add_bag_item(self.ctx, req(body={"subject": "Art", "label": "Apron"}, token=self.token))
        self.assertEqual(status, 201)
        with self.assertRaises(HTTPError) as caught:                                    # duplicate
            routes.add_bag_item(self.ctx, req(body={"subject": "art", "label": "apron"}, token=self.token))
        self.assertEqual(caught.exception.status, 400)
        routes.remove_bag_item(self.ctx, req(params={"id": body["id"]}, token=self.token))
        parents = next(i for i in self.store.list_bag_items(HH, KID) if i["by"] == "parent")
        with self.assertRaises(HTTPError) as caught:
            routes.remove_bag_item(self.ctx, req(params={"id": parents["id"]}, token=self.token))
        self.assertEqual(caught.exception.status, 403)

    def test_a_tick_cannot_be_dated_far_away(self):
        with self.assertRaises(HTTPError) as caught:
            routes.tick_bag(self.ctx, req(body={"date": (date.today() + timedelta(days=60)).isoformat(), "key": "x", "done": True}, token=self.token))
        self.assertEqual(caught.exception.status, 400)

    def test_manifest_allows_landscape(self):
        self.assertNotIn("orientation", routes.manifest(self.ctx, req("GET"))[1])

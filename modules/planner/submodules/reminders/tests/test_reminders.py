from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest

from chit_server.loader import load_file_module
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

timeline = load_file_module(Path(__file__).parents[2] / "timeline" / "server" / "routes.py")  # reads the same store API
TODAY = date(2026, 10, 7)  # Wednesday


class ReminderStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "r.db", plain=True)
        seed_all(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def titles(self, day):
        return [r["title"] for r in self.store.list_reminders_for_day("hh-meyer", day)]

    def setUp_recurring(self):
        self.store.add_reminder("hh-meyer", "Pack the swimming bag", "mila", None, [2], "morning", reminder_id="rem-weekly")

    def test_recurring_reminders_follow_their_weekdays(self):
        self.setUp_recurring()
        self.assertIn("Pack the swimming bag", self.titles(TODAY))                  # Wednesday
        self.assertNotIn("Pack the swimming bag", self.titles(TODAY + timedelta(days=1)))

    def test_one_off_reminders_only_on_their_date(self):
        day = date.today()
        self.store.add_reminder("hh-meyer", "Renew passport", "nina", day.isoformat(), day_part="day", reminder_id="r-pass")
        self.assertIn("Renew passport", self.titles(day))
        self.assertNotIn("Renew passport", self.titles(day + timedelta(days=1)))

    def test_every_day_when_no_weekdays_and_no_date(self):
        self.store.add_reminder("hh-meyer", "Vitamins", None, None, [], "morning", reminder_id="rem-vitamins")
        self.assertIn("Vitamins", self.titles(TODAY))
        self.assertIn("Vitamins", self.titles(TODAY + timedelta(days=3)))

    def test_ordered_by_day_part_with_any_time_last(self):
        self.store.add_reminder("hh-meyer", "Whenever", None, None, [], None, reminder_id="r-any")
        parts = [r["day_part"] for r in self.store.list_reminders_for_day("hh-meyer", TODAY)]
        order = {"morning": 0, "day": 1, "evening": 2, None: 3}
        self.assertEqual(parts, sorted(parts, key=lambda p: order[p]))
        self.assertEqual(parts[-1], None)

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.store.add_reminder("hh-meyer", "x", "nobody")                           # not a member
        with self.assertRaises(ValueError):
            self.store.add_reminder("hh-meyer", "x", None, "2026-10-09", [1])             # date and weekdays
        with self.assertRaises(ValueError):
            self.store.add_reminder("hh-meyer", "x", None, None, [], "midnight")          # unknown zone
        with self.assertRaises(ValueError):
            self.store.add_reminder("hh-meyer", " ")

    def test_update_and_archive(self):
        self.store.add_reminder("hh-meyer", "Vitamins", None, None, [], "morning", reminder_id="rem-vitamins")
        self.store.update_reminder("hh-meyer", "rem-vitamins", "Vitamins and water", None, None, [0], "evening")
        row = next(r for r in self.store.list_reminders("hh-meyer") if r["id"] == "rem-vitamins")
        self.assertEqual((row["title"], row["weekdays"], row["day_part"]), ("Vitamins and water", [0], "evening"))
        self.store.archive_reminder("hh-meyer", "rem-vitamins")
        self.assertNotIn("rem-vitamins", [r["id"] for r in self.store.list_reminders("hh-meyer")])
        with self.assertRaises(LookupError):
            self.store.archive_reminder("hh-meyer", "rem-vitamins")

    def test_timeline_lists_reminders_for_the_client_to_place_in_zones(self):
        items = timeline.reminder_items([
            {"id": "a", "title": "Dentist", "member_id": "nina", "day_part": "day", "skipped": False},
            {"id": "b", "title": "Skipped", "member_id": None, "day_part": "evening", "skipped": True},
            {"id": "c", "title": "Whenever", "member_id": "nina", "day_part": None, "skipped": False},
        ])
        self.assertEqual([(i["title"], i["day_part"]) for i in items], [("Dentist", "day"), ("Whenever", None)])

    def test_skip_hides_for_that_day_only_and_can_be_undone(self):
        self.store.add_reminder("hh-meyer", "Vitamins", None, None, [], "morning", reminder_id="rem-vitamins")
        self.store.set_skipped("hh-meyer", "reminder", "rem-vitamins", TODAY, True)
        by_id = {r["id"]: r for r in self.store.list_reminders_for_day("hh-meyer", TODAY)}
        self.assertTrue(by_id["rem-vitamins"]["skipped"])
        tomorrow = {r["id"]: r for r in self.store.list_reminders_for_day("hh-meyer", TODAY + timedelta(days=1))}
        self.assertFalse(tomorrow["rem-vitamins"]["skipped"])
        self.store.set_skipped("hh-meyer", "reminder", "rem-vitamins", TODAY, False)
        self.assertFalse({r["id"]: r for r in self.store.list_reminders_for_day("hh-meyer", TODAY)}["rem-vitamins"]["skipped"])
        with self.assertRaises(LookupError):
            self.store.set_skipped("other-household", "reminder", "rem-vitamins", TODAY, True)

    def test_done_is_per_day_and_per_screen_and_does_not_remove_the_reminder(self):
        self.store.add_reminder("hh-meyer", "Hand in the trip form", None, TODAY.isoformat(), (), None, reminder_id="rem-form")
        self.store.set_reminder_state("hh-meyer", "rem-form", TODAY, "done")                       # the dashboard
        self.assertEqual(self.store.reminder_states_for_day("hh-meyer", TODAY), {"rem-form": "done"})
        self.assertIn("Hand in the trip form", self.titles(TODAY))                                # still listed: done is not deleted
        self.assertEqual(self.store.reminder_states_for_day("hh-meyer", TODAY + timedelta(days=1)), {})     # another day is untouched
        self.assertEqual(self.store.reminder_states_for_day("hh-meyer", TODAY, "mila"), {})       # Mila's phone is separate
        self.store.set_reminder_state("hh-meyer", "rem-form", TODAY, None)
        self.assertEqual(self.store.reminder_states_for_day("hh-meyer", TODAY), {})
        with self.assertRaises(ValueError):
            self.store.set_reminder_state("hh-meyer", "rem-form", TODAY, "later")
        with self.assertRaises(LookupError):
            self.store.set_reminder_state("hh-meyer", "nope", TODAY, "done")

    def test_done_route_and_the_today_payload(self):
        import json
        from datetime import datetime
        from chit_server.router import Context, Request
        routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
        today = datetime.now().date()
        self.store.add_reminder("hh-meyer", "Bring the form", None, today.isoformat(), (), None, reminder_id="rem-now")
        ctx = Context(store=self.store)
        post = lambda body, rid: Request("POST", "/x", {}, "application/json", json.dumps(body).encode(), params={"id": rid})
        routes.mark_done(ctx, post({"done": True}, "rem-now"))
        item = next(r for r in routes.today(ctx, Request("GET", "/x", {}, ""))[1]["reminders"] if r["id"] == "rem-now")
        self.assertTrue(item["done"])
        routes.mark_done(ctx, post({"done": False}, "rem-now"))
        item = next(r for r in routes.today(ctx, Request("GET", "/x", {}, ""))[1]["reminders"] if r["id"] == "rem-now")
        self.assertFalse(item["done"])
        from chit_server.router import HTTPError
        for body, rid in (({"done": "yes"}, "rem-now"), ({"done": True}, "nope")):
            with self.assertRaises(HTTPError):
                routes.mark_done(ctx, post(body, rid))

    def test_upcoming_lists_future_one_offs_soonest_first(self):
        today = date.today()
        titles = [r["title"] for r in self.store.list_upcoming_reminders("hh-meyer", today, 7)]
        self.assertEqual(titles[:2], ["Pack the swimming bag", "Parents' evening at school"])
        self.assertNotIn("Call the dentist", titles)   # today is not "upcoming"


if __name__ == "__main__":
    unittest.main()

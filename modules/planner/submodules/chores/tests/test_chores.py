from datetime import date, timedelta
from pathlib import Path
import json
import tempfile
import unittest

from chit_server.loader import load_file_module
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore
from chit_store.chore_series import compute_streak

seed_module = load_file_module(Path(__file__).parents[1] / "server" / "seed.py")
TODAY = date(2026, 10, 7)  # a Wednesday


def days(*offsets):
    return {(TODAY - timedelta(days=n)).isoformat() for n in offsets}


class StreakTests(unittest.TestCase):
    def test_daily_streak_counts_back_from_yesterday_while_today_is_open(self):
        self.assertEqual(compute_streak("", days(1, 2, 3), TODAY), 3)

    def test_today_done_extends_the_streak(self):
        self.assertEqual(compute_streak("", days(0, 1, 2), TODAY), 3)

    def test_a_gap_breaks_it(self):
        self.assertEqual(compute_streak("", days(1, 2, 4), TODAY), 2)

    def test_only_expected_weekdays_count(self):
        # Tuesdays and Fridays: Oct 6 (Tue) and Oct 2 (Fri) completed, Sep 29 (Tue) missed
        done = {"2026-10-06", "2026-10-02"}
        self.assertEqual(compute_streak("1,4", done, TODAY), 2)

    def test_a_skipped_day_neither_counts_nor_breaks_the_streak(self):
        # done yesterday and 3 days ago; the day in between was skipped on purpose
        self.assertEqual(compute_streak("", days(1, 3), TODAY, skipped=days(2)), 2)
        self.assertEqual(compute_streak("", days(1, 3), TODAY), 1)

    def test_no_completions_is_zero(self):
        self.assertEqual(compute_streak("", set(), TODAY), 0)


class ChoreStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "c.db", plain=True)
        seed_all(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def test_seed_is_idempotent_and_streaks_match_the_fixture(self):
        self.assertEqual(seed_module.seed(self.store), [])
        by_id = {c["id"]: c for c in self.store.list_chores_today("hh-meyer", date.today())}
        self.assertEqual(by_id["chore-plants"]["streak"], 12)   # 11 + done today
        self.assertTrue(by_id["chore-plants"]["done"])
        self.assertEqual(by_id["chore-bins"]["streak"], 6)
        self.assertFalse(by_id["chore-bins"]["done"])

    def test_toggle_changes_done_and_streak(self):
        today = date.today()
        self.store.set_chore_done("hh-meyer", "chore-bins", today, True)
        done = {c["id"]: c for c in self.store.list_chores_today("hh-meyer", today)}["chore-bins"]
        self.assertEqual((done["done"], done["streak"]), (True, 7))
        self.store.set_chore_done("hh-meyer", "chore-bins", today, False)
        again = {c["id"]: c for c in self.store.list_chores_today("hh-meyer", today)}["chore-bins"]
        self.assertEqual((again["done"], again["streak"]), (False, 6))

    def test_other_household_cannot_complete_a_chore(self):
        with self.assertRaises(LookupError):
            self.store.set_chore_done("someone-else", "chore-bins", date.today(), True)

    def test_assignee_must_belong_to_the_household(self):
        with self.assertRaises(ValueError):
            self.store.add_chore_series("hh-meyer", "x", assignee_id="nobody")

    def test_skipping_today_flags_it_and_keeps_the_streak(self):
        today = date.today()
        self.store.set_skipped("hh-meyer", "chore", "chore-toys", today, True)
        toys = {c["id"]: c for c in self.store.list_chores_today("hh-meyer", today)}["chore-toys"]
        self.assertTrue(toys["skipped"])
        self.assertEqual(toys["streak"], 2)          # not broken, and not extended
        self.store.set_skipped("hh-meyer", "chore", "chore-toys", today, False)
        self.assertFalse({c["id"]: c for c in self.store.list_chores_today("hh-meyer", today)}["chore-toys"]["skipped"])
        with self.assertRaises(LookupError):
            self.store.set_skipped("hh-meyer", "chore", "nope", today, True)
        with self.assertRaises(ValueError):
            self.store.set_skipped("hh-meyer", "task", "chore-toys", today, True)

    def test_chore_not_due_today_is_not_listed(self):
        today = date.today()
        other = (today.weekday() + 1) % 7
        self.store.add_chore_series("hh-meyer", "Only tomorrow", "nina", [other], series_id="chore-tomorrow")
        ids = [c["id"] for c in self.store.list_chores_today("hh-meyer", today)]
        self.assertNotIn("chore-tomorrow", ids)

    def test_day_part_orders_the_list_and_is_validated(self):
        today = date.today()
        listed = self.store.list_chores_today("hh-meyer", today)
        ranks = {"morning": 0, "day": 1, "evening": 2, None: 3}
        self.assertEqual([c["day_part"] for c in listed], sorted([c["day_part"] for c in listed], key=lambda p: ranks[p]))
        with self.assertRaises(ValueError):
            self.store.add_chore_series("hh-meyer", "x", None, [], day_part="noon")

    def test_update_changes_schedule_and_keeps_history(self):
        today = date.today()
        self.store.update_chore_series("hh-meyer", "chore-toys", "Tidy toys and books", "mila", [today.weekday()], "evening")
        row = next(c for c in self.store.list_chore_series("hh-meyer") if c["id"] == "chore-toys")
        self.assertEqual((row["title"], row["assignee_id"], row["weekdays"], row["day_part"]),
                         ("Tidy toys and books", "mila", [today.weekday()], "evening"))
        # past completions are kept; the streak is recomputed against the new schedule (weekly now, so 0 until it repeats)
        with self.store._connection() as connection:
            kept = connection.execute("SELECT COUNT(*) FROM chore_completions WHERE series_id = 'chore-toys'").fetchone()[0]
        self.assertEqual(kept, 2)
        self.assertEqual(next(c for c in self.store.list_chores_today("hh-meyer", today) if c["id"] == "chore-toys")["streak"], 0)

    def test_archive_hides_but_keeps_history(self):
        self.store.archive_chore_series("hh-meyer", "chore-toys")
        self.assertNotIn("chore-toys", [c["id"] for c in self.store.list_chore_series("hh-meyer")])
        with self.store._connection() as connection:
            kept = connection.execute("SELECT COUNT(*) FROM chore_completions WHERE series_id = 'chore-toys'").fetchone()[0]
        self.assertGreater(kept, 0)
        with self.assertRaises(LookupError):
            self.store.archive_chore_series("hh-meyer", "chore-toys")


if __name__ == "__main__":
    unittest.main()

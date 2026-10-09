from datetime import date, datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from chit_server.loader import load_file_module
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

kids = Path(__file__).parents[2]   # .../kids/submodules
view_routes = load_file_module(kids / "kid-view" / "server" / "routes.py")
grade_routes = load_file_module(kids / "learning" / "server" / "routes.py")
health_routes = load_file_module(kids / "health" / "server" / "routes.py")
HH, MILA, LEO = "hh-meyer", "mila", "leo"
TODAY = date(2026, 10, 7)          # Mila is 10, Leo is 5


def req(body=None, params=None, query=None):
    return Request("PUT", "/x", query or {}, "application/json", json.dumps(body or {}).encode(), params=params or {})


class PrivacyStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "p.db", plain=True)
        seed_all(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def test_defaults_let_a_ten_year_old_hide_grades_but_not_medicine(self):
        mila = self.store.kid_privacy(HH, MILA, TODAY)
        self.assertEqual((mila["grades"]["eligible"], mila["health"]["eligible"]), (True, False))
        self.assertEqual((mila["grades"]["min_age"], mila["health"]["min_age"]), (10, 14))
        self.assertFalse(self.store.kid_privacy(HH, LEO, TODAY)["grades"]["eligible"])

    def test_a_child_can_take_a_section_private_only_when_old_enough(self):
        self.store.set_kid_privacy(HH, MILA, "grades", True, TODAY)
        self.assertTrue(self.store.is_private(HH, MILA, "grades", TODAY))
        with self.assertRaises(ValueError):
            self.store.set_kid_privacy(HH, MILA, "health", True, TODAY)       # 10 < 14
        with self.assertRaises(ValueError):
            self.store.set_kid_privacy(HH, LEO, "grades", True, TODAY)        # 5 < 10
        self.store.set_kid_privacy(HH, MILA, "grades", False, TODAY)          # giving it back is always allowed
        self.assertFalse(self.store.is_private(HH, MILA, "grades", TODAY))

    def test_a_parent_who_raises_the_age_takes_the_choice_back(self):
        self.store.set_kid_privacy(HH, MILA, "grades", True, TODAY)
        self.store.set_privacy_policy(HH, "grades", 12)
        now = self.store.kid_privacy(HH, MILA, TODAY)["grades"]
        self.assertEqual((now["eligible"], now["chosen"], now["private"]), (False, True, False))
        self.store.set_privacy_policy(HH, "grades", 10)                       # lowering it again restores the child's own choice
        self.assertTrue(self.store.is_private(HH, MILA, "grades", TODAY))

    def test_policy_and_choice_are_validated(self):
        for bad in (-1, 19, "ten", True, None):
            with self.assertRaises(ValueError):
                self.store.set_privacy_policy(HH, "grades", bad)
        with self.assertRaises(ValueError):
            self.store.set_privacy_policy(HH, "stars", 10)
        with self.assertRaises(ValueError):
            self.store.set_kid_privacy(HH, MILA, "grades", "yes", TODAY)
        with self.assertRaises(LookupError):
            self.store.kid_privacy(HH, "nina", TODAY)                         # an adult is not a child


class ParentScreensTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "p.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)
        self.today = datetime.now(timezone.utc).date()

    def tearDown(self):
        self.temp.cleanup()

    def _make_old_enough(self, section, ages_to):
        self.store.set_privacy_policy(HH, section, 0)       # the real age depends on today's date: lower the bar so Mila qualifies

    def test_private_grades_send_no_grades_but_keep_the_subjects(self):
        self._make_old_enough("grades", 0)
        subject = self.store.list_subjects_with_grades(HH, MILA)[0]
        self.store.add_grade(HH, subject["id"], "written", 2, self.today, None)
        before = grade_routes.overview(self.ctx, req(query={"member": MILA}))[1]
        self.assertTrue(before["entries"])
        self.store.set_kid_privacy(HH, MILA, "grades", True, self.today)
        after = grade_routes.overview(self.ctx, req(query={"member": MILA}))[1]
        self.assertEqual((after["state"], after["entries"]), ("private", []))
        self.assertTrue(after["subjects"])
        self.assertNotIn("average", after["subjects"][0])
        self.assertNotIn("grades", json.dumps(after["subjects"]))

    def test_private_medicine_stays_visible_only_when_safety_critical(self):
        self._make_old_enough("health", 0)
        self.store.add_med(HH, MILA, "Vitamin D", "1 tablet", "08:00", [0, 1, 2, 3, 4, 5, 6], None, None)
        self.store.add_med(HH, MILA, "Inhaler", "2 puffs", "20:00", [0, 1, 2, 3, 4, 5, 6], None, None, True)
        names = [m["name"] for m in health_routes.overview(self.ctx, req(query={"member": MILA}))[1]["meds"]]
        self.assertIn("Vitamin D", names)
        self.assertIn("Inhaler", names)
        self.store.set_kid_privacy(HH, MILA, "health", True, self.today)
        body = health_routes.overview(self.ctx, req(query={"member": MILA}))[1]
        self.assertEqual(body["state"], "private")
        self.assertEqual([m["name"] for m in body["meds"]], ["Inhaler"])
        self.assertEqual(body["hidden"], len(names) - 1)
        self.assertNotIn("Vitamin D", json.dumps(body))

    def test_the_parent_summary_says_private_but_never_what_is_in_it(self):
        self._make_old_enough("grades", 0)
        self.store.set_kid_privacy(HH, MILA, "grades", True, self.today)
        body = view_routes.privacy(self.ctx, req())[1]
        mila = next(c for c in body["children"] if c["member_id"] == MILA)
        self.assertTrue(mila["sections"]["grades"]["private"])
        self.assertEqual(set(mila["sections"]["grades"]), {"age", "eligible", "private"})
        self.assertEqual(body["policy"]["grades"], 0)
        view_routes.update_privacy_policy(self.ctx, req({"section": "grades", "min_age": 12}))
        self.assertEqual(view_routes.privacy(self.ctx, req())[1]["policy"]["grades"], 12)
        with self.assertRaises(HTTPError):
            view_routes.update_privacy_policy(self.ctx, req({"section": "grades", "min_age": 40}))


if __name__ == "__main__":
    unittest.main()

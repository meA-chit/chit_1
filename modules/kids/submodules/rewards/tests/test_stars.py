from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest

from chit_server.loader import load_file_module
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
HH = "hh-meyer"


def post(body, params=None, query=None):
    import json
    return Request("POST", "/x", query or {}, "application/json", json.dumps(body).encode(), params=params or {})


class StarTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "k.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)
        self.today = date.today()

    def tearDown(self):
        self.temp.cleanup()

    def mila(self):
        _, payload = routes.overview(self.ctx, Request("GET", "/x", {}, ""))
        return next(c for c in payload["children"] if c["member_id"] == "mila")

    def test_seed_shows_stars_goals_and_star_chores(self):
        mila = self.mila()
        self.assertEqual(mila["stars_total"], 9)                      # 6 table + 3 dishwasher, the "again" day earns none
        goals = {g["title"]: g for g in mila["goals"]}
        self.assertEqual(goals["Sleepover with friends"]["pct"], 18)
        self.assertFalse(goals["Movie night, pick the film"]["reached"])
        self.assertEqual({c["title"] for c in mila["chores"] if c["star"]}, {"Empty the dishwasher", "Set the table"})
        self.assertEqual(len(mila["week"]), 7)

    def test_outcome_needs_a_ticked_star_chore(self):
        with self.assertRaises(HTTPError) as raised:                # dishwasher is not ticked off today
            routes.set_outcome(self.ctx, post({"chore_id": "chore-dishwasher", "outcome": "well"}))
        self.assertEqual(raised.exception.status, 400)
        with self.assertRaises(HTTPError) as raised:                # the bins are not a star chore
            routes.set_outcome(self.ctx, post({"chore_id": "chore-bins", "outcome": "well"}))
        self.assertEqual(raised.exception.status, 404)

    def test_a_star_is_added_and_can_be_taken_back_but_never_goes_negative(self):
        before = self.mila()["stars_total"]
        self.store.set_chore_done(HH, "chore-dishwasher", self.today, True)
        routes.set_outcome(self.ctx, post({"chore_id": "chore-dishwasher", "outcome": "well"}))
        self.assertEqual(self.mila()["stars_total"], before + 1)
        routes.set_outcome(self.ctx, post({"chore_id": "chore-dishwasher", "outcome": "again"}))   # try again: no star, nothing subtracted
        self.assertEqual(self.mila()["stars_total"], before)
        self.store.set_chore_done(HH, "chore-dishwasher", self.today, False)                       # unticked: a star needs the tick
        routes.set_outcome(self.ctx, post({"chore_id": "chore-dishwasher", "outcome": None}))

    def test_star_chore_needs_an_owner(self):
        self.store.add_chore_series(HH, "Anyone chore", None, series_id="chore-any")
        with self.assertRaises(HTTPError):
            routes.set_star_chore(self.ctx, post({"enabled": True}, {"id": "chore-any"}))

    def test_goal_counts_from_its_start_and_is_approved_by_a_parent(self):
        routes.create_goal(self.ctx, post({"member_id": "mila", "title": "Ice cream", "cost": 5}))            # fresh start today
        routes.create_goal(self.ctx, post({"member_id": "mila", "title": "Cinema", "cost": 5, "count_existing": True}))
        goals = {g["title"]: g for g in self.mila()["goals"]}
        self.assertEqual(goals["Ice cream"]["have"], 1)   # only today's star, earlier ones do not count
        self.assertTrue(goals["Cinema"]["reached"])
        routes.approve_goal(self.ctx, post({"approved": True}, {"id": goals["Cinema"]["id"]}))
        self.assertEqual({g["title"]: g["status"] for g in self.mila()["goals"]}["Cinema"], "approved")
        routes.remove_goal(self.ctx, Request("DELETE", "/x", {}, "", params={"id": goals["Ice cream"]["id"]}))
        self.assertNotIn("Ice cream", [g["title"] for g in self.mila()["goals"]])

    def test_goal_validation_and_children_only(self):
        for body in ({"member_id": "mila", "title": "x", "cost": 0}, {"member_id": "nina", "title": "x", "cost": 5},
                     {"member_id": "mila", "title": " ", "cost": 5}, {"member_id": "mila", "title": "x", "cost": "5"}):
            with self.assertRaises(HTTPError):
                routes.create_goal(self.ctx, post(body))

    def test_seeding_twice_changes_nothing(self):
        before = self.mila()["stars_total"]
        seed_all(self.store)
        self.assertEqual(self.mila()["stars_total"], before)
        self.assertEqual(len(self.mila()["goals"]), 3)


if __name__ == "__main__":
    unittest.main()

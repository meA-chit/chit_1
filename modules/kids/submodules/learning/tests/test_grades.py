from datetime import date
from pathlib import Path
import json
import tempfile
import unittest

from chit_server.loader import load_file_module
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
grades = load_file_module(Path(__file__).parents[3] / "shared" / "grades.py")
W = {"main_written_pct": 50, "other_written_pct": 30}


def g(kind, value, day="2026-01-01"):
    return {"grade_type": kind, "grade": value, "given_on": day}


def post(body, params=None):
    return Request("POST", "/x", {}, "application/json", json.dumps(body).encode(), params=params or {})


class AverageTests(unittest.TestCase):
    def test_each_type_is_averaged_then_weighted_by_subject_kind(self):
        entries = [g("written", 2), g("written", 3), g("oral", 1)]            # written 2.5, oral 1.0
        self.assertEqual(grades.subject_average("main", entries, W), {"written": 2.5, "oral": 1.0, "average": 1.75})   # 50/50
        self.assertEqual(grades.subject_average("other", entries, W)["average"], 1.45)                                  # 30/70

    def test_one_type_alone_is_used_as_is_and_nothing_is_not_zero(self):
        self.assertEqual(grades.subject_average("other", [g("oral", 2)], W)["average"], 2.0)
        self.assertEqual(grades.subject_average("main", [], W), {"written": None, "oral": None, "average": None})

    def test_trend_needs_three_grades(self):
        self.assertIsNone(grades.trend([g("oral", 2), g("oral", 2)]))
        better = [g("oral", 3, "2026-01-01"), g("oral", 3, "2026-02-01"), g("oral", 2, "2026-03-01"), g("oral", 2, "2026-04-01")]
        self.assertEqual(grades.trend(better), "better")                       # lower is better in the German scale


class GradeRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "g.db", plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)

    def tearDown(self):
        self.temp.cleanup()

    def overview(self):
        return routes.overview(self.ctx, Request("GET", "/x", {}, ""))[1]

    def test_seed_has_main_and_other_subjects_with_weighted_averages(self):
        subjects = {s["name"]: s for s in self.overview()["subjects"]}
        self.assertEqual(subjects["German"]["kind"], "main")
        self.assertEqual(subjects["Sport"]["kind"], "other")
        self.assertEqual(subjects["German"]["average"], 2.25)                  # written (3+2)/2 = 2.5, oral 2.0, 50/50
        self.assertIsNone(subjects["Music"]["written"])                        # no written exam: not invented
        self.assertEqual(len(self.overview()["entries"]), 12)

    def test_add_grade_and_validation(self):
        subject = next(s for s in self.overview()["subjects"] if s["name"] == "Maths")["id"]
        status, _ = routes.add_grade(self.ctx, post({"subject_id": subject, "grade_type": "written", "grade": 1.5, "date": date.today().isoformat()}))
        self.assertEqual(status, 201)
        for bad in ({"grade": 7}, {"grade": 0.5}, {"grade": "2"}, {"grade_type": "project"}, {"date": "2999-01-01"}, {"subject_id": "nope"}):
            body = {"subject_id": subject, "grade_type": "oral", "grade": 2, **bad}
            with self.assertRaises(HTTPError):
                routes.add_grade(self.ctx, post(body))

    def test_weights_change_the_average(self):
        routes.set_weights(self.ctx, post({"main_written_pct": 70, "other_written_pct": 30}))
        german = next(s for s in self.overview()["subjects"] if s["name"] == "German")
        self.assertEqual(german["average"], 2.35)                              # 2.5 * 0.7 + 2.0 * 0.3
        with self.assertRaises(HTTPError):
            routes.set_weights(self.ctx, post({"main_written_pct": 101, "other_written_pct": 30}))

    def test_subjects_belong_to_children_and_can_be_removed_with_their_grades_hidden(self):
        with self.assertRaises(HTTPError):
            routes.add_subject(self.ctx, post({"member_id": "nina", "name": "Latin", "kind": "main"}))
        status, created = routes.add_subject(self.ctx, post({"member_id": "mila", "name": "Latin", "kind": "main"}))
        routes.remove_subject(self.ctx, Request("DELETE", "/x", {}, "", params={"id": created["id"]}))
        self.assertNotIn("Latin", [s["name"] for s in self.overview()["subjects"]])


if __name__ == "__main__":
    unittest.main()

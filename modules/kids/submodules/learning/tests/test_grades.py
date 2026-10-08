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
W = {"core_written_pct": 50, "minor_written_pct": 30, "elective_written_pct": 20}


def g(kind, value, day="2026-01-01"):
    return {"grade_type": kind, "grade": value, "given_on": day}


def post(body, params=None):
    return Request("POST", "/x", {}, "application/json", json.dumps(body).encode(), params=params or {})


class AverageTests(unittest.TestCase):
    def test_each_type_is_averaged_then_weighted_by_subject_type(self):
        entries = [g("written", 2), g("written", 3), g("oral", 1)]            # written 2.5, oral 1.0
        self.assertEqual(grades.subject_average("core", entries, W), {"written": 2.5, "oral": 1.0, "average": 1.75})   # 50/50
        self.assertEqual(grades.subject_average("minor", entries, W)["average"], 1.45)                                  # 30/70
        self.assertEqual(grades.subject_average("elective", entries, W)["average"], 1.3)                                # 20/80: each type has its own weight

    def test_one_type_alone_is_used_as_is_and_nothing_is_not_zero(self):
        self.assertEqual(grades.subject_average("minor", [g("oral", 2)], W)["average"], 2.0)
        self.assertEqual(grades.subject_average("core", [], W), {"written": None, "oral": None, "average": None})

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

    def test_seed_subjects_come_from_the_plan_with_a_type_and_weighted_averages(self):
        subjects = {s["name"]: s for s in self.overview()["subjects"]}
        self.assertEqual(sorted(subjects), ["Biology", "Geography", "German", "Maths", "Sport"])   # exactly the lessons in the seeded plan
        self.assertEqual(subjects["German"]["kind"], "core")
        self.assertEqual(subjects["Sport"]["kind"], "minor")
        self.assertEqual(subjects["German"]["average"], 2.25)                  # written (3+2)/2 = 2.5, oral 2.0, 50/50
        self.assertIsNone(subjects["Sport"]["written"])                        # no written exam: not invented
        self.assertEqual(len(self.overview()["entries"]), 12)
        self.assertEqual([s["kind"] for s in self.overview()["subjects"]], ["core", "core", "minor", "minor", "minor"])   # core first

    def test_add_grade_and_validation(self):
        subject = next(s for s in self.overview()["subjects"] if s["name"] == "Maths")["id"]
        status, _ = routes.add_grade(self.ctx, post({"subject_id": subject, "grade_type": "written", "grade": 1.5, "date": date.today().isoformat()}))
        self.assertEqual(status, 201)
        for bad in ({"grade": 7}, {"grade": 0.5}, {"grade": "2"}, {"grade_type": "project"}, {"date": "2999-01-01"}, {"subject_id": "nope"}):
            body = {"subject_id": subject, "grade_type": "oral", "grade": 2, **bad}
            with self.assertRaises(HTTPError):
                routes.add_grade(self.ctx, post(body))

    def test_weights_change_the_average(self):
        routes.set_weights(self.ctx, post({"core_written_pct": 70, "minor_written_pct": 30, "elective_written_pct": 30}))
        german = next(s for s in self.overview()["subjects"] if s["name"] == "German")
        self.assertEqual(german["average"], 2.35)                              # 2.5 * 0.7 + 2.0 * 0.3
        for bad in ({"core_written_pct": 101}, {"elective_written_pct": "30"}, {"minor_written_pct": None}):
            with self.assertRaises(HTTPError):
                routes.set_weights(self.ctx, post({"core_written_pct": 50, "minor_written_pct": 30, "elective_written_pct": 30, **bad}))

    # ---- subjects exist only because a lesson is in the school-day plan ----
    def subjects(self, member="mila"):
        return {s["name"]: s for s in self.store.list_subjects("hh-meyer", member)}

    def lesson(self, title, subject_kind=None, weekday=4):
        return self.store.add_school_slot("hh-meyer", "mila", weekday, "15:00", "15:45", title, "lesson", None, subject_kind)

    def test_there_is_no_way_to_add_a_subject_directly(self):
        for name in ("add_subject", "create_subject", "archive_subject"):                # a subject only comes from a lesson in the plan
            self.assertFalse(hasattr(routes, name), name)
            self.assertFalse(hasattr(self.store, name), name)

    def test_a_lesson_in_the_plan_creates_its_subject_with_the_chosen_type(self):
        self.assertNotIn("Latin", self.subjects())
        self.lesson("Latin", "core")
        self.assertEqual(self.subjects()["Latin"]["kind"], "core")
        self.lesson("Chess club")                                              # no type given: minor until a parent decides
        self.assertEqual(self.subjects()["Chess club"]["kind"], "minor")
        self.lesson("latin", "elective", weekday=3)                            # the same subject, found case-insensitively, retyped
        self.assertEqual((self.subjects()["Latin"]["kind"], self.subjects()["Latin"]["lessons"]), ("elective", 2))
        self.assertEqual(len([n for n in self.subjects() if n.lower() == "latin"]), 1)

    def test_only_lessons_make_subjects(self):
        self.store.add_school_slot("hh-meyer", "mila", 4, "15:00", "15:45", "Chess club", "care", None, "core")   # a care slot: no subject
        self.assertNotIn("Chess club", self.subjects())

    def test_a_subject_is_per_child(self):
        self.lesson("Latin")
        self.assertNotIn("Latin", self.subjects("leo"))

    def test_the_type_can_be_changed_on_the_subject_and_is_validated(self):
        maths = self.subjects()["Maths"]
        routes.update_subject(self.ctx, post({"kind": "elective"}, {"id": maths["id"]}))
        self.assertEqual(self.subjects()["Maths"]["kind"], "elective")
        for bad in ("main", "other", "", None):
            with self.assertRaises(HTTPError):
                routes.update_subject(self.ctx, post({"kind": bad}, {"id": maths["id"]}))
        with self.assertRaises(HTTPError):
            routes.update_subject(self.ctx, post({"kind": "core"}, {"id": "nope"}))

    def test_removing_the_last_lesson_hides_the_subject_but_keeps_its_grades(self):
        slot = self.lesson("Latin", "core")
        latin = self.subjects()["Latin"]["id"]
        self.store.add_grade("hh-meyer", latin, "oral", 2, date.today(), None)
        self.store.delete_school_slot("hh-meyer", slot)
        self.assertNotIn("Latin", self.subjects())
        self.assertNotIn("Latin", [s["name"] for s in self.overview()["subjects"]])
        with self.assertRaises(HTTPError):                                     # nothing new can be graded under a subject that left the plan
            routes.add_grade(self.ctx, post({"subject_id": latin, "grade_type": "oral", "grade": 2, "date": date.today().isoformat()}))
        self.lesson("Latin")                                                   # the lesson comes back: so do the subject, its type and its grade
        again = next(s for s in self.overview()["subjects"] if s["name"] == "Latin")
        self.assertEqual((again["id"], again["kind"], again["count"]), (latin, "core", 1))

    def test_another_lesson_with_the_same_title_keeps_the_subject_visible(self):
        first, second = self.lesson("Latin", "core"), self.lesson("Latin", weekday=3)
        self.store.delete_school_slot("hh-meyer", first)
        self.assertIn("Latin", self.subjects())
        self.store.delete_school_slot("hh-meyer", second)
        self.assertNotIn("Latin", self.subjects())

    def test_renaming_the_last_lesson_renames_the_subject_with_its_grades(self):
        slot = self.lesson("Latn", "core")
        self.store.add_grade("hh-meyer", self.subjects()["Latn"]["id"], "oral", 2, date.today(), None)
        self.store.update_school_slot("hh-meyer", slot, "15:00", "15:45", "Latin", "lesson", None)
        self.assertEqual(sorted(n for n in self.subjects() if n in ("Latn", "Latin")), ["Latin"])
        renamed = next(s for s in self.overview()["subjects"] if s["name"] == "Latin")
        self.assertEqual((renamed["kind"], renamed["count"]), ("core", 1))

    def test_editing_a_lesson_can_retype_its_subject(self):
        slot = self.lesson("Latin", "core")
        self.store.update_school_slot("hh-meyer", slot, "15:00", "15:45", "Latin", "lesson", None, "elective")
        self.assertEqual(self.subjects()["Latin"]["kind"], "elective")
        with self.assertRaises(ValueError):
            self.store.update_school_slot("hh-meyer", slot, "15:00", "15:45", "Latin", "lesson", None, "main")

    # ---- codes and names ----
    def test_every_subject_has_a_short_unique_code_from_the_start(self):
        codes = [x["code"] for x in self.store.list_subjects("hh-meyer", "mila")]
        self.assertTrue(all(c and 1 <= len(c) <= 6 for c in codes), codes)
        self.assertEqual(len(codes), len({c.lower() for c in codes}))
        self.assertEqual(self.subjects()["Maths"]["code"], "Maths")                  # a short name is its own code

    def test_default_codes(self):
        from chit_store.kids import default_code
        self.assertEqual(default_code("Maths", set()), "Maths")
        self.assertEqual(default_code("Mathematics", set()), "Math")
        self.assertEqual(default_code("Arts & Crafts", set()), "AC")
        self.assertEqual(default_code("Sport m/Sport w", set()), "SMSW")
        self.assertEqual(default_code("Maths", {"maths"}), "Maths2")                 # never a code another subject uses
        self.assertLessEqual(len(default_code("Extraordinarily long", set())), 6)

    def test_name_code_and_type_are_managed_on_the_subject(self):
        maths = self.subjects()["Maths"]
        routes.update_subject(self.ctx, post({"name": "Mathematics", "code": "M", "kind": "elective"}, {"id": maths["id"]}))
        changed = self.subjects()["Mathematics"]
        self.assertEqual((changed["code"], changed["kind"], changed["id"]), ("M", "elective", maths["id"]))
        self.assertNotIn("Maths", self.subjects())

    def test_a_new_name_follows_the_subject_into_lessons_homework_and_bag_items(self):
        maths = self.subjects()["Maths"]
        self.store.add_task("hh-meyer", "mila", "homework", "Maths", "Worksheet", date.today().isoformat(), None, "child", date.today())
        self.store.add_bag_item("hh-meyer", "mila", "Maths", "Compass", "parent")
        self.store.add_grade("hh-meyer", maths["id"], "oral", 2, date.today(), None)
        routes.update_subject(self.ctx, post({"name": "Mathematics"}, {"id": maths["id"]}))
        titles = {s["title"] for s in self.store.list_school_slots("hh-meyer", "mila") if s["kind"] == "lesson"}
        self.assertIn("Mathematics", titles)
        self.assertNotIn("Maths", titles)                                            # every lesson was renamed, so it stays one subject
        self.assertEqual(len([n for n in self.subjects() if n in ("Maths", "Mathematics")]), 1)
        self.assertIn("Mathematics", [t["subject"] for t in self.store.list_tasks("hh-meyer", "mila", date.today())])
        self.assertEqual({i["subject"] for i in self.store.list_bag_items("hh-meyer", "mila") if i["label"] in ("Compass", "Geometry set")}, {"Mathematics"})
        mathematics = next(s for s in self.overview()["subjects"] if s["name"] == "Mathematics")
        self.assertEqual(mathematics["count"], 5)                                    # its grades came along

    def test_names_and_codes_must_be_unique_and_valid(self):
        maths, german = self.subjects()["Maths"], self.subjects()["German"]
        for body in ({"name": "german"}, {"code": self.subjects()["German"]["code"].upper()}, {"code": "toolong1"}, {"code": "a b"}, {"code": ""}, {"name": " "}, {}):
            with self.assertRaises(HTTPError, msg=body):
                routes.update_subject(self.ctx, post(body, {"id": maths["id"]}))
        routes.update_subject(self.ctx, post({"code": maths["code"]}, {"id": maths["id"]}))      # keeping its own code is fine
        self.assertEqual(german["code"], self.subjects()["German"]["code"])

    def test_a_lesson_can_set_the_code_of_its_subject(self):
        self.lesson("Latin", "core")
        self.store.add_school_slot("hh-meyer", "mila", 2, "15:00", "15:45", "Latin", "lesson", None, None, "Lat")
        self.assertEqual(self.subjects()["Latin"]["code"], "Lat")
        with self.assertRaises(ValueError):                                          # a code another subject uses
            self.store.add_school_slot("hh-meyer", "mila", 2, "16:00", "16:45", "Chess", "lesson", None, None, "lat")
        self.assertEqual(next(s for s in self.store.list_school_slots("hh-meyer", "mila") if s["title"] == "Latin")["code"], "Lat")

    def test_a_returning_subject_never_takes_a_code_that_was_given_away(self):
        slot = self.lesson("Latin", "core")
        self.store.update_school_slot("hh-meyer", slot, "15:00", "15:45", "Latin", "lesson", None, None, "Lat")
        self.store.delete_school_slot("hh-meyer", slot)                              # Latin leaves the plan
        other = self.lesson("Chess", None)
        self.store.update_school_slot("hh-meyer", other, "15:00", "15:45", "Chess", "lesson", None, None, "Lat")   # and its code is reused
        self.lesson("Latin")                                                         # Latin returns
        codes = [x["code"].lower() for x in self.store.list_subjects("hh-meyer", "mila")]
        self.assertEqual(len(codes), len(set(codes)))

    # ---- duplicates: merge, or remove ----
    def duplicate_pair(self):
        """The same subject typed twice in the plan with different codes: 'Sport' (kept) and 'Sprt' (the typo)."""
        self.lesson("Sprt", "elective", weekday=4)
        self.lesson("Sprt", None, weekday=3)
        keep, dup = self.subjects()["Sport"], self.subjects()["Sprt"]
        self.store.add_grade("hh-meyer", dup["id"], "oral", 2, date.today(), None)
        self.store.add_task("hh-meyer", "mila", "homework", "Sprt", "Run 3 km", date.today().isoformat(), None, "child", date.today())
        self.store.add_bag_item("hh-meyer", "mila", "Sprt", "Trainers", "child")
        self.store.add_bag_item("hh-meyer", "mila", "Sprt", "Sports kit", "child")           # the kept subject already has this one
        return keep, dup

    def test_merging_moves_everything_onto_the_subject_to_keep(self):
        keep, dup = self.duplicate_pair()
        grades_before = next(s for s in self.overview()["subjects"] if s["name"] == "Sport")["count"]
        status, body = routes.merge_subject(self.ctx, post({"into": keep["id"]}, {"id": dup["id"]}))
        self.assertEqual(status, 200)
        self.assertNotIn("Sprt", self.subjects())
        kept = self.subjects()["Sport"]
        self.assertEqual((kept["id"], kept["code"], kept["kind"]), (keep["id"], keep["code"], keep["kind"]))     # the kept subject is untouched
        titles = [s["title"] for s in self.store.list_school_slots("hh-meyer", "mila") if s["kind"] == "lesson"]
        self.assertNotIn("Sprt", titles)
        self.assertEqual(kept["lessons"], 5 + 2)                                       # its own five lessons plus the duplicate's two
        self.assertEqual(next(s for s in self.overview()["subjects"] if s["name"] == "Sport")["count"], grades_before + 1)   # the grade moved over
        self.assertEqual([t["subject"] for t in self.store.list_tasks("hh-meyer", "mila", date.today()) if t["title"] == "Run 3 km"], ["Sport"])
        labels = sorted(i["label"] for i in self.store.list_bag_items("hh-meyer", "mila") if i["subject"] == "Sport")
        self.assertEqual(labels, ["Sports kit", "Trainers", "Water bottle"])            # no duplicate "Sports kit"
        self.assertFalse([i for i in self.store.list_bag_items("hh-meyer", "mila") if i["subject"] == "Sprt"])

    def test_merging_is_refused_for_bad_pairs(self):
        keep, dup = self.duplicate_pair()
        leo = self.store.list_subjects("hh-meyer", "leo")
        for body, params in (({"into": dup["id"]}, {"id": dup["id"]}), ({"into": "nope"}, {"id": dup["id"]}), ({"into": keep["id"]}, {"id": "nope"}), ({}, {"id": dup["id"]})):
            with self.assertRaises(HTTPError):
                routes.merge_subject(self.ctx, post(body, params))
        self.assertIn("Sprt", self.subjects())                                           # nothing was changed by the refused attempts
        self.store.add_school_slot("hh-meyer", "leo", 1, "08:00", "08:45", "Maths", "lesson", None)
        other = self.store.list_subjects("hh-meyer", "leo")[0]
        with self.assertRaises(HTTPError):                                               # another child's subject
            routes.merge_subject(self.ctx, post({"into": other["id"]}, {"id": dup["id"]}))

    def test_removing_a_subject_removes_its_lessons_grades_and_bag_items(self):
        keep, dup = self.duplicate_pair()
        status, body = routes.remove_subject(self.ctx, Request("DELETE", "/x", {}, "", params={"id": dup["id"]}))
        self.assertEqual((status, body["lessons"], body["grades"]), (200, 2, 1))        # says what was lost
        self.assertNotIn("Sprt", self.subjects())
        self.assertNotIn("Sprt", [s["title"] for s in self.store.list_school_slots("hh-meyer", "mila")])
        self.assertFalse([i for i in self.store.list_bag_items("hh-meyer", "mila") if i["subject"] == "Sprt"])
        homework = [t for t in self.store.list_tasks("hh-meyer", "mila", date.today()) if t["title"] == "Run 3 km"]
        self.assertEqual([t["subject"] for t in homework], [None])                      # the homework stays, without the subject
        self.assertIn("Sport", self.subjects())                                          # the other subjects are untouched
        with self.assertRaises(HTTPError):
            routes.remove_subject(self.ctx, Request("DELETE", "/x", {}, "", params={"id": dup["id"]}))

    def test_plan_slots_report_their_subject_type(self):
        self.lesson("Latin", "elective")
        by_title = {s["title"]: s for s in self.store.list_school_slots("hh-meyer", "mila")}
        self.assertEqual((by_title["Latin"]["subject_kind"], by_title["Maths"]["subject_kind"], by_title["Recess"]["subject_kind"]), ("elective", "core", None))
        self.assertEqual((by_title["Maths"]["code"], by_title["Recess"]["code"]), ("Maths", None))


if __name__ == "__main__":
    unittest.main()

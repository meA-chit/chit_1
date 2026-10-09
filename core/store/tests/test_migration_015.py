"""Migration 015: manual subjects are removed, subjects come from the plan, weights move to three subject types."""
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from chit_store import store as store_module
from chit_store import EncryptedHouseholdStore
from chit_store.testing import sqlite_only


class SubjectsFromPlanMigrationTests(unittest.TestCase):
    @sqlite_only
    def test_old_manual_subjects_and_grades_are_removed_and_the_plan_becomes_the_subjects(self):
        with tempfile.TemporaryDirectory() as temp:
            old_migrations = Path(temp) / "migrations"
            shutil.copytree(store_module.MIGRATIONS, old_migrations)
            for newer in ("015_subjects_from_plan.sql", "016_subject_codes.sql"):     # the database as it was before both
                (old_migrations / newer).unlink()
            real = store_module.MIGRATIONS
            store_module.MIGRATIONS = old_migrations
            try:
                db = Path(temp) / "old.db"
                store = EncryptedHouseholdStore(db, plain=True)
                from chit_store.cli import seed_households
                seed_households(store)                                        # the household only; the old schema cannot take the new seed code
            finally:
                store_module.MIGRATIONS = real
            connection = sqlite3.connect(db)
            for weekday, title, kind in ((0, "Maths", "lesson"), (1, "maths", "lesson"), (0, "Sport m/Sport w", "lesson"), (0, "Recess", "break")):   # a plan typed in before this migration
                connection.execute("INSERT INTO kid_school_slots(id, household_id, member_id, weekday, start_time, end_time, title, kind) VALUES (?, 'hh-meyer', 'mila', ?, '08:00', '08:45', ?, ?)",
                                   ("s%d%s" % (weekday, title), weekday, title, kind))
            connection.execute("DELETE FROM kid_grades")
            connection.execute("DELETE FROM kid_subjects")
            connection.execute("INSERT INTO kid_subjects(id, household_id, member_id, name, kind, created_at) VALUES ('old1', 'hh-meyer', 'mila', 'Arts & Crafts', 'other', 'x')")
            connection.execute("INSERT INTO kid_grades(id, subject_id, grade_type, grade, given_on, created_at) VALUES ('g1', 'old1', 'oral', 2, '2026-01-01', 'x')")
            connection.execute("DELETE FROM kid_settings")
            connection.execute("INSERT INTO kid_settings(household_id, main_written_pct, other_written_pct) VALUES ('hh-meyer', 60, 40)")
            connection.commit()
            connection.close()

            migrated = EncryptedHouseholdStore(db, plain=True)               # opens the old database with the new code: migration 015 runs
            subjects = {s["name"]: s for s in migrated.list_subjects("hh-meyer", "mila")}
            self.assertNotIn("Arts & Crafts", subjects)                       # the manual subject is gone ...
            self.assertEqual(migrated.list_subjects_with_grades("hh-meyer", "mila")[0]["grades"], [])   # ... with its grades
            self.assertEqual(sorted(subjects), ["Maths", "Sport m/Sport w"])  # exactly the lesson titles (Maths and maths are one subject); no break
            self.assertEqual({s["kind"] for s in subjects.values()}, {"minor"})   # type starts as minor; a parent sets it
            self.assertEqual(len({s["code"].lower() for s in subjects.values()}), 2)    # migration 016: every subject got its own short code
            self.assertTrue(all(0 < len(s["code"]) <= 6 for s in subjects.values()))
            self.assertEqual(migrated.list_subjects("hh-meyer", "leo"), [])    # a child with no plan has no subjects
            self.assertEqual(migrated.get_grade_weights("hh-meyer"), {"core_written_pct": 60, "minor_written_pct": 40, "elective_written_pct": 40})
            migrated.add_grade("hh-meyer", subjects["Maths"]["id"], "written", 2, __import__("datetime").date.today(), None)   # the new tables work

    def test_a_fresh_database_gets_the_new_tables(self):
        with tempfile.TemporaryDirectory() as temp:
            store = EncryptedHouseholdStore(Path(temp) / "n.db", plain=True)
            self.assertEqual(store.get_grade_weights("none"), {"core_written_pct": 50, "minor_written_pct": 30, "elective_written_pct": 30})


if __name__ == "__main__":
    unittest.main()

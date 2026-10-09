"""Tenant isolation on Postgres (ADR-0015): one household must never read, change or create another household's data.

Everything here runs through the restricted application role (PostgresHouseholdStore.with_role); the table owner bypasses
row-level security by design, so it is used only to build the fixture and to check the outcome. The suite is skipped on
SQLite, which has no row-level security.
"""
import copy
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

from chit_store import EncryptedHouseholdStore
from chit_store.cli import DEFAULT_SEED_DIR, seed_households
from chit_store.kid_phone import _hash
from chit_store.testing import POSTGRES

if POSTGRES:
    import psycopg

SEED = json.loads((DEFAULT_SEED_DIR / "meyer-family.json").read_text())
NOW = "2026-10-09T10:00:00+00:00"
TOKENS = {"A": "tokenAAAA" + "a" * 36, "B": "tokenBBBB" + "b" * 36}      # shaped like real device tokens (the route checks the shape first)


# People and access, not household content (ADR-0014): read and written only by chit_store.accounts, before any household is
# chosen. Anything else without row-level security is a mistake, so adding a table means deciding which list it belongs to.
ACCOUNT_TABLES = {"auth_accounts", "auth_memberships", "auth_pairings", "auth_enrolments", "auth_email_codes", "auth_sessions",
                  "auth_terms_acceptances", "auth_events"}


def tenant_column(table):
    return "id" if table == "households" else "household_id"


@unittest.skipUnless(POSTGRES, "row-level security exists only on the Postgres backend")
class IsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.owner = EncryptedHouseholdStore(Path(cls.temp.name) / "isolation.db")      # owner role: bypasses RLS
        cls.app = cls.owner.with_role(os.environ["CHIT_PG_TEST_APP_URL"])               # what the real application uses
        assert cls.app._confined and not cls.owner._confined
        cls.A = seed_households(cls.owner)[0]
        other = copy.deepcopy(SEED)
        other["household"]["name"] = "Other family"
        cls.B = cls.owner.save_household_setup(other, preserve_ids=False)["household_id"]
        assert cls.A != cls.B
        cls.members = {}
        for household in (cls.A, cls.B):
            cls._populate(household, "A" if household == cls.A else "B")
        every = [row[0] for row in cls._owner_rows(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
            "AND table_type = 'BASE TABLE' AND table_name <> 'schema_migrations' ORDER BY 1")]
        cls.account_tables = [t for t in every if t in ACCOUNT_TABLES]
        cls.tables = [t for t in every if t not in ACCOUNT_TABLES]      # household content: every one of these must be isolated

        for household, name in ((cls.A, "Kid-A-Aaaa"), (cls.B, "Kid-B-Bbbb")):       # distinguishable in API payloads
            cls._owner_rows("UPDATE household_members SET name = ? WHERE id = ? RETURNING id", (name, cls.members[household]["child"]))
        from chit_server import gateway
        from chit_server.app import build_router
        from chit_server.registry import load_manifests
        full = build_router(load_manifests())
        full.routes[("GET", "/api/planner/calendar/agenda")] = lambda ctx, request: (200, {"state": "unavailable", "events": []})   # no network
        cls.gateway = gateway.make_gateway(cls.app, load_manifests(), full, host="127.0.0.1", port=0)   # the REAL gateway, restricted role
        cls.base = "http://127.0.0.1:%d" % cls.gateway.server_address[1]
        threading.Thread(target=cls.gateway.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.gateway.shutdown()
        cls.gateway.server_close()
        cls.temp.cleanup()

    # --- fixture ------------------------------------------------------------------------------------------------
    @classmethod
    def _owner_rows(cls, sql, params=()):
        with cls.owner._connection() as connection:
            return connection.execute(sql, params).fetchall()

    @classmethod
    def _populate(cls, household, s):
        child = cls._owner_rows("SELECT id FROM household_members WHERE household_id = ? AND role = 'child' ORDER BY seq", (household,))[0][0]
        adult = cls._owner_rows("SELECT id FROM household_members WHERE household_id = ? AND role = 'adult' ORDER BY seq", (household,))[0][0]
        cls.members[household] = {"child": child, "adult": adult}
        statements = [
            ("INSERT INTO chore_series(id, household_id, title, assignee_id, weekdays, archived, created_at, updated_at) VALUES (?, ?, 'Dishes', ?, '', 0, ?, ?)",
             ("ser-" + s, household, adult, NOW, NOW)),
            ("INSERT INTO chore_completions(series_id, day, completed_by, completed_at) VALUES (?, '2026-10-01', ?, ?)", ("ser-" + s, adult, NOW)),
            ("INSERT INTO kid_star_chores(series_id) VALUES (?)", ("ser-" + s,)),
            ("INSERT INTO kid_chore_outcomes(series_id, day, outcome, granted_at) VALUES (?, '2026-10-01', 'well', ?)", ("ser-" + s, NOW)),
            ("INSERT INTO reminders(id, household_id, title, member_id, created_at, updated_at) VALUES (?, ?, 'Water the plants', ?, ?, ?)",
             ("rem-" + s, household, adult, NOW, NOW)),
            ("INSERT INTO reminder_states(household_id, reminder_id, member_id, day, state, updated_at) VALUES (?, ?, ?, '2026-10-01', 'done', ?)",
             (household, "rem-" + s, adult, NOW)),
            ("INSERT INTO kid_goals(id, household_id, member_id, title, cost, started_on, created_at) VALUES (?, ?, ?, 'Bike', 20, '2026-10-01', ?)",
             ("goal-" + s, household, child, NOW)),
            ("INSERT INTO kid_subjects(id, household_id, member_id, name, created_at) VALUES (?, ?, ?, 'Maths', ?) ON CONFLICT DO NOTHING",
             ("sub-" + s, household, child, NOW)),
            ("INSERT INTO kid_grades(id, subject_id, grade_type, grade, given_on, created_at) VALUES (?, ?, 'written', 2, '2026-10-01', ?)",
             ("gr-" + s, "sub-" + s, NOW)),
            ("INSERT INTO kid_meds(id, household_id, member_id, name, time_of_day, created_at) VALUES (?, ?, ?, 'Vitamin D', '08:00', ?)",
             ("med-" + s, household, child, NOW)),
            ("INSERT INTO kid_med_log(med_id, day, status, logged_at) VALUES (?, '2026-10-01', 'given', ?)", ("med-" + s, NOW)),
            ("INSERT INTO kid_tasks(id, household_id, member_id, kind, title, due_on, created_by, created_at) VALUES (?, ?, ?, 'homework', 'Read', '2026-10-10', 'parent', ?)",
             ("task-" + s, household, child, NOW)),
            ("INSERT INTO kid_bag_items(id, household_id, member_id, subject, label, created_by, created_at) VALUES (?, ?, ?, 'Maths', 'Ruler', 'parent', ?)",
             ("bag-" + s, household, child, NOW)),
            ("INSERT INTO kid_bag_ticks(member_id, day, key, ticked_at) VALUES (?, '2026-10-01', 'Maths:Ruler', ?)", (child, NOW)),
            ("INSERT INTO kid_school_slots(id, household_id, member_id, weekday, start_time, end_time, title, kind) VALUES (?, ?, ?, 0, '08:00', '08:45', 'Maths', 'lesson')",
             ("slot-" + s, household, child)),
            ("INSERT INTO kid_privacy_policy(household_id, section, min_age) VALUES (?, 'grades', 12) ON CONFLICT DO NOTHING", (household,)),
            ("INSERT INTO kid_privacy(member_id, section, private, updated_at) VALUES (?, 'grades', 1, ?) ON CONFLICT DO NOTHING", (child, NOW)),
            ("INSERT INTO kid_phone_access(member_id, household_id, enabled, updated_at) VALUES (?, ?, 1, ?) ON CONFLICT DO NOTHING", (child, household, NOW)),
            ("INSERT INTO kid_phone_devices(id, household_id, member_id, token_hash, paired_at) VALUES (?, ?, ?, ?, ?)",
             ("dev-" + s, household, child, _hash(TOKENS[s]), NOW)),
            ("INSERT INTO kid_phone_handoffs(token_hash, device_id, expires_at) VALUES (?, ?, '2099-01-01T00:00:00+00:00')", (_hash("handoff-" + s), "dev-" + s)),
            ("INSERT INTO kid_phone_pairings(id, household_id, member_id, secret_hash, code_salt, code_hash, expires_at, created_at) VALUES (?, ?, ?, ?, 'salt', 'hash', '2099-01-01T00:00:00+00:00', ?)",
             ("pair-" + s, household, child, _hash("secret-" + s), NOW)),
            ("INSERT INTO planner_skips(household_id, kind, item_id, day, created_at) VALUES (?, 'chore', 'x', '2026-10-01', ?)", (household, NOW)),
            ("INSERT INTO energy_connections(household_id, provider, secret, updated_at) VALUES (?, 'tibber', 'not-a-real-key', ?)", (household, NOW)),
            ("INSERT INTO meter_readings(household_id, meter, read_on, value, updated_at) VALUES (?, 'water', '2026-10-01', 1.5, ?)", (household, NOW)),
            ("INSERT INTO kid_settings(household_id) VALUES (?) ON CONFLICT DO NOTHING", (household,)),
        ]
        with cls.owner._connection() as connection:
            for sql, params in statements:
                connection.execute(sql, params)

    @contextmanager
    def scoped(self, household):
        """A connection of the application role serving one household, for the length of the block."""
        with self.app.request_scope(household), self.app._connection() as connection:
            yield connection

    def app_count(self, table, household, where=""):
        with self.app.request_scope(household), self.app._connection() as connection:
            return connection.execute("SELECT count(*) FROM %s %s" % (table, where)).fetchone()[0]

    def owner_count(self, table, household):
        return self._owner_rows("SELECT count(*) FROM %s WHERE %s = ?" % (table, tenant_column(table)), (household,))[0][0]

    # --- the fixture is meaningful ----------------------------------------------------------------------------------
    def test_fixture_covers_most_tables_for_both_households(self):
        filled = [t for t in self.tables if self.owner_count(t, self.A) and self.owner_count(t, self.B)]
        self.assertGreaterEqual(len(filled), 38, "isolation cannot be proven on tables that hold no data: %s" % sorted(set(self.tables) - set(filled)))

    # --- structure: no table can be forgotten ----------------------------------------------------------------------
    def test_every_table_has_row_level_security_and_a_policy(self):
        secured = {r[0] for r in self._owner_rows(
            "SELECT c.relname FROM pg_class c WHERE c.relnamespace = current_schema()::regnamespace AND c.relkind = 'r' AND c.relrowsecurity")}
        policies = {r[0] for r in self._owner_rows("SELECT tablename FROM pg_policies WHERE schemaname = current_schema()")}
        self.assertEqual(set(self.tables) - secured, set(), "tables without row-level security")
        self.assertEqual(set(self.tables) - policies, set(), "tables without a policy")

    def test_only_the_account_tables_are_outside_row_level_security(self):
        self.assertEqual(set(self.account_tables), ACCOUNT_TABLES)
        unprotected = {r[0] for r in self._owner_rows(
            "SELECT c.relname FROM pg_class c WHERE c.relnamespace = current_schema()::regnamespace AND c.relkind = 'r' "
            "AND NOT c.relrowsecurity AND c.relname <> 'schema_migrations'")}
        self.assertEqual(unprotected, ACCOUNT_TABLES)

    def test_the_application_role_does_not_own_or_bypass_anything(self):
        with self.app._connection() as connection:
            role = connection.execute("SELECT rolsuper, rolbypassrls, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname = current_user").fetchone()
            owned = connection.execute("SELECT count(*) FROM pg_class WHERE relnamespace = current_schema()::regnamespace AND relowner = "
                                       "(SELECT oid FROM pg_roles WHERE rolname = current_user)").fetchone()[0]
        self.assertEqual(role, (False, False, False, False))
        self.assertEqual(owned, 0)

    # --- reads ------------------------------------------------------------------------------------------------------
    def test_without_a_household_nothing_is_visible(self):
        for table in self.tables:
            with self.app._connection() as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM %s" % table).fetchone()[0], 0, table)

    def test_each_household_sees_only_its_own_rows_in_every_table(self):
        for household, other in ((self.A, self.B), (self.B, self.A)):
            for table in self.tables:
                column = tenant_column(table)
                self.assertEqual(self.app_count(table, household, "WHERE %s <> '%s'" % (column, household)), 0, "%s leaks rows" % table)
                self.assertEqual(self.app_count(table, household), self.owner_count(table, household), "%s: wrong row count" % table)
                self.assertEqual(self.app_count(table, household, "WHERE %s = '%s'" % (column, other)), 0, "%s: other household readable by id" % table)

    def test_scope_cannot_be_changed_through_the_store(self):
        with self.app.request_scope(self.A):
            with self.assertRaises(PermissionError):
                self.app.bind_household(self.B)
            self.assertEqual(self.app.current_household(), self.A)

    def test_row_security_cannot_be_switched_off_by_the_application_role(self):
        with self.scoped(self.A) as connection:
            connection.execute("SET row_security = off")
            with self.assertRaises(psycopg.Error):
                connection.execute("SELECT count(*) FROM households").fetchone()

    # --- writes -----------------------------------------------------------------------------------------------------
    def test_rows_of_another_household_cannot_be_updated_or_deleted(self):
        before = {t: self.owner_count(t, self.B) for t in self.tables}
        with self.scoped(self.A) as connection:
            for table in self.tables:
                if table == "households":
                    continue
                self.assertEqual(connection.execute("DELETE FROM %s WHERE household_id = ?" % table, (self.B,)).rowcount, 0, table)
            self.assertEqual(connection.execute("UPDATE household_members SET name = 'hacked' WHERE household_id = ?", (self.B,)).rowcount, 0)
            self.assertEqual(connection.execute("UPDATE households SET name = 'hacked' WHERE id = ?", (self.B,)).rowcount, 0)
            self.assertEqual(connection.execute("DELETE FROM households WHERE id = ?", (self.B,)).rowcount, 0)
        self.assertEqual({t: self.owner_count(t, self.B) for t in self.tables}, before)
        self.assertEqual(self._owner_rows("SELECT name FROM households WHERE id = ?", (self.B,))[0][0], "Other family")

    def test_a_row_cannot_be_written_into_or_moved_to_another_household(self):
        with self.scoped(self.A) as connection:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("INSERT INTO reminders(id, household_id, title, created_at, updated_at) VALUES ('evil', ?, 'x', ?, ?)", (self.B, NOW, NOW))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("INSERT INTO planner_skips(household_id, kind, item_id, day, created_at) VALUES (?, 'chore', 'evil', '2026-10-02', ?)", (self.B, NOW))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("UPDATE reminders SET household_id = ? WHERE id = 'rem-A'", (self.B,))      # move my row into theirs
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("INSERT INTO households(id, name, timezone, owner_member_id, created_at, updated_at) VALUES (?, 'x', 'UTC', 'm', ?, ?)",
                                   (self.B + "-twin", NOW, NOW))        # cannot create a household other than the one served
        self.assertEqual(self._owner_rows("SELECT count(*) FROM reminders WHERE id = 'evil'")[0][0], 0)
        self.assertEqual(self._owner_rows("SELECT household_id FROM reminders WHERE id = 'rem-A'")[0][0], self.A)

    def test_a_child_row_cannot_be_attached_to_another_households_parent(self):
        with self.scoped(self.A) as connection:
            for sql, params in (
                ("INSERT INTO kid_med_log(med_id, day, status, logged_at) VALUES ('med-B', '2026-10-05', 'given', ?)", (NOW,)),
                ("INSERT INTO kid_grades(id, subject_id, grade_type, grade, given_on, created_at) VALUES ('g-evil', 'sub-B', 'oral', 1, '2026-10-05', ?)", (NOW,)),
                ("INSERT INTO kid_bag_ticks(member_id, day, key, ticked_at) VALUES (?, '2026-10-05', 'k', ?)", (self.members[self.B]["child"], NOW)),
                ("INSERT INTO chore_completions(series_id, day, completed_by, completed_at) VALUES ('ser-B', '2026-10-05', 'x', ?)", (NOW,)),
            ):
                # refused either by the row-level policy (the parent is invisible, so no household can be derived) or by
                # the not-null / foreign-key rules; what matters is that nothing is written
                with self.assertRaises((psycopg.errors.InsufficientPrivilege, psycopg.errors.IntegrityError)):
                    connection.execute(sql, params)
        for table, where in (("kid_med_log", "day = '2026-10-05'"), ("kid_grades", "id = 'g-evil'"), ("kid_bag_ticks", "day = '2026-10-05'"),
                             ("chore_completions", "day = '2026-10-05'")):
            self.assertEqual(self._owner_rows("SELECT count(*) FROM %s WHERE %s" % (table, where))[0][0], 0, table)

    def test_a_row_may_not_reference_a_parent_with_a_foreign_household_id(self):
        owner_error = (psycopg.errors.ForeignKeyViolation, psycopg.errors.IntegrityError)
        with self.assertRaises(owner_error):           # even the owner cannot cross households: composite foreign keys
            with self.owner._connection() as connection:
                connection.execute("INSERT INTO kid_goals(id, household_id, member_id, title, cost, started_on, created_at) VALUES ('x', ?, ?, 't', 1, '2026-10-01', ?)",
                                   (self.A, self.members[self.B]["child"], NOW))

    # --- the store -------------------------------------------------------------------------------------------------
    def test_store_methods_given_another_households_id_find_nothing_and_change_nothing(self):
        with self.app.request_scope(self.A):
            self.assertEqual(self.app.list_chore_series(self.B), [])
            with self.assertRaises(LookupError):
                self.app.get_household_document(self.B)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):       # the row-level policy refuses the insert
                self.app.add_chore_series(self.B, "evil chore", None)
            with self.assertRaises(LookupError):                                # the row is invisible, so there is nothing to update
                self.app.update_chore_series(self.B, "ser-B", "hacked", None, [0], None)
        self.assertEqual(self._owner_rows("SELECT title FROM chore_series WHERE id = 'ser-B'")[0][0], "Dishes")
        self.assertEqual(self._owner_rows("SELECT count(*) FROM chore_series WHERE title = 'evil chore'")[0][0], 0)

    def test_each_household_still_works_normally_through_the_store(self):
        for household, other in ((self.A, self.B), (self.B, self.A)):
            before, other_before = self.owner_count("chore_series", household), self.owner_count("chore_series", other)
            with self.app.request_scope(household):
                self.assertEqual(self.app.get_household_document(household)["id"], household)
                self.assertTrue(any(s["title"] == "Dishes" for s in self.app.list_chore_series(household)))
                created = self.app.add_chore_series(household, "New chore", self.members[household]["adult"])
                self.assertIn(created, [s["id"] for s in self.app.list_chore_series(household)])
            self.assertEqual(self.owner_count("chore_series", household), before + 1)
            self.assertEqual(self.owner_count("chore_series", other), other_before)

    def test_the_scope_ends_with_the_request(self):
        with self.app.request_scope(self.A), self.app._connection() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM households").fetchone()[0], 1)
        with self.app._connection() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM households").fetchone()[0], 0)
        with self.app.request_scope(self.B), self.app._connection() as connection:
            self.assertEqual(connection.execute("SELECT id FROM households").fetchone()[0], self.B)

    def test_concurrent_requests_never_see_each_others_household(self):
        failures = []

        def worker(household, other):
            for _ in range(15):
                with self.app.request_scope(household), self.app._connection() as connection:
                    seen = {r[0] for r in connection.execute("SELECT household_id FROM household_members").fetchall()}
                    if seen != {household}:
                        failures.append((household, seen))
        threads = [threading.Thread(target=worker, args=pair) for pair in ((self.A, self.B), (self.B, self.A)) * 3]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(failures, [])

    # --- credentials that identify a household before it is known ---------------------------------------------------
    def test_a_kid_phone_token_selects_exactly_its_own_household(self):
        for token, household in ((TOKENS["A"], self.A), (TOKENS["B"], self.B)):
            with self.app.request_scope(None):
                device = self.app.phone_device_for_token(token)
                self.assertEqual(device["household_id"], household)
                self.assertEqual(self.app.current_household(), household)
                with self.app._connection() as connection:
                    self.assertEqual({r[0] for r in connection.execute("SELECT household_id FROM kid_phone_devices").fetchall()}, {household})

    def test_an_unknown_token_gets_no_household_and_sees_nothing(self):
        with self.app.request_scope(None):
            self.assertIsNone(self.app.phone_device_for_token("tokenNOBODY" + "n" * 34))
            self.assertIsNone(self.app.current_household())
            with self.app._connection() as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM kid_phone_devices").fetchone()[0], 0)

    def test_a_token_cannot_move_a_request_that_already_serves_another_household(self):
        with self.app.request_scope(self.B):
            with self.assertRaises(PermissionError):
                self.app.phone_device_for_token(TOKENS["A"])
            self.assertEqual(self.app.current_household(), self.B)

    def _gateway_get(self, path, token=None):
        request = urllib.request.Request(self.base + path, headers={"Authorization": "Bearer " + token} if token else {})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.status, response.read().decode()
        except urllib.error.HTTPError as error:
            return error.code, error.read().decode()

    def test_the_real_gateway_serves_each_kid_only_their_own_household(self):
        for token, mine, theirs in ((TOKENS["A"], "Kid-A-Aaaa", "Kid-B-Bbbb"), (TOKENS["B"], "Kid-B-Bbbb", "Kid-A-Aaaa")):
            status, body = self._gateway_get("/api/kids/phone/device/view", token)
            self.assertEqual(status, 200, body)
            self.assertIn(mine, body)
            self.assertNotIn(theirs, body)
        for token in (None, "tokenNOBODY" + "n" * 34, "x" * 40):
            self.assertEqual(self._gateway_get("/api/kids/phone/device/view", token)[0], 401)
        for _ in range(5):          # no scope lingers between requests: alternate and re-check
            for token, mine, theirs in ((TOKENS["A"], "Kid-A-Aaaa", "Kid-B-Bbbb"), (TOKENS["B"], "Kid-B-Bbbb", "Kid-A-Aaaa")):
                _, body = self._gateway_get("/api/kids/phone/device/view", token)
                self.assertIn(mine, body)
                self.assertNotIn(theirs, body)

    def test_the_lookup_functions_are_narrow_and_safe(self):
        rows = self._owner_rows("SELECT proname, prosecdef, array_to_string(proconfig, ',') FROM pg_proc "
                                "WHERE pronamespace = current_schema()::regnamespace AND proname LIKE 'chit_%household%' AND prosecdef")
        self.assertEqual({r[0] for r in rows}, {"chit_household_for_phone_credential", "chit_latest_household_id", "chit_households_for_account"})
        for name, _, config in rows:
            self.assertIn("search_path=", config, "%s must pin its search_path" % name)
        with self.app._connection() as connection:       # in a multi-household deployment "latest household" answers nothing
            self.assertIsNone(connection.execute("SELECT chit_latest_household_id()").fetchone()[0])

    def test_single_household_mode_serves_the_latest_household_only(self):
        single = self.owner.with_role(os.environ["CHIT_PG_TEST_APP_URL"])
        single.single_household = True
        latest = self._owner_rows("SELECT id FROM households ORDER BY created_at DESC, seq DESC LIMIT 1")[0][0]
        self.assertEqual(single.default_scope(), latest)
        with single.request_scope(single.default_scope()):
            self.assertEqual(single.latest_household_id(), latest)
            with single._connection() as connection:
                self.assertEqual([r[0] for r in connection.execute("SELECT id FROM households").fetchall()], [latest])
        self.assertIsNone(self.app.default_scope())                       # multi-household: no implicit household
        with self.app.request_scope(None):
            self.assertIsNone(self.app.latest_household_id())


if __name__ == "__main__":
    unittest.main()

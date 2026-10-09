from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from chit_server import gateway
from chit_server.app import build_router
from chit_server.loader import load_file_module
from chit_server.registry import load_manifests
from chit_server.router import Context, HTTPError, Request
from chit_server.seed import seed_all
from chit_store import EncryptedHouseholdStore

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
HH, KID = "hh-meyer", "mila"
T0 = datetime(2026, 10, 7, 9, 0, tzinfo=timezone.utc)


def req(method="POST", body=None, params=None, query=None, token=None):
    headers = {"authorization": "Bearer " + token} if token else {}
    return Request(method, "/x", query or {}, "application/json", json.dumps(body or {}).encode(), params=params or {}, headers=headers)


class PhoneBase(unittest.TestCase):
    def setUp(self):
        EncryptedHouseholdStore._failures.clear()          # the pairing throttle is process-wide
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "p.db"
        self.store = EncryptedHouseholdStore(self.db, plain=True)
        seed_all(self.store)
        self.ctx = Context(store=self.store)

    def tearDown(self):
        self.temp.cleanup()

    def enable(self, **share):
        self.store.set_phone_settings(HH, KID, True, share or None)

    def pair(self, now=T0):
        self.enable()
        pairing = self.store.create_phone_pairing(HH, KID, now)
        return pairing, self.store.complete_phone_pairing(pairing["secret"], pairing["code"], "iPhone", now)


class PairingTests(PhoneBase):
    def test_pairing_needs_the_parent_to_enable_the_phone_view(self):
        with self.assertRaises(ValueError):
            self.store.create_phone_pairing(HH, KID, T0)

    def test_qr_secret_plus_code_pairs_once(self):
        pairing, device = self.pair()
        self.assertEqual(device["member_id"], KID)
        self.assertEqual(self.store.phone_device_for_token(device["token"], T0)["member_id"], KID)
        with self.assertRaises(self.store.PairingError) as again:                    # the QR is single-use
            self.store.complete_phone_pairing(pairing["secret"], pairing["code"], None, T0)
        self.assertEqual(again.exception.reason, "invalid")

    def test_wrong_code_counts_down_then_locks_even_for_the_right_code(self):
        self.enable()
        pairing = self.store.create_phone_pairing(HH, KID, T0)
        wrong = "000000" if pairing["code"] != "000000" else "111111"
        for left in (4, 3, 2, 1):
            with self.assertRaises(self.store.PairingError) as caught:
                self.store.complete_phone_pairing(pairing["secret"], wrong, None, T0)
            self.assertEqual((caught.exception.reason, caught.exception.attempts_left), ("wrong_code", left))
        with self.assertRaises(self.store.PairingError) as caught:
            self.store.complete_phone_pairing(pairing["secret"], wrong, None, T0)
        self.assertEqual(caught.exception.reason, "locked")
        with self.assertRaises(self.store.PairingError):
            self.store.complete_phone_pairing(pairing["secret"], pairing["code"], None, T0)

    def test_pairing_expires_after_ten_minutes(self):
        self.enable()
        pairing = self.store.create_phone_pairing(HH, KID, T0)
        self.assertIsNotNone(self.store.active_phone_pairing(HH, KID, T0 + timedelta(minutes=9)))
        with self.assertRaises(self.store.PairingError) as caught:
            self.store.complete_phone_pairing(pairing["secret"], pairing["code"], None, T0 + timedelta(minutes=10, seconds=1))
        self.assertEqual(caught.exception.reason, "invalid")
        self.assertIsNone(self.store.active_phone_pairing(HH, KID, T0 + timedelta(minutes=11)))

    def test_a_new_pairing_cancels_the_previous_one(self):
        self.enable()
        first = self.store.create_phone_pairing(HH, KID, T0)
        self.store.create_phone_pairing(HH, KID, T0)
        with self.assertRaises(self.store.PairingError):
            self.store.complete_phone_pairing(first["secret"], first["code"], None, T0)

    def test_turning_the_phone_view_off_revokes_every_phone_and_open_pairing(self):
        _, device = self.pair()
        open_pairing = self.store.create_phone_pairing(HH, KID, T0)
        self.store.set_phone_settings(HH, KID, False)
        self.assertIsNone(self.store.phone_device_for_token(device["token"], T0))
        self.assertEqual(self.store.list_phone_devices(HH, KID), [])
        self.enable()                                                                  # turning it on again does not bring them back
        self.assertIsNone(self.store.phone_device_for_token(device["token"], T0))
        with self.assertRaises(self.store.PairingError):
            self.store.complete_phone_pairing(open_pairing["secret"], open_pairing["code"], None, T0)

    def test_revoking_one_phone(self):
        _, device = self.pair()
        self.store.revoke_phone_device(HH, device["device_id"])
        self.assertIsNone(self.store.phone_device_for_token(device["token"], T0))
        with self.assertRaises(LookupError):
            self.store.revoke_phone_device(HH, device["device_id"])

    def test_handoff_is_single_use_expires_and_rotates_the_token(self):
        _, device = self.pair()
        handoff = self.store.create_phone_handoff(device["device_id"], T0)
        new = self.store.exchange_phone_handoff(handoff, T0 + timedelta(minutes=1))
        self.assertIsNotNone(new)
        self.assertIsNone(self.store.phone_device_for_token(device["token"], T0))      # the Safari token is dead now
        self.assertEqual(self.store.phone_device_for_token(new, T0)["device_id"], device["device_id"])
        self.assertIsNone(self.store.exchange_phone_handoff(handoff, T0))              # single use
        late = self.store.create_phone_handoff(device["device_id"], T0)
        self.assertIsNone(self.store.exchange_phone_handoff(late, T0 + timedelta(minutes=16)))

    def test_nothing_secret_is_stored_in_clear(self):
        pairing, device = self.pair()
        handoff = self.store.create_phone_handoff(device["device_id"], T0)
        if os.environ.get("CHIT_STORE_BACKEND") == "postgres":
            with self.store._connection() as connection:
                dump = "\n".join(str(row) for table in ("kid_phone_devices", "kid_phone_pairings", "kid_phone_handoffs")
                                 for row in connection.execute("SELECT * FROM " + table).fetchall())
        else:
            dump = "\n".join(sqlite3.connect(self.db).iterdump())
        for secret in (pairing["secret"], pairing["code"], device["token"], handoff):
            self.assertNotIn(secret, dump)

    def test_a_typed_link_code_pairs_like_the_qr_and_still_needs_the_code(self):
        self.enable()
        pairing = self.store.create_phone_pairing(HH, KID, T0)
        self.assertRegex(pairing["link_code"], r"^[A-Z2-9]{4}-[A-Z2-9]{4}$")
        wrong = "000000" if pairing["code"] != "000000" else "111111"
        with self.assertRaises(self.store.PairingError) as caught:
            self.store.complete_phone_pairing(None, wrong, None, T0, link=pairing["link_code"])
        self.assertEqual(caught.exception.reason, "wrong_code")
        device = self.store.complete_phone_pairing(None, pairing["code"], "Home Screen app", T0, link=pairing["link_code"].lower().replace("-", " "))
        self.assertEqual(device["member_id"], KID)
        with self.assertRaises(self.store.PairingError):                           # one pairing, one phone, however it was typed
            self.store.complete_phone_pairing(pairing["secret"], pairing["code"], None, T0)

    def test_guessing_link_codes_is_throttled(self):
        self.enable()
        pairing = self.store.create_phone_pairing(HH, KID, T0)
        for _ in range(20):
            with self.assertRaises(self.store.PairingError) as caught:
                self.store.complete_phone_pairing(None, "123456", None, T0, link="AAAA-AAAA")
            self.assertEqual(caught.exception.reason, "invalid")
        with self.assertRaises(self.store.PairingError) as caught:                 # even the real codes are refused for a while
            self.store.complete_phone_pairing(None, pairing["code"], None, T0, link=pairing["link_code"])
        self.assertEqual(caught.exception.reason, "throttled")

    def test_only_children_can_have_a_phone_view(self):
        with self.assertRaises(LookupError):
            self.store.set_phone_settings(HH, "nina", True)


class DeviceRouteTests(PhoneBase):
    def token(self):
        return self.pair(datetime.now(timezone.utc))[1]["token"]

    def view(self, token):
        return routes.view(self.ctx, req("GET", token=token))[1]

    def test_no_token_or_a_bad_token_is_401(self):
        for token in (None, "x" * 40):
            with self.assertRaises(HTTPError) as caught:
                routes.view(self.ctx, req("GET", token=token))
            self.assertEqual(caught.exception.status, 401)

    def test_parents_choice_decides_what_the_server_sends(self):
        payload = self.view(self.token())
        self.assertEqual(payload["child"]["name"], "Mila")
        self.assertIn("school", payload)
        self.assertIn("stars", payload)
        self.assertNotIn("grades", payload)                                        # strict classes are off until a parent opts in
        self.assertNotIn("health", payload)
        token = self.token()
        self.store.set_phone_settings(HH, KID, None, {"grades": True, "health": True, "timetable": False})
        payload = self.view(token)
        self.assertIn("grades", payload)
        self.assertIn("health", payload)
        self.assertNotIn("school", payload)
        self.assertIn("Vitamin D", [m["name"] for m in payload["health"]["meds"]])

    def test_grades_on_the_phone_carry_the_subject_type_and_the_weights(self):
        token = self.token()
        self.store.set_phone_settings(HH, KID, None, {"grades": True})
        grades = self.view(token)["grades"]
        self.assertEqual({s["kind"] for s in grades["subjects"]}, {"core", "minor"})
        self.assertEqual(grades["weights"], {"core_written_pct": 50, "minor_written_pct": 30, "elective_written_pct": 30})
        self.assertEqual(sorted(s["name"] for s in grades["subjects"]), ["Biology", "Geography", "German", "Maths", "Sport"])   # the lessons of the plan

    def test_the_payload_carries_no_ids_that_point_outside_the_child(self):
        text = json.dumps(self.view(self.token()))
        for forbidden in ('"member_id"', '"household_id"', "hh-meyer", "assignee"):
            self.assertNotIn(forbidden, text)

    def test_child_can_tick_a_chore_but_not_after_a_parent_decided(self):
        token = self.token()
        chores = self.view(token)["stars"]["chores"]
        open_chore = next(c for c in chores if not c["done"] and c["star"])
        routes.tick_chore(self.ctx, req(body={"done": True}, params={"id": open_chore["id"]}, token=token))
        self.assertTrue(next(c for c in self.view(token)["stars"]["chores"] if c["id"] == open_chore["id"])["done"])
        rewards = load_file_module(Path(__file__).parents[2] / "rewards" / "server" / "routes.py")
        rewards.set_outcome(self.ctx, req(body={"chore_id": open_chore["id"], "outcome": "well"}))
        with self.assertRaises(HTTPError) as caught:
            routes.tick_chore(self.ctx, req(body={"done": False}, params={"id": open_chore["id"]}, token=token))
        self.assertEqual(caught.exception.status, 409)

    def test_cannot_tick_someone_elses_chore(self):
        token = self.token()
        others = [c for c in self.store.list_chores_today(HH, datetime.now().date()) if c["assignee_id"] != KID]
        self.assertTrue(others)
        with self.assertRaises(HTTPError) as caught:
            routes.tick_chore(self.ctx, req(body={"done": True}, params={"id": others[0]["id"]}, token=token))
        self.assertEqual(caught.exception.status, 404)

    def test_http_pair_maps_failures_to_statuses_and_unpair_revokes(self):
        self.enable()
        pairing = self.store.create_phone_pairing(HH, KID)
        wrong = "000000" if pairing["code"] != "000000" else "111111"
        with self.assertRaises(HTTPError) as caught:
            routes.pair(self.ctx, req(body={"secret": pairing["secret"], "code": wrong}))
        self.assertEqual(caught.exception.status, 403)
        with self.assertRaises(HTTPError) as caught:
            routes.pair(self.ctx, req(body={"secret": pairing["secret"], "code": "12"}))
        self.assertEqual(caught.exception.status, 400)
        status, body = routes.pair(self.ctx, req(body={"secret": pairing["secret"], "code": pairing["code"][:3] + " " + pairing["code"][3:]}))
        self.assertEqual(status, 201)
        routes.unpair(self.ctx, req(token=body["token"]))
        with self.assertRaises(HTTPError):
            routes.view(self.ctx, req("GET", token=body["token"]))


class PhoneHomeworkTests(PhoneBase):
    def setUp(self):
        super().setUp()
        self.token = self.pair(datetime.now(timezone.utc))[1]["token"]

    def tasks(self):
        return {t["title"]: t for t in routes.view(self.ctx, req("GET", token=self.token))[1]["homework"]["tasks"]}

    def test_the_phone_sees_homework_and_all_the_childs_subjects_to_pick_from(self):
        payload = routes.view(self.ctx, req("GET", token=self.token))[1]
        self.assertIn("Worksheet 4: fractions", self.tasks())
        subjects = {x["name"]: x for x in payload["homework"]["subjects"]}
        self.assertEqual(sorted(subjects), ["Biology", "Geography", "German", "Maths", "Sport"])      # every type, straight from the plan
        self.assertEqual((subjects["Maths"]["kind"], subjects["Sport"]["kind"]), ("core", "minor"))
        self.assertTrue(all(x["code"] for x in subjects.values()))
        self.assertEqual(payload["subjects"], payload["homework"]["subjects"])                       # the catalogue the phone labels subjects with
        self.assertEqual(payload["homework"]["summary"]["due_tomorrow"], 1)

    def test_a_child_adds_ticks_and_removes_their_own_task_but_not_a_parents(self):
        due = (datetime.now().date() + timedelta(days=2)).isoformat()
        status, body = routes.add_homework(self.ctx, req(body={"kind": "test", "subject": "Maths", "title": "Fractions", "due_on": due}, token=self.token))
        self.assertEqual(status, 201)
        self.assertEqual(self.tasks()["Fractions"]["by"], "child")
        routes.tick_homework(self.ctx, req(body={"done": True}, params={"id": body["id"]}, token=self.token))
        self.assertTrue(self.tasks()["Fractions"]["done"])
        routes.remove_homework(self.ctx, req(params={"id": body["id"]}, token=self.token))
        self.assertNotIn("Fractions", self.tasks())
        parents = self.tasks()["Read chapter 3 and write a summary"]
        with self.assertRaises(HTTPError) as caught:
            routes.remove_homework(self.ctx, req(params={"id": parents["id"]}, token=self.token))
        self.assertEqual(caught.exception.status, 403)
        routes.tick_homework(self.ctx, req(body={"done": True}, params={"id": parents["id"]}, token=self.token))   # ticking a parent's one is fine

    def test_not_sharing_homework_removes_it_from_the_view_and_the_routes(self):
        self.store.set_phone_settings(HH, KID, None, {"homework": False})
        self.assertNotIn("homework", routes.view(self.ctx, req("GET", token=self.token))[1])
        with self.assertRaises(HTTPError) as caught:
            routes.add_homework(self.ctx, req(body={"kind": "test", "title": "x", "due_on": datetime.now().date().isoformat()}, token=self.token))
        self.assertEqual(caught.exception.status, 403)

    def test_the_subject_list_does_not_depend_on_sharing_the_timetable(self):
        self.store.set_phone_settings(HH, KID, None, {"timetable": False})
        payload = routes.view(self.ctx, req("GET", token=self.token))[1]
        self.assertEqual(len(payload["homework"]["subjects"]), 5)
        self.assertNotIn("school", payload)
        self.store.set_phone_settings(HH, KID, None, {"timetable": False, "homework": False, "grades": False})
        self.assertNotIn("subjects", routes.view(self.ctx, req("GET", token=self.token))[1])           # nothing that names subjects is shared

    def test_homework_must_name_one_of_the_childs_subjects_by_name_or_code(self):
        due = (datetime.now().date() + timedelta(days=2)).isoformat()
        with self.assertRaises(HTTPError) as caught:
            routes.add_homework(self.ctx, req(body={"kind": "homework", "subject": "Quidditch", "title": "x", "due_on": due}, token=self.token))
        self.assertEqual(caught.exception.status, 400)
        code = next(x["code"] for x in self.store.list_subjects(HH, KID) if x["name"] == "Maths")
        routes.add_homework(self.ctx, req(body={"kind": "homework", "subject": code.lower(), "title": "By code", "due_on": due}, token=self.token))
        routes.add_homework(self.ctx, req(body={"kind": "homework", "title": "No subject", "due_on": due}, token=self.token))
        self.assertEqual((self.tasks()["By code"]["subject"], self.tasks()["No subject"]["subject"]), ("Maths", None))   # the subject's own name is stored


class ParentRouteTests(PhoneBase):
    def test_starting_a_pairing_needs_the_gateway_and_returns_a_fragment_url(self):
        self.enable()
        import os
        os.environ.pop("CHIT_PHONE", None)
        with self.assertRaises(HTTPError) as caught:
            routes.start_pairing(self.ctx, req(body={"member_id": KID}))
        self.assertEqual(caught.exception.status, 409)
        os.environ.update(CHIT_PHONE="1", CHIT_PHONE_URL="http://192.0.2.7:8766")
        try:
            status, body = routes.start_pairing(self.ctx, req(body={"member_id": KID}))
        finally:
            os.environ.pop("CHIT_PHONE"); os.environ.pop("CHIT_PHONE_URL")
        self.assertEqual(status, 201)
        self.assertEqual(body["url"], "http://192.0.2.7:8766/#p=" + body["secret"])
        self.assertRegex(body["code"], r"^\d{6}$")

    def test_settings_never_return_secrets(self):
        self.pair()
        text = json.dumps(routes.settings(self.ctx, req("GET"))[1])
        self.assertIn("iPhone", text)
        for word in ("secret", "token", "code_hash", "secret_hash"):
            self.assertNotIn(word, text)


class GatewayTests(unittest.TestCase):
    def test_the_gateway_exposes_only_device_routes(self):
        full = build_router(load_manifests())
        narrow = gateway.device_router(full)
        paths = [p for _, p in narrow.routes] + [pattern for _, _, pattern, _ in narrow.patterns]
        self.assertTrue(paths)
        self.assertTrue(all(p.startswith(gateway.DEVICE_PREFIX) for p in paths), paths)
        for method, path in (("GET", "/api/kids/phone/settings"), ("POST", "/api/kids/phone/pairings"), ("PUT", "/api/kids/phone/settings/x"),
                             ("DELETE", "/api/kids/phone/devices/x"), ("GET", "/api/household/current"), ("GET", "/api/kids/health/meds"),
                             ("GET", "/api/kids/grades/overview"), ("GET", "/api/shell")):
            self.assertIsNone(narrow.resolve(method, path), path)
        self.assertIsNotNone(narrow.resolve("GET", "/api/kids/phone/device/view"))

    def test_the_gateway_serves_only_the_app_files(self):
        self.assertTrue(all((gateway.KID_APP / name).is_file() for name in gateway.STATIC_ALLOW), "an allowed file is missing")

import copy
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit

from chit_store import EncryptedHouseholdStore
from chit_store.testing import sqlite_only
from chit_store.cli import DEFAULT_SEED_DIR, export_household, seed_households

SEED = json.loads((DEFAULT_SEED_DIR / "meyer-family.json").read_text())


class HouseholdDocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "dev.db", plain=True)

    def tearDown(self):
        self.temp.cleanup()

    @sqlite_only
    def test_plain_mode_is_refused_in_production(self):
        from unittest.mock import patch
        with patch.dict("os.environ", {"CHIT_ENV": "production"}):
            with self.assertRaises(ValueError):
                EncryptedHouseholdStore(Path(self.temp.name) / "p.db", plain=True)

    def test_seed_is_idempotent_and_keeps_stable_ids(self):
        self.assertEqual(seed_households(self.store), ["hh-meyer"])
        self.assertEqual(seed_households(self.store), [])
        document = self.store.get_household_document("hh-meyer")
        self.assertEqual([m["client_id"] for m in document["members"]], ["nina", "jonas", "mila", "leo"])
        self.assertEqual(document["modules"], sorted(SEED["modules"]))
        mila = next(m for m in document["members"] if m["client_id"] == "mila")
        self.assertEqual(mila["modules"], ["kids", "planner"])
        leo = next(m for m in document["members"] if m["client_id"] == "leo")
        self.assertEqual(leo["profile"]["pickup_adult_client_ids"], ["nina", "jonas"])

    def test_commute_fields_persist_and_are_validated(self):
        seed_households(self.store)
        document = self.store.get_household_document("hh-meyer")
        mila = next(m for m in document["members"] if m["client_id"] == "mila")
        self.assertEqual(mila["profile"]["commute_mode"], "cycle")
        football = next(a for a in mila["profile"]["activities"] if a["name"] == "Football")
        self.assertEqual((football["commute_mode"], football["travel_minutes"], football["escort"], football["escort_adult_client_id"]),
                         ("car", 20, "parent", "jonas"))
        payload = {k: v for k, v in document.items() if k not in {"id", "created_at", "updated_at"}}
        for change, message in (
            (lambda p: p.update(commute_mode="rocket"), "commute mode"),
            (lambda p: p["activities"][0].update(escort="parent", escort_adult_client_id="leo"), "adult"),
            (lambda p: p["activities"][0].update(travel_minutes=-5), "travel minutes"),
        ):
            bad = copy.deepcopy(payload)
            change(next(m for m in bad["members"] if m["client_id"] == "mila")["profile"])
            with self.assertRaisesRegex(ValueError, message):
                self.store.update_household("hh-meyer", bad)
        self.assertEqual(self.store.get_household_document("hh-meyer")["members"][2]["profile"]["commute_mode"], "cycle")  # rolled back

    def test_document_round_trips(self):
        seed_households(self.store)
        first = self.store.get_household_document("hh-meyer")
        payload = {k: v for k, v in first.items() if k not in {"id", "created_at", "updated_at"}}
        self.store.update_household("hh-meyer", payload)
        second = self.store.get_household_document("hh-meyer")
        self.assertEqual({k: v for k, v in second.items() if k != "updated_at"},
                         {k: v for k, v in first.items() if k != "updated_at"})

    def test_edit_keeps_ids_chores_and_created_at(self):
        seed_households(self.store)
        before = self.store.get_household_document("hh-meyer")
        with self.store._connection() as connection:
            rule_id = connection.execute("SELECT id FROM chore_generation_rules").fetchone()[0]
        edited = copy.deepcopy(before)
        edited["household"]["name"] = "Meyer-Schmidt family"
        edited["members"][0]["name"] = "Nina M."
        edited["members"].append({"client_id": "new-1", "role": "child", "name": "Zoe", "profile": {}, "modules": None})
        edited["members"] = [m for m in edited["members"] if m["client_id"] != "leo"]
        edited["calendars"][0]["chore_enabled"] = False
        result = self.store.update_household("hh-meyer", edited)
        after = self.store.get_household_document("hh-meyer")
        self.assertEqual(after["household"]["name"], "Meyer-Schmidt family")
        self.assertEqual(after["created_at"], before["created_at"])
        self.assertEqual(after["members"][0]["client_id"], "nina")
        names = [m["name"] for m in after["members"]]
        self.assertIn("Zoe", names)
        self.assertNotIn("Leo", names)
        self.assertNotEqual(result["member_ids"]["new-1"], "new-1")
        self.assertFalse(after["calendars"][0]["chore_enabled"])
        with self.store._connection() as connection:
            enabled = connection.execute("SELECT enabled FROM chore_generation_rules WHERE id = ?", (rule_id,)).fetchone()
        self.assertEqual(enabled[0], 0)  # rule kept, just switched off

    def test_edit_can_change_owner_and_remove_old_owner(self):
        seed_households(self.store)
        doc = self.store.get_household_document("hh-meyer")
        doc["owner_client_id"] = "jonas"
        doc["members"] = [m for m in doc["members"] if m["client_id"] != "nina"]
        for member in doc["members"]:
            member["profile"] = {k: v for k, v in member["profile"].items() if "adult_client_ids" not in k}
        for calendar in doc["calendars"]:
            calendar["member_client_ids"] = [m for m in calendar["member_client_ids"] if m != "nina"]
        self.store.update_household("hh-meyer", doc)
        self.assertEqual(self.store.get_household_document("hh-meyer")["owner_client_id"], "jonas")

    def test_invalid_edit_rolls_back(self):
        seed_households(self.store)
        doc = self.store.get_household_document("hh-meyer")
        doc["household"]["name"] = "Should not persist"
        doc["members"][0]["role"] = "child"  # role change is rejected
        with self.assertRaises(ValueError):
            self.store.update_household("hh-meyer", doc)
        self.assertEqual(self.store.get_household_document("hh-meyer")["household"]["name"], "Meyer family")

    def test_member_cannot_enable_what_household_has_not(self):
        doc = copy.deepcopy(SEED)
        doc["members"][2]["modules"] = ["finance"]
        with self.assertRaises(ValueError):
            self.store.save_household_setup(doc, preserve_ids=True)

    def test_latest_household_is_newest_created_and_unaffected_by_edit(self):
        seed_households(self.store)
        text = json.dumps(SEED)
        for ident in ("nina", "jonas", "mila", "leo", "cal-bins", "cal-school"):
            text = text.replace('"%s"' % ident, '"%s-2"' % ident)  # ids are global: fixtures must not share them
        second = json.loads(text)
        second["household"]["id"] = "hh-second"
        second["household"]["name"] = "Second"
        self.store.save_household_setup(second, preserve_ids=True)
        self.assertEqual(self.store.latest_household_id(), "hh-second")
        doc = self.store.get_household_document("hh-meyer")
        self.store.update_household("hh-meyer", doc)
        self.assertEqual(self.store.latest_household_id(), "hh-second")

    def test_enablement_layers(self):
        seed_households(self.store)
        enablement = self.store.household_enablement("hh-meyer")
        self.assertEqual(enablement["modules"], set(SEED["modules"]))
        self.assertIsNone(enablement["members"]["nina"]["modules"])
        self.assertEqual(enablement["members"]["mila"]["modules"], {"planner", "kids"})

    def test_export_masks_private_urls(self):
        seed_households(self.store)
        doc = export_household(self.store, "latest")
        self.assertEqual(doc["household"]["id"], "hh-meyer")
        self.assertTrue(all("REPLACE-ME" in c["subscription_url"] for c in doc["calendars"]))
        kept = export_household(self.store, "hh-meyer", include_urls=True)
        self.assertEqual(kept["calendars"][0]["subscription_url"], "https://calendar.example/meyer/bins.ics")


class SeedLintTests(unittest.TestCase):
    def test_seed_files_only_use_example_hosts_and_load(self):
        with tempfile.TemporaryDirectory() as temp:
            store = EncryptedHouseholdStore(Path(temp) / "lint.db", plain=True)
            for path in DEFAULT_SEED_DIR.glob("*.json"):
                document = json.loads(path.read_text())
                for calendar in document["calendars"]:
                    host = urlsplit(calendar["subscription_url"]).hostname or ""
                    self.assertTrue(host.endswith(".example") or host.endswith(".example.com") or host == "example.com",
                                    "%s: private-looking feed host %s" % (path.name, host))
            seed_households(store)


if __name__ == "__main__":
    unittest.main()


class AvatarAndLocationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "a.db", plain=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_avatars_and_colours_round_trip(self):
        seed_households(self.store)
        doc = self.store.get_household_document("hh-meyer")
        mila = next(m for m in doc["members"] if m["client_id"] == "mila")
        self.assertEqual((mila["avatar"], mila["color"]), ("k2", "#ff8fb8"))
        self.assertEqual(mila["profile"]["dropoff_time"], "08:00")
        self.assertEqual((doc["household"]["latitude"], doc["household"]["longitude"]), (48.1374, 11.5755))

    def test_defaults_are_assigned_and_distinct(self):
        document = copy.deepcopy(SEED)
        for member in document["members"]:
            member.pop("avatar"), member.pop("color")
        self.store.save_household_setup(document, preserve_ids=True)
        members = self.store.get_household_document("hh-meyer")["members"]
        self.assertEqual(len({m["color"] for m in members}), 4)
        self.assertTrue(all(m["avatar"].startswith("a" if m["role"] == "adult" else "k") for m in members))

    def test_an_adult_cannot_pick_a_child_avatar(self):
        document = copy.deepcopy(SEED)
        document["members"][0]["avatar"] = "k1"
        with self.assertRaises(ValueError):
            self.store.save_household_setup(document, preserve_ids=True)

    def test_bad_colour_and_coordinates_are_rejected(self):
        for mutate in (lambda d: d["members"][0].update(color="red"),
                       lambda d: d["household"].update(latitude=123),
                       lambda d: d["household"].update(longitude="east")):
            document = copy.deepcopy(SEED)
            mutate(document)
            with self.assertRaises(ValueError):
                self.store.save_household_setup(document, preserve_ids=True)


class HouseholdTypeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = EncryptedHouseholdStore(Path(self.temp.name) / "t.db", plain=True)

    def tearDown(self):
        self.temp.cleanup()

    def _doc(self, kind=None, adults=2, children=0):
        document = copy.deepcopy(SEED)
        keep = [m for m in document["members"] if m["role"] == "adult"][:adults] + \
               [m for m in document["members"] if m["role"] == "child"][:children]
        document["members"] = keep
        document["owner_client_id"] = keep[0]["client_id"]
        document["modules"] = None
        for calendar in document.get("calendars", []):
            calendar["member_client_ids"] = []
            calendar["chore_assignee_client_ids"] = []
        for member in keep:
            profile = member.get("profile") or {}
            for key in ("pickup_adult_client_ids", "dropoff_adult_client_ids"):
                profile[key] = [i for i in profile.get(key, []) if i in {m["client_id"] for m in keep}]
            for activity in profile.get("activities", []) or []:
                if activity.get("escort_adult_client_id") not in {m["client_id"] for m in keep}:
                    activity["escort_adult_client_id"] = None
        if kind:
            document["household"]["type"] = kind
        return document

    def test_type_is_derived_for_documents_that_do_not_say(self):
        seed_households(self.store)
        self.assertEqual(self.store.get_household_document("hh-meyer")["household"]["type"], "family")

    def test_each_type_allows_only_its_members(self):
        cases = [("single", 1, 0, True), ("single", 2, 0, False), ("single", 1, 1, False),
                 ("couple", 2, 0, True), ("couple", 1, 0, False), ("couple", 2, 1, False),
                 ("shared", 3, 0, True), ("shared", 2, 1, False),
                 ("family", 2, 2, True), ("family", 1, 1, True), ("family", 2, 0, True)]
        for kind, adults, children, allowed in cases:
            document = self._doc(kind, adults, children)
            with self.subTest(kind=kind, adults=adults, children=children):
                if allowed:
                    self.store._parse_setup(document)
                else:
                    with self.assertRaises(ValueError):
                        self.store._parse_setup(document)

    def test_unknown_type_is_rejected_and_type_round_trips(self):
        with self.assertRaises(ValueError):
            self.store._parse_setup(self._doc("castle"))
        document = self._doc("couple", 2, 0)
        document["household"]["id"] = "hh-couple"
        self.store.save_household_setup(document, preserve_ids=True)
        self.assertEqual(self.store.get_household_document("hh-couple")["household"]["type"], "couple")

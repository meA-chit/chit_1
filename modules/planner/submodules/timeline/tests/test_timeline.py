from pathlib import Path
import copy
import json
import unittest

from chit_server.loader import load_file_module

routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
SEED = json.loads((Path(__file__).parents[5] / "seed" / "households" / "meyer-family.json").read_text())


def document():
    return copy.deepcopy({"members": SEED["members"]})  # tests mutate it; never share state


def lane(lanes, member_id):
    return next(item for item in lanes if item["member_id"] == member_id)


class TimelineTests(unittest.TestCase):
    def test_tuesday_routines(self):
        lanes = routes.build_lanes(document(), "tuesday")
        jonas = lane(lanes, "jonas")["blocks"]
        titles = [b["title"] for b in jonas]
        self.assertIn("Work · office", titles)
        self.assertEqual(titles.count("Commute"), 2)       # office days have a commute each way
        self.assertNotIn("Drop off Leo", titles)            # Nina does the drop-offs in the sample household
        nina = lane(lanes, "nina")["blocks"]
        self.assertIn("Drop off Leo", [b["title"] for b in nina])
        self.assertNotIn("Drop off Mila", [b["title"] for b in nina])   # Mila cycles on her own
        self.assertIn("Work · home", [b["title"] for b in nina])
        self.assertNotIn("Commute", [b["title"] for b in nina])   # working from home: no commute
        self.assertIn("Pick up Leo", [b["title"] for b in nina])   # first listed pickup adult
        mila = lane(lanes, "mila")["blocks"]
        self.assertEqual((mila[0]["start"], mila[0]["end"], mila[0]["kind"]), ("08:00", "15:30", "school"))
        trips = {b["title"]: (b["start"], b["end"], b["kind"]) for b in mila if b["kind"] == "commute"}
        self.assertEqual(trips["Cycle to school"], ("07:45", "08:00", "commute"))   # independent: on her own lane
        self.assertEqual(trips["Cycle home"], ("15:30", "15:45", "commute"))

    def test_no_work_block_when_the_day_has_no_location(self):
        doc = document()
        doc["members"][0]["profile"]["work_days"] = {}
        titles = [b["title"] for b in lane(routes.build_lanes(doc, "tuesday"), "nina")["blocks"]]
        self.assertFalse([t for t in titles if t.startswith("Work")])   # trips remain, work is not invented

    def test_activity_only_on_its_day(self):
        self.assertNotIn("Swimming", [b["title"] for b in lane(routes.build_lanes(document(), "tuesday"), "mila")["blocks"]])
        wed = lane(routes.build_lanes(document(), "wednesday"), "mila")["blocks"]
        self.assertIn("Swimming", [b["title"] for b in wed])
        swim = next(b for b in wed if b["title"] == "Swimming")
        self.assertEqual(swim["icon"], "🏊")                                              # an activity carries the icon of its name
        self.assertNotIn("icon", next(b for b in wed if b["kind"] == "commute"))          # blocks that are not activities have none

    def test_independent_activity_has_the_childs_own_commute(self):
        wed = {b["title"]: (b["start"], b["end"]) for b in lane(routes.build_lanes(document(), "wednesday"), "mila")["blocks"]}
        self.assertEqual(wed["Cycle to Swimming"], ("16:50", "17:00"))
        self.assertEqual(wed["Cycle home"], ("18:00", "18:10"))

    def test_parent_accompanied_activity_puts_the_trips_on_the_parent(self):
        lanes = routes.build_lanes(document(), "saturday")
        jonas = {b["title"]: (b["start"], b["end"], b["kind"]) for b in lane(lanes, "jonas")["blocks"]}
        self.assertEqual(jonas["Take Mila to Football"], ("09:40", "10:00", "dropoff"))
        self.assertEqual(jonas["Pick up Mila"], ("11:30", "11:50", "pickup"))
        self.assertEqual([b["title"] for b in lane(lanes, "mila")["blocks"]], ["Football"])   # driven: no trip of her own

    def test_no_commute_entered_means_no_trip_is_invented(self):
        doc = document()
        for activity in next(m for m in doc["members"] if m["client_id"] == "mila")["profile"]["activities"]:
            activity["travel_minutes"] = None
        wed = [b["title"] for b in lane(routes.build_lanes(doc, "wednesday"), "mila")["blocks"]]
        self.assertEqual(wed, ["Swimming"])

    def test_missing_dropoff_time_leaves_the_start_unknown(self):
        doc = document()
        for member in doc["members"]:
            if member["client_id"] == "mila":
                member["profile"].pop("dropoff_time")
        block = lane(routes.build_lanes(doc, "tuesday"), "mila")["blocks"][0]
        self.assertIsNone(block["start"])       # never invented
        self.assertEqual(block["end"], "15:30")


if __name__ == "__main__":
    unittest.main()

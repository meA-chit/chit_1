from datetime import date, timedelta
from io import BytesIO
import unittest
from unittest.mock import patch

from pathlib import Path

from chit_server.loader import load_file_module

reader = load_file_module(Path(__file__).parents[1] / "server" / "reader.py")


class CalendarFeedTests(unittest.TestCase):
    def test_reads_near_term_all_day_and_timed_events(self):
        tomorrow = date.today() + timedelta(days=1)
        next_day = tomorrow + timedelta(days=1)
        calendar_data = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "BEGIN:VEVENT\r\n"
            "UID:waste-1\r\n"
            "DTSTART;VALUE=DATE:%s\r\n"
            "DTEND;VALUE=DATE:%s\r\n"
            "SUMMARY:Restmüll\r\n"
            "END:VEVENT\r\n"
            "BEGIN:VEVENT\r\n"
            "UID:activity-1\r\n"
            "DTSTART:%sT173000Z\r\n"
            "DTEND:%sT183000Z\r\n"
            "SUMMARY:Swimming\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        ) % (
            tomorrow.strftime("%Y%m%d"),
            next_day.strftime("%Y%m%d"),
            tomorrow.strftime("%Y%m%d"),
            tomorrow.strftime("%Y%m%d"),
        )

        class Response(BytesIO):
            status = 200

        with patch.object(reader, "urlopen", return_value=Response(calendar_data.encode("utf-8"))):
            events = reader.read_calendar_events("webcal://calendar.example/private.ics", "Europe/Berlin")

        self.assertEqual([event["title"] for event in events], ["Restmüll", "Swimming"])
        self.assertTrue(events[0]["all_day"])
        self.assertFalse(events[1]["all_day"])
        self.assertIn("T19:30:00+02:00", events[1]["start"])


if __name__ == "__main__":
    unittest.main()

class AgendaContractTests(unittest.TestCase):
    """The agenda is a public read API (planner contracts.md): events say which people their calendar belongs to, by name and by id."""

    def test_events_carry_member_ids_of_the_calendar(self):
        import tempfile
        from chit_server.router import Context, Request
        from chit_server.seed import seed_all
        from chit_store import EncryptedHouseholdStore
        routes = load_file_module(Path(__file__).parents[1] / "server" / "routes.py")
        with tempfile.TemporaryDirectory() as temp:
            store = EncryptedHouseholdStore(Path(temp) / "c.db", plain=True)
            seed_all(store)
            sources = {s["name"]: s for s in store.latest_household_calendar_sources()["sources"]}
            self.assertEqual(sources["School calendar"]["member_ids"], ["mila", "nina"])
            event = {"title": "Trip", "start": "2026-10-09T08:00:00+02:00", "end": "2026-10-09T09:00:00+02:00", "all_day": False}
            with patch.object(routes.reader, "read_calendar_events", return_value=[dict(event)]):
                payload = routes.agenda(Context(store=store), Request("GET", "/x", {}, ""))[1]
            school = [e for e in payload["events"] if e["source"] == "School calendar"][0]
            self.assertEqual((school["members"], school["member_ids"]), (["Mila", "Nina Meyer"], ["mila", "nina"]))
            self.assertEqual(school["icon"], "🚌")                                       # "Trip": the icon comes from the title, falling back to the category

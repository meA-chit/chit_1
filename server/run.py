from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import date, datetime, time, timedelta, timezone
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from chit_store import EncryptedHouseholdStore
from icalendar import Calendar


MAX_REQUEST_BYTES = 1_048_576
MAX_CALENDAR_BYTES = 2_000_000
CALENDAR_LOOKAHEAD_DAYS = 21
SETUP_PAGE = PROJECT_ROOT / "dashboard" / "household-setup.html"
CALENDAR_HOME_PAGE = PROJECT_ROOT / "dashboard" / "calendar-home.html"
HOME_PAGE = PROJECT_ROOT / "dashboard" / "home.html"
# Static directories served without auth (read-only public assets)
_STATIC_ROOTS = {
    "/js/": PROJECT_ROOT / "js",
    "/css/": PROJECT_ROOT / "css",
    "/assets/": PROJECT_ROOT / "assets",
}
_STATIC_MIME = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".html": "text/html; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
}
def read_calendar_events(subscription_url: str, timezone_name: str) -> list[dict[str, str | bool]]:
    local_zone = ZoneInfo(timezone_name)
    parts = urlsplit(subscription_url)
    if parts.scheme.lower() == "webcal":
        subscription_url = urlunsplit(("https", parts.netloc, parts.path, parts.query, ""))
    request = Request(subscription_url, headers={
        "User-Agent": "Chit-Calendar-Reader/1.0",
        "Accept": "text/calendar, application/ics, text/plain;q=0.8, */*;q=0.5",
    })
    with urlopen(request, timeout=12) as response:
        if response.status < 200 or response.status >= 300:
            raise ValueError("calendar provider returned an unsuccessful response")
        payload = response.read(MAX_CALENDAR_BYTES + 1)
    if len(payload) > MAX_CALENDAR_BYTES:
        raise ValueError("calendar response is larger than the 2 MB limit")
    calendar = Calendar.from_ical(payload)
    start_date = datetime.now(local_zone).date()
    end_date = start_date + timedelta(days=CALENDAR_LOOKAHEAD_DAYS)
    events = []
    for component in calendar.walk("VEVENT"):
        start_value = component.get("DTSTART")
        if start_value is None:
            continue
        start_value = start_value.dt
        is_all_day = isinstance(start_value, date) and not isinstance(start_value, datetime)
        if is_all_day:
            event_date = start_value
            if event_date < start_date or event_date > end_date:
                continue
            start_at = datetime.combine(event_date, time.min)
            end_value = component.get("DTEND")
            end_at = datetime.combine(end_value.dt, time.min) if end_value else start_at + timedelta(days=1)
        else:
            event_at = start_value
            if event_at.tzinfo is None:
                event_at = event_at.replace(tzinfo=timezone.utc)
            event_at = event_at.astimezone(local_zone)
            if event_at.date() < start_date or event_at.date() > end_date:
                continue
            start_at = event_at
            end_value = component.get("DTEND")
            end_at = end_value.dt if end_value else event_at
            if isinstance(end_at, date) and not isinstance(end_at, datetime):
                end_at = datetime.combine(end_at, time.min)
            elif end_at.tzinfo is None:
                end_at = end_at.replace(tzinfo=timezone.utc)
            end_at = end_at.astimezone(local_zone)
        summary = str(component.get("SUMMARY", "Untitled event")).strip()
        events.append({
            "title": summary or "Untitled event",
            "start": start_at.isoformat(),
            "end": end_at.isoformat(),
            "all_day": is_all_day,
        })
    events.sort(key=lambda event: (event["start"], event["title"]))
    return events[:100]


class ChitHandler(BaseHTTPRequestHandler):
    server_version = "ChitLocal/0.1"

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path in {"/", "/dashboard/household-setup.html", "/dashboard/home.html"}:
            if path == "/dashboard/home.html":
                self._send_html(HOME_PAGE.read_bytes())
            else:
                self._send_html(SETUP_PAGE.read_bytes())
            return
        if path == "/dashboard/calendar-home.html":
            self._send_html(CALENDAR_HOME_PAGE.read_bytes())
            return
        if path == "/api/health":
            self._send_json(200, {"status": "ready", "storage": "encrypted-sqlite"})
            return
        if path == "/api/home/calendar":
            self._send_home_calendar()
            return
        if path == "/api/home/summary":
            self._send_home_summary()
            return
        # Serve static assets (js/, css/, assets/) without auth
        for prefix, root in _STATIC_ROOTS.items():
            if path.startswith(prefix):
                relative = path[len(prefix):]
                # Reject path traversal
                file_path = (root / relative).resolve()
                if not str(file_path).startswith(str(root.resolve())):
                    self._send_json(403, {"error": "Forbidden"})
                    return
                if file_path.is_file():
                    suffix = file_path.suffix.lower()
                    mime = _STATIC_MIME.get(suffix, "application/octet-stream")
                    content = file_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", str(len(content)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(content)
                    return
                self._send_json(404, {"error": "Not found"})
                return
        self._send_json(404, {"error": "Not found"})

    def _send_home_calendar(self) -> None:
        household = self.server.store.latest_household_calendar_sources()
        if household is None:
            self._send_json(200, {"state": "unavailable", "reason": "unconfigured", "events": []})
            return
        if not household["sources"]:
            self._send_json(200, {
                "state": "unavailable", "reason": "unconfigured", "household": household["name"], "events": []
            })
            return
        events = []
        summaries = []
        any_error = False
        for source in household["sources"]:
            try:
                source_events = read_calendar_events(source["subscription_url"], household["timezone"])
                self.server.store.record_calendar_check(source["id"], "available")
                for event in source_events:
                    event["source"] = source["name"]
                    event["category"] = source["category"]
                    event["members"] = source["members"]
                    events.append(event)
                summaries.append({"name": source["name"], "state": "available", "event_count": len(source_events)})
            except Exception as error:
                any_error = True
                state = "stale" if source["last_checked_at"] else "unavailable"
                self.server.store.record_calendar_check(source["id"], state)
                self.log_error("calendar read failed for source %s (%s)", source["id"], type(error).__name__)
                summaries.append({"name": source["name"], "state": state, "event_count": 0})
        events.sort(key=lambda event: (event["start"], event["title"]))
        state = "partial" if any_error and events else "unavailable" if any_error else "available"
        self._send_json(200, {
            "state": state,
            "household": household["name"],
            "range_days": CALENDAR_LOOKAHEAD_DAYS,
            "sources": summaries,
            "events": events[:100],
        })

    def _send_home_summary(self) -> None:
        summary = self.server.store.latest_household_summary()
        if summary is None:
            self._send_json(200, {"state": "unconfigured"})
            return
        self._send_json(200, {"state": "configured", "household": summary})

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if path != "/api/households/setup":
            self._send_json(404, {"error": "Not found"})
            return
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            self._send_json(415, {"error": "Content-Type must be application/json"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length"})
            return
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Request body must be between 1 byte and 1 MiB"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = self.server.store.save_household_setup(payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON"})
            return
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return
        except Exception as error:
            self.log_error("setup save failed: %s: %s", type(error).__name__, error)
            self._send_json(400, {"error": "Setup could not be saved; check required fields and assignments"})
            return
        self._send_json(201, result)


    def log_message(self, format: str, *args: object) -> None:
        message = format % args
        if "POST" in message:
            message = message.split(" HTTP/")[0] + " [request details omitted]"
        super().log_message("%s", message)

    def _send_html(self, content: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status: int, content: dict[str, object]) -> None:
        body = json.dumps(content).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    store = EncryptedHouseholdStore()
    server = ThreadingHTTPServer(("127.0.0.1", 8765), ChitHandler)
    server.daemon_threads = True
    server.store = store
    print("Chit setup: http://127.0.0.1:8765/dashboard/household-setup.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping Chit local server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

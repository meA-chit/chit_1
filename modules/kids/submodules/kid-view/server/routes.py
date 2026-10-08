"""A child's own phone (kids/kid-view, ADR-0012).

Two halves with different audiences:
  /api/kids/phone/*          parent management: enable the phone view, choose what it shows, pair, revoke.
  /api/kids/phone/device/*   what the phone itself calls, with a device token. This is the ONLY part the phone gateway exposes.

The device payload is built on the server from the parent's settings: a section the parent did not share is not in
the response at all, so hiding is not a client-side courtesy.
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import re
import threading
import time

from chit_server import gateway
from chit_server.icons import icon_for
from chit_server.loader import load_file_module
from chit_server.router import HTTPError

shared = Path(__file__).parents[3] / "shared"
api = load_file_module(shared / "api.py")
grades = load_file_module(shared / "grades.py")
meds = load_file_module(shared / "meds.py")
homework = load_file_module(shared / "homework.py")
plan = load_file_module(shared / "plan.py")

TOKEN = re.compile(r"^[A-Za-z0-9_-]{16,128}$")
CODE = re.compile(r"^[0-9 ]{6,7}$")
LINK = re.compile(r"^[A-Za-z0-9 -]{8,10}$")


# ---------- parent management ----------
def _children(ctx):
    household_id, document, now = api.need_household(ctx)
    return household_id, api.children(document), now


def settings(ctx, request):
    household_id, kids, now = _children(ctx)
    store = ctx.store
    return 200, {
        "gateway": gateway.enabled(), "phone_url": gateway.base_url(),
        "children": [{
            "member_id": kid["client_id"], "name": kid["name"], **store.phone_settings(household_id, kid["client_id"]),
            "devices": store.list_phone_devices(household_id, kid["client_id"]),
            "pairing": store.active_phone_pairing(household_id, kid["client_id"]),
        } for kid in kids],
    }


def update_settings(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    data = api.body(request)
    result = api.checked(ctx.store.set_phone_settings, household_id, request.params["id"], data.get("enabled"), data.get("share"))
    return 200, {"member_id": request.params["id"], **result}


def start_pairing(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    base = gateway.base_url()
    if base is None:
        raise HTTPError(409, "The phone gateway is off. Start the hub with CHIT_PHONE=1 (see apps/kid-app/README.md).")
    member = str(api.body(request).get("member_id", ""))
    pairing = api.checked(ctx.store.create_phone_pairing, household_id, member)
    # The secret rides in the URL fragment: it is never sent to a server or written to an access log.
    return 201, {**pairing, "url": "%s/#p=%s" % (base, pairing["secret"]), "phone_url": base}


def cancel_pairing(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    ctx.store.cancel_phone_pairing(household_id, request.params["id"])
    return 200, {"member_id": request.params["id"], "cancelled": True}


def revoke_device(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    api.checked(ctx.store.revoke_phone_device, household_id, request.params["id"])
    return 200, {"id": request.params["id"], "revoked": True}


# ---------- the phone ----------
def _device(ctx, request):
    header = request.headers.get("authorization", "")
    token = header[7:].strip() if header[:7].lower() == "bearer " else ""
    device = ctx.store.phone_device_for_token(token) if TOKEN.match(token) else None
    if device is None:
        raise HTTPError(401, "This phone is not paired (any more). Ask a parent for a new QR code.")
    return device


def pair(ctx, request):
    data = api.body(request)
    secret, link, code = str(data.get("secret", "")), str(data.get("link", "")), str(data.get("code", ""))
    if not CODE.match(code):
        raise HTTPError(400, "Enter the 6 digits shown on your parent's screen.")
    if secret and not TOKEN.match(secret) or not secret and not LINK.match(link):
        raise HTTPError(400, "Scan the QR code again, or type the link code from your parent's screen.")
    try:
        result = ctx.store.complete_phone_pairing(secret or None, code, str(data.get("label") or "") or None, link=link or None)
    except ctx.store.PairingError as error:
        status = {"invalid": 410, "locked": 423, "wrong_code": 403, "throttled": 429}[error.reason]
        message = str(error) + (" %d tries left." % error.attempts_left if error.attempts_left else "")
        raise HTTPError(status, message) from None
    return 201, {"token": result["token"]}


def handoff(ctx, request):
    device = _device(ctx, request)
    return 201, {"handoff": ctx.store.create_phone_handoff(device["device_id"])}


def exchange(ctx, request):
    handoff_token = str(api.body(request).get("handoff", ""))
    token = ctx.store.exchange_phone_handoff(handoff_token) if TOKEN.match(handoff_token) else None
    if token is None:
        raise HTTPError(410, "This link has expired. Ask a parent for a new QR code.")
    return 200, {"token": token}


def unpair(ctx, request):
    device = _device(ctx, request)
    api.checked(ctx.store.revoke_phone_device, device["household_id"], device["device_id"])
    return 200, {"unpaired": True}


def manifest(ctx, request):
    """Web app manifest whose start_url carries a one-use handoff, so the Home Screen app can pick up the pairing."""
    handoff_token = request.query.get("h", "")
    start = "/?h=%s" % handoff_token if TOKEN.match(handoff_token) else "/"
    return 200, {"name": "Chit Kids", "short_name": "Chit", "start_url": start, "scope": "/", "display": "standalone",
                 "background_color": "#f5faf8", "theme_color": "#00695c",
                 "icons": [{"src": "/icon-180.png", "sizes": "180x180", "type": "image/png"},
                           {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]}


def view(ctx, request):
    device = _device(ctx, request)
    store, household_id, member = ctx.store, device["household_id"], device["member_id"]
    _, document, now = api.latest(ctx)
    kid = next((k for k in api.children(document) if k["client_id"] == member), None)
    if kid is None:
        raise HTTPError(401, "This phone is not paired (any more). Ask a parent for a new QR code.")
    share = store.phone_settings(household_id, member)["share"]
    today = now.date()
    payload = {
        "state": "manual", "date": today.isoformat(), "now": now.strftime("%H:%M"), "weekday": today.weekday(),
        "child": {"name": kid["name"].split(" ")[0], "avatar": kid.get("avatar"), "color": kid.get("color")},
        "share": share, "source": "entered by your parents in Chit",
    }
    if share["timetable"] or share["homework"] or share["grades"]:
        payload["subjects"] = _subjects(store, household_id, member)     # name, code and type: lets the phone label a subject the same way everywhere
    if share["timetable"]:
        payload["school"] = {"slots": store.list_school_slots(household_id, member)}
    if share["reminders"]:
        def mine(day):
            states = store.reminder_states_for_day(household_id, day, member)     # this child's own done / not relevant marks
            return [{"id": r["id"], "title": r["title"], "day_part": r["day_part"], "state": states.get(r["id"])} for r in store.list_reminders_for_day(household_id, day)
                    if not r["skipped"] and r["member_id"] in (None, member)]
        payload["reminders"] = {"today": mine(today), "tomorrow": mine(today + timedelta(days=1))}
    if share["stars"]:
        payload["stars"] = _stars(store, household_id, member, today)
    if share["homework"]:
        payload["homework"] = _homework(store, household_id, member, today)
    if share["activities"]:
        payload["activities"] = _activities(ctx, household_id, document, kid, today)
    if share["bag"]:
        payload["bag"] = _bag(ctx, household_id, member, today, share["timetable"], share["reminders"], document)
    if share["grades"]:
        payload["grades"] = _grades(store, household_id, member)
    if share["health"]:
        payload["health"] = _health(store, household_id, member, document, now)
    return 200, payload


def _stars(store, household_id, member, today):
    star_ids = store.star_chore_ids(household_id)
    outcomes = store.chore_outcomes(household_id, today)
    days = store.star_days(household_id, member, "0000-01-01")
    monday = today - timedelta(days=today.weekday())
    week = [days.get((monday + timedelta(days=i)).isoformat(), 0) for i in range(7)]
    goals = []
    for goal in store.list_goals(household_id):
        if goal["member_id"] != member:
            continue
        have = sum(n for day, n in days.items() if day >= goal["started_on"])
        goals.append({"id": goal["id"], "title": goal["title"], "note": goal["note"], "cost": goal["cost"], "have": have,
                      "reached": have >= goal["cost"], "approved": goal["status"] == "approved"})
    chores = [{"id": c["id"], "title": c["title"], "day_part": c.get("day_part"), "done": c["done"], "star": c["id"] in star_ids,
               "outcome": outcomes.get(c["id"])}
              for c in store.list_chores_today(household_id, today) if c["assignee_id"] == member and not c["skipped"]]
    return {"total": sum(days.values()), "week": week, "goals": goals, "chores": chores}


def _subjects(store, household_id, member):
    """The child's subjects (lessons in their plan): name, code and type. The add-homework form picks from these, nothing is typed."""
    return [{"name": x["name"], "code": x["code"], "kind": x["kind"]} for x in store.list_subjects(household_id, member)]


def _homework(store, household_id, member, today):
    tasks = [homework.view(t, today) for t in store.list_tasks(household_id, member, today)]
    return {"tasks": tasks, "summary": homework.summarize(tasks, today), "subjects": _subjects(store, household_id, member)}


# ---------- activities, calendar events, bag (K1, K2) ----------
_EVENTS: dict = {}               # household id -> (fetched at, planner agenda payload)
_EVENTS_TTL = 600                # seconds: the agenda reads every calendar feed over the network, the phone refreshes every minute
_EVENTS_LOCK = threading.Lock()
_REFRESHING: set = set()


def clear_events_cache():
    with _EVENTS_LOCK:
        _EVENTS.clear()
        _REFRESHING.clear()


def _fetch_agenda(ctx, household_id):
    try:
        agenda = ctx.read("/api/planner/calendar/agenda") if ctx.read else {"state": "unavailable", "events": []}
    except Exception:
        agenda = {"state": "unavailable", "events": []}
    with _EVENTS_LOCK:
        # a failed read never replaces a good one: keep the last events and say they are stale
        old = _EVENTS.get(household_id)
        if agenda.get("state") in ("unavailable",) and old and old[1].get("events"):
            agenda = {**old[1], "state": "stale"}
        _EVENTS[household_id] = (time.monotonic(), agenda)
        _REFRESHING.discard(household_id)
    return agenda


def _agenda(ctx, household_id):
    """Cached planner agenda (public read API). A stale copy is served at once and refreshed in the background."""
    with _EVENTS_LOCK:
        hit = _EVENTS.get(household_id)
        fresh = hit is not None and time.monotonic() - hit[0] < _EVENTS_TTL
        if hit is not None and not fresh and household_id not in _REFRESHING:
            _REFRESHING.add(household_id)
            threading.Thread(target=_fetch_agenda, args=(ctx, household_id), daemon=True).start()
    return hit[1] if hit is not None else _fetch_agenda(ctx, household_id)


def _activities(ctx, household_id, document, kid, today):
    names = {m["client_id"]: m["name"].split(" ")[0] for m in document["members"]}
    agenda = _agenda(ctx, household_id)
    unconfigured = agenda.get("state") == "unavailable" and agenda.get("reason") == "unconfigured"
    weekly = plan.weekly_activities(kid["profile"].get("activities"), names)
    events = plan.child_events(agenda, kid["client_id"], today)
    for item in weekly:                                   # the football for "Football training", the pool for "Swimming" ...
        item["icon"] = icon_for(item["name"], "sport_activity")
    for item in events:
        item["icon"] = icon_for(item["title"], item.get("category"))
    return {"weekly": weekly, "events": events,
            "events_state": "unconfigured" if unconfigured else agenda.get("state", "unavailable"),
            "checked_at": agenda.get("checked_at")}


def _bag(ctx, household_id, member, today, with_timetable, with_reminders, document):
    store = ctx.store
    items = store.list_bag_items(household_id, member)
    suggestions_for = sorted({i["subject"] for i in items})
    if not with_timetable:
        return {"available": False, "reason": "timetable_not_shared", "days": [], "items": items}
    slots = store.list_school_slots(household_id, member)
    days = []
    for day in [today, plan.next_school_day(slots, today)]:
        titles = plan.school_day(slots, day) if day else []
        if not titles or any(d["date"] == day.isoformat() for d in days):
            continue
        states = store.reminder_states_for_day(household_id, day, member)
        reminders = [{**r, "state": states.get(r["id"])} for r in store.list_reminders_for_day(household_id, day)
                     if not r["skipped"] and r["member_id"] in (None, member)] if with_reminders else []
        tasks = [homework.view(t, today) for t in store.list_tasks(household_id, member, today)]
        kid = next((k for k in api.children(document) if k["client_id"] == member), {"profile": {}})
        acts = [a["name"] for a in plan.weekly_activities(kid["profile"].get("activities"), {}) if day.weekday() in a["weekdays"]]
        ticked = store.list_bag_ticks(member, [day])[day.isoformat()]
        entries = plan.derive_bag(titles, items, reminders, tasks, acts, day, ticked)
        days.append({"date": day.isoformat(), "weekday": day.weekday(), "items": entries, "ready": bool(entries) and all(e["ticked"] for e in entries)})
    return {"available": bool(days), "reason": None if days else "no_school_days", "days": days, "items": items, "subjects": suggestions_for}


def _bag_shared(ctx, device):
    if not ctx.store.phone_settings(device["household_id"], device["member_id"])["share"]["bag"]:
        raise HTTPError(403, "The bag list is not shared with this phone")


def tick_bag(ctx, request):
    device = _device(ctx, request)
    _bag_shared(ctx, device)
    data = api.body(request)
    if not isinstance(data.get("done"), bool):
        raise HTTPError(400, "done must be true or false")
    day = api.parse_day(data.get("date"), api.latest(ctx)[2], past_days=1, future_days=7)
    api.checked(ctx.store.set_bag_tick, device["member_id"], day, data.get("key"), data["done"])
    return 200, {"date": day.isoformat(), "key": data.get("key"), "done": data["done"]}


def add_bag_item(ctx, request):
    device = _device(ctx, request)
    _bag_shared(ctx, device)
    data = api.body(request)
    item_id = api.checked(ctx.store.add_bag_item, device["household_id"], device["member_id"], data.get("subject"), data.get("label"), "child")
    return 201, {"id": item_id}


def remove_bag_item(ctx, request):
    device = _device(ctx, request)
    _bag_shared(ctx, device)
    api.checked(ctx.store.delete_bag_item, device["household_id"], request.params["id"], device["member_id"])
    return 200, {"id": request.params["id"], "removed": True}


def _grades(store, household_id, member):
    weights = store.get_grade_weights(household_id)
    subjects = []
    for subject in store.list_subjects_with_grades(household_id, member):
        average = grades.subject_average(subject["kind"], subject["grades"], weights)
        if average["average"] is None:
            continue
        subjects.append({"name": subject["name"], "code": subject["code"], "kind": subject["kind"], "average": average["average"],
                         "written_average": average["written"], "oral_average": average["oral"],
                         "grades": [{"type": g["grade_type"], "grade": g["grade"], "given_on": g["given_on"], "note": g["note"]} for g in subject["grades"]]})
    overall = round(sum(s["average"] for s in subjects) / len(subjects), 2) if subjects else None
    return {"subjects": subjects, "overall": overall, "weights": weights, "scale": "1 (best) to 6"}


def _health(store, household_id, member, document, now):
    today = now.date()
    since = (today - timedelta(days=6)).isoformat()
    names = {m["client_id"]: m["name"].split(" ")[0] for m in document["members"]}
    out = []
    for med in store.list_meds(household_id, member, since):
        week = [{"day": (today - timedelta(days=6 - i)).isoformat(), "due": meds.due_on(med["weekdays"], today - timedelta(days=6 - i)),
                 "status": med["log"].get((today - timedelta(days=6 - i)).isoformat())} for i in range(7)]
        out.append({"name": med["name"], "dose": med["dose"], "time": med["time"], "reminds": names.get(med["remind_member_id"]),
                    "due_today": meds.due_on(med["weekdays"], today), "status": med["log"].get(today.isoformat()), "week": week})
    return {"meds": out}


def reminder_state(ctx, request):
    """The child marks a reminder done or not relevant for a day from today to a week ahead ({state: done|na|null}). Only this child's phone changes."""
    device = _device(ctx, request)
    if not ctx.store.phone_settings(device["household_id"], device["member_id"])["share"]["reminders"]:
        raise HTTPError(403, "Reminders are not shared with this phone")
    data = api.body(request)
    if data.get("state") not in (None, "done", "na"):
        raise HTTPError(400, "state must be done, na or null")
    day = api.parse_day(data.get("date"), api.latest(ctx)[2], past_days=0, future_days=7)     # the next school day can be a Monday
    api.checked(ctx.store.set_reminder_state, device["household_id"], request.params["id"], day, data.get("state"), device["member_id"])
    return 200, {"id": request.params["id"], "date": day.isoformat(), "state": data.get("state")}


def tick_chore(ctx, request):
    """The child says "I did it". It only ticks the chore; the star is still a parent's call (Done well / Try again)."""
    device = _device(ctx, request)
    store, household_id, member = ctx.store, device["household_id"], device["member_id"]
    if not store.phone_settings(household_id, member)["share"]["stars"]:
        raise HTTPError(403, "Chores are not shared with this phone")
    done = api.body(request).get("done")
    if not isinstance(done, bool):
        raise HTTPError(400, "done must be true or false")
    _, _, now = api.latest(ctx)
    today = now.date()
    chore = next((c for c in store.list_chores_today(household_id, today) if c["id"] == request.params["id"] and c["assignee_id"] == member and not c["skipped"]), None)
    if chore is None:
        raise HTTPError(404, "That is not one of your chores today")
    if store.chore_outcomes(household_id, today).get(chore["id"]):
        raise HTTPError(409, "A parent already looked at this one")
    store.set_chore_done(household_id, chore["id"], today, done, member)
    return 200, {"id": chore["id"], "done": done}


def _homework_shared(ctx, device):
    if not ctx.store.phone_settings(device["household_id"], device["member_id"])["share"]["homework"]:
        raise HTTPError(403, "Homework is not shared with this phone")


def add_homework(ctx, request):
    device = _device(ctx, request)
    _homework_shared(ctx, device)
    data = api.body(request)
    _, _, now = api.latest(ctx)
    task_id = api.checked(ctx.store.add_task, device["household_id"], device["member_id"], data.get("kind"), data.get("subject"),
                          str(data.get("title", "")), data.get("due_on"), data.get("note"), "child", now.date())
    return 201, {"id": task_id}


def tick_homework(ctx, request):
    device = _device(ctx, request)
    _homework_shared(ctx, device)
    done = api.body(request).get("done")
    if not isinstance(done, bool):
        raise HTTPError(400, "done must be true or false")
    api.checked(ctx.store.set_task_done, device["household_id"], request.params["id"], done, device["member_id"])
    return 200, {"id": request.params["id"], "done": done}


def dismiss_homework(ctx, request):
    device = _device(ctx, request)
    _homework_shared(ctx, device)
    dismissed = api.body(request).get("dismissed")
    if not isinstance(dismissed, bool):
        raise HTTPError(400, "dismissed must be true or false")
    api.checked(ctx.store.set_task_dismissed, device["household_id"], request.params["id"], dismissed, device["member_id"])
    return 200, {"id": request.params["id"], "dismissed": dismissed}


def remove_homework(ctx, request):
    device = _device(ctx, request)
    _homework_shared(ctx, device)
    api.checked(ctx.store.delete_task, device["household_id"], request.params["id"], device["member_id"])
    return 200, {"id": request.params["id"], "removed": True}


def register(router) -> None:
    router.get("/api/kids/phone/settings")(settings)
    router.put("/api/kids/phone/settings/{id}")(update_settings)
    router.post("/api/kids/phone/pairings")(start_pairing)
    router.delete("/api/kids/phone/pairings/{id}")(cancel_pairing)
    router.delete("/api/kids/phone/devices/{id}")(revoke_device)
    # The phone gateway exposes exactly the routes below (prefix /api/kids/phone/device/) and nothing else.
    router.post("/api/kids/phone/device/pair")(pair)
    router.post("/api/kids/phone/device/handoff")(handoff)
    router.post("/api/kids/phone/device/exchange")(exchange)
    router.post("/api/kids/phone/device/unpair")(unpair)
    router.get("/api/kids/phone/device/manifest")(manifest)
    router.get("/api/kids/phone/device/view")(view)
    router.post("/api/kids/phone/device/chores/{id}/done")(tick_chore)
    router.post("/api/kids/phone/device/bag/tick")(tick_bag)
    router.post("/api/kids/phone/device/bag/items")(add_bag_item)
    router.delete("/api/kids/phone/device/bag/items/{id}")(remove_bag_item)
    router.post("/api/kids/phone/device/homework")(add_homework)
    router.post("/api/kids/phone/device/homework/{id}/done")(tick_homework)
    router.post("/api/kids/phone/device/homework/{id}/dismiss")(dismiss_homework)
    router.post("/api/kids/phone/device/reminders/{id}/state")(reminder_state)
    router.delete("/api/kids/phone/device/homework/{id}")(remove_homework)

"""Stars and goals (kids/rewards).

A chore a parent marked as a star chore can end as Done (just ticked), Done well (a green star, granted by a parent) or
Try again (nothing lost). Stars are only ever added. Goals count a child's stars since their start date; stars are never
spent, and a parent approves a goal once it is reached.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from chit_server.loader import load_file_module
from chit_server.router import HTTPError

api = load_file_module(Path(__file__).parents[3] / "shared" / "api.py")


def _goal_view(goal, days):
    have = sum(n for day, n in days.items() if day >= goal["started_on"])
    return {**goal, "have": have, "reached": have >= goal["cost"], "pct": min(100, round(have * 100 / goal["cost"]))}


def build_child(child, chores, today_chores, star_ids, outcomes, goals, days, today):
    mine = [c for c in chores if c["assignee_id"] == child["client_id"]]
    monday = today - timedelta(days=today.weekday())
    week = [{"day": (monday + timedelta(days=i)).isoformat(), "stars": days.get((monday + timedelta(days=i)).isoformat(), 0)} for i in range(7)]
    return {
        "member_id": child["client_id"], "name": child["name"], "avatar": child.get("avatar"), "color": child.get("color"),
        "stars_total": sum(days.values()), "stars_week": sum(d["stars"] for d in week), "week": week,
        "goals": [_goal_view(g, days) for g in goals if g["member_id"] == child["client_id"]],
        "chores": [{"id": c["id"], "title": c["title"], "weekdays": [api.WEEKDAYS[d] for d in c["weekdays"]],
                    "day_part": c["day_part"], "star": c["id"] in star_ids} for c in mine],
        "today": [{"id": c["id"], "title": c["title"], "done": c["done"], "star": c["id"] in star_ids, "outcome": outcomes.get(c["id"])}
                  for c in today_chores if c["assignee_id"] == child["client_id"] and not c["skipped"]],
    }


def overview(ctx, request):
    household_id, document, now = api.latest(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "children": []}
    today = now.date()
    store = ctx.store
    chores = store.list_chore_series(household_id)
    today_chores = store.list_chores_today(household_id, today)
    star_ids, outcomes, goals = store.star_chore_ids(household_id), store.chore_outcomes(household_id, today), store.list_goals(household_id)
    kids = [build_child(k, chores, today_chores, star_ids, outcomes, goals, store.star_days(household_id, k["client_id"], "0000-01-01"), today)
            for k in api.children(document)]
    return 200, {"state": "manual", "date": today.isoformat(), "children": kids, "source": "chores and star grants entered in Chit"}


def set_star_chore(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    data = api.body(request)
    if not isinstance(data.get("enabled"), bool):
        raise HTTPError(400, "enabled must be true or false")
    api.checked(ctx.store.set_star_chore, household_id, request.params["id"], data["enabled"])
    return 200, {"id": request.params["id"], "star": data["enabled"]}


def set_outcome(ctx, request):
    household_id, _, now = api.need_household(ctx)
    data = api.body(request)
    day = api.parse_day(data.get("date"), now, past_days=14)
    api.checked(ctx.store.set_chore_outcome, household_id, str(data.get("chore_id", "")), day, data.get("outcome"))
    return 200, {"chore_id": data.get("chore_id"), "date": day.isoformat(), "outcome": data.get("outcome")}


def _goal_fields(data):
    cost = data.get("cost")
    return str(data.get("title", "")), cost, data.get("note")


def create_goal(ctx, request):
    household_id, document, now = api.need_household(ctx)
    data = api.body(request)
    title, cost, note = _goal_fields(data)
    member = str(data.get("member_id", ""))
    started = date(1, 1, 1) if data.get("count_existing") is True else now.date()   # count the stars already earned, or start fresh today
    goal_id = api.checked(ctx.store.add_goal, household_id, member, title, cost, note, started)
    return 201, {"id": goal_id}


def update_goal(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    title, cost, note = _goal_fields(api.body(request))
    api.checked(ctx.store.update_goal, household_id, request.params["id"], title, cost, note)
    return 200, {"id": request.params["id"]}


def remove_goal(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    api.checked(ctx.store.set_goal_status, household_id, request.params["id"], "archived")
    return 200, {"id": request.params["id"], "removed": True}


def approve_goal(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    data = api.body(request)
    approved = data.get("approved", True)
    if not isinstance(approved, bool):
        raise HTTPError(400, "approved must be true or false")
    api.checked(ctx.store.set_goal_status, household_id, request.params["id"], "approved" if approved else "active")
    return 200, {"id": request.params["id"], "approved": approved}


def register(router) -> None:
    router.get("/api/kids/stars/overview")(overview)
    router.put("/api/kids/stars/chores/{id}")(set_star_chore)
    router.post("/api/kids/stars/outcome")(set_outcome)
    router.post("/api/kids/goals")(create_goal)
    router.put("/api/kids/goals/{id}")(update_goal)
    router.delete("/api/kids/goals/{id}")(remove_goal)
    router.post("/api/kids/goals/{id}/approve")(approve_goal)

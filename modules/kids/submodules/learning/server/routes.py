"""Subjects and grades (kids/learning), German scale 1 (best) to 6.

Two graded types, written exam and oral / short test; a subject is core, minor or elective. The average of a subject combines the
average of each type with weights per subject kind (shared/grades.py). Grades are for parents; nothing here is shown on shared screens.
"""
from __future__ import annotations

from pathlib import Path

from chit_server.loader import load_file_module
from chit_server.router import HTTPError

shared = Path(__file__).parents[3] / "shared"
api = load_file_module(shared / "api.py")
grades = load_file_module(shared / "grades.py")
homework = load_file_module(shared / "homework.py")


def build_subjects(subjects, weights):
    out = []
    for subject in subjects:
        entries = subject["grades"]
        out.append({"id": subject["id"], "name": subject["name"], "code": subject["code"], "kind": subject["kind"], "lessons": subject["lessons"], "count": len(entries),
                    "latest": entries[-1]["grade"] if entries else None, "trend": grades.trend(entries),
                    **grades.subject_average(subject["kind"], entries, weights)})
    return out


def overview(ctx, request):
    household_id, document, now = api.latest(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "subjects": []}
    member = api.child_id(document, request)
    weights = ctx.store.get_grade_weights(household_id)
    raw = ctx.store.list_subjects_with_grades(household_id, member) if member else []
    entries = sorted(({**g, "subject": s["name"], "subject_id": s["id"]} for s in raw for g in s["grades"]),
                     key=lambda g: (g["given_on"], g["id"]), reverse=True)[:12]
    return 200, {"state": "manual", "member_id": member, "weights": weights, "subjects": build_subjects(raw, weights),
                 "entries": entries, "scale": "1 (best) to 6", "source": "grades entered in Chit"}


def update_subject(ctx, request):
    """Change a subject's full name, code and/or type (core, minor, elective). A new name is carried to its lessons, homework and bag items.
    A subject cannot be added or removed here: it exists because its lesson is in the school-day plan."""
    household_id, _, _ = api.need_household(ctx)
    data = api.body(request)
    fields = {key: data.get(key) for key in ("name", "code", "kind") if data.get(key) is not None}
    if not fields:
        raise HTTPError(400, "send a name, a code or a kind")
    api.checked(ctx.store.update_subject, household_id, request.params["id"], **fields)
    return 200, {"id": request.params["id"], **fields}


def merge_subject(ctx, request):
    """Fold a duplicate subject into the one to keep ({into: id}): lessons, grades, homework and bag items move over."""
    household_id, _, _ = api.need_household(ctx)
    into = str(api.body(request).get("into", ""))
    api.checked(ctx.store.merge_subjects, household_id, request.params["id"], into)
    return 200, {"id": request.params["id"], "merged_into": into}


def remove_subject(ctx, request):
    """Remove a subject for good, with its lessons in the plan and its grades. Reports what was removed."""
    household_id, _, _ = api.need_household(ctx)
    removed = api.checked(ctx.store.delete_subject, household_id, request.params["id"])
    return 200, {"id": request.params["id"], "removed": True, **removed}


def add_grade(ctx, request):
    household_id, _, now = api.need_household(ctx)
    data = api.body(request)
    day = api.parse_day(data.get("date"), now, past_days=400)
    grade_id = api.checked(ctx.store.add_grade, household_id, str(data.get("subject_id", "")), data.get("grade_type"), data.get("grade"), day, data.get("note"))
    return 201, {"id": grade_id}


def remove_grade(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    api.checked(ctx.store.delete_grade, household_id, request.params["id"])
    return 200, {"id": request.params["id"], "removed": True}


def set_weights(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    data = api.body(request)
    api.checked(ctx.store.set_grade_weights, household_id, data.get("core_written_pct"), data.get("minor_written_pct"), data.get("elective_written_pct"))
    return 200, ctx.store.get_grade_weights(household_id)


def homework_overview(ctx, request):
    """Homework and tests for a child, with the summary tiles. Parents read and write; the phone has its own routes (kid-view)."""
    household_id, document, now = api.latest(ctx)
    if household_id is None:
        return 200, {"state": "unconfigured", "tasks": []}
    member = api.child_id(document, request)
    today = now.date()
    tasks = [homework.view(t, today) for t in ctx.store.list_tasks(household_id, member, today)] if member else []
    subjects = [{"name": x["name"], "code": x["code"], "kind": x["kind"]} for x in ctx.store.list_subjects(household_id, member)] if member else []
    return 200, {"state": "manual", "member_id": member, "date": today.isoformat(), "summary": homework.summarize(tasks, today), "tasks": tasks, "subjects": subjects,
                 "source": "homework and tests entered in Chit"}


def _task_fields(data):
    return data.get("kind"), data.get("subject"), str(data.get("title", "")), data.get("due_on"), data.get("note")


def add_task(ctx, request):
    household_id, _, now = api.need_household(ctx)
    data = api.body(request)
    task_id = api.checked(ctx.store.add_task, household_id, str(data.get("member_id", "")), *_task_fields(data), "parent", now.date())
    return 201, {"id": task_id}


def update_task(ctx, request):
    """{done: bool} ticks it off or reopens it; {dismissed: bool} marks it not relevant or brings it back; a full body (kind, subject, title, due_on, note) edits it."""
    household_id, _, now = api.need_household(ctx)
    data = api.body(request)
    if "title" in data or "kind" in data:
        api.checked(ctx.store.update_task, household_id, request.params["id"], *_task_fields(data), now.date())
    if "done" in data:
        if not isinstance(data["done"], bool):
            raise HTTPError(400, "done must be true or false")
        api.checked(ctx.store.set_task_done, household_id, request.params["id"], data["done"])
    if "dismissed" in data:
        if not isinstance(data["dismissed"], bool):
            raise HTTPError(400, "dismissed must be true or false")
        api.checked(ctx.store.set_task_dismissed, household_id, request.params["id"], data["dismissed"])
    return 200, {"id": request.params["id"]}


def remove_task(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    api.checked(ctx.store.delete_task, household_id, request.params["id"])
    return 200, {"id": request.params["id"], "removed": True}


def register(router) -> None:
    router.get("/api/kids/homework")(homework_overview)
    router.post("/api/kids/homework")(add_task)
    router.put("/api/kids/homework/{id}")(update_task)
    router.delete("/api/kids/homework/{id}")(remove_task)
    router.get("/api/kids/grades/overview")(overview)
    router.put("/api/kids/grades/weights")(set_weights)
    router.put("/api/kids/grades/subjects/{id}")(update_subject)
    router.delete("/api/kids/grades/subjects/{id}")(remove_subject)
    router.post("/api/kids/grades/subjects/{id}/merge")(merge_subject)
    router.post("/api/kids/grades")(add_grade)
    router.delete("/api/kids/grades/{id}")(remove_grade)

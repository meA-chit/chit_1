"""Subjects and grades (kids/learning), German scale 1 (best) to 6.

Two graded types, written exam and oral / short test; subjects are main or other. The average of a subject combines the
average of each type with weights per subject kind (shared/grades.py). Grades are for parents; nothing here is shown on shared screens.
"""
from __future__ import annotations

from pathlib import Path

from chit_server.loader import load_file_module
from chit_server.router import HTTPError

shared = Path(__file__).parents[3] / "shared"
api = load_file_module(shared / "api.py")
grades = load_file_module(shared / "grades.py")


def build_subjects(subjects, weights):
    out = []
    for subject in subjects:
        entries = subject["grades"]
        out.append({"id": subject["id"], "name": subject["name"], "kind": subject["kind"], "count": len(entries),
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


def add_subject(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    data = api.body(request)
    subject_id = api.checked(ctx.store.add_subject, household_id, str(data.get("member_id", "")), str(data.get("name", "")), data.get("kind"))
    return 201, {"id": subject_id}


def update_subject(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    data = api.body(request)
    api.checked(ctx.store.update_subject, household_id, request.params["id"], str(data.get("name", "")), data.get("kind"))
    return 200, {"id": request.params["id"]}


def remove_subject(ctx, request):
    household_id, _, _ = api.need_household(ctx)
    api.checked(ctx.store.archive_subject, household_id, request.params["id"])
    return 200, {"id": request.params["id"], "removed": True}


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
    api.checked(ctx.store.set_grade_weights, household_id, data.get("main_written_pct"), data.get("other_written_pct"))
    return 200, ctx.store.get_grade_weights(household_id)


def register(router) -> None:
    router.get("/api/kids/grades/overview")(overview)
    router.put("/api/kids/grades/weights")(set_weights)
    router.post("/api/kids/grades/subjects")(add_subject)
    router.put("/api/kids/grades/subjects/{id}")(update_subject)
    router.delete("/api/kids/grades/subjects/{id}")(remove_subject)
    router.post("/api/kids/grades")(add_grade)
    router.delete("/api/kids/grades/{id}")(remove_grade)

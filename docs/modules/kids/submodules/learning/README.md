# Submodule: learning (module `kids`)

> Parent: [`docs/modules/kids/README.md`](../../README.md) · Code: `modules/kids/submodules/learning/`

## Purpose
Exam and homework tracker; later tutor support and exam preparation planning.

## Boundaries
- Owns: _to be defined_
- Reads from other submodules/modules: _to be defined (public contracts only)_
- Must not: import other modules' internals; infer availability from missing data; present forecast/manual/demo data as measured.

## Enablement
Can be enabled or disabled independently of its siblings where its dependencies allow it. Declared in `modules/kids/module.manifest.yaml`.

## UI (cards / views)
_To be defined._

## What it does
German scale 1 (best) to 6. Two graded types, **written exam** and **oral / short test**. A **subject** is a lesson title in the child's school-day plan (`kids/school`) and has a type: **core**, **minor** or **elective** (see `../../decisions/0001-subjects-come-from-the-plan.md`). A subject's average = the average of each type, combined with the household's written share for the subject type (default core 50/50, minor and elective 30/70 written/oral; editable because schools differ); a subject with one type uses it alone and no grade is ever treated as zero. The trend compares the two latest grades with the earlier ones.
- API: `GET /api/kids/grades/overview?member=`, `PUT /api/kids/grades/weights`, `POST|PUT|DELETE /api/kids/grades/subjects[/{id}]`, `POST /api/kids/grades`, `DELETE /api/kids/grades/{id}`.
- Grades are for parents: no dashboard card, and a child's own view never shows them.
- Data: `kid_subjects`, `kid_grades`, `kid_settings` (migration 010). Seed: `seed/kids/learning.json`.

## Status
Implemented (first version).
## Homework and tests (2026-10-07)
Table `kid_tasks` (migration 013): `kind` homework or test, subject (free text), title, due date, done time, `created_by` parent or child. A child writes their own from the phone (shared via `share_homework`, default on) and may delete only what they wrote; a parent can add, edit, tick and remove anything. A test is a task whose date counts down. Summary tiles (due tomorrow, tests in 2 weeks, overdue, done this week, open per school day) are computed on the hub (`shared/homework.py`).

Routes: `GET/POST /api/kids/homework`, `PUT/DELETE /api/kids/homework/{id}` (parents); the phone uses `/api/kids/phone/device/homework*` (kid-view). Parent UI: the "Homework & tests" panel on the Kids page. Phone UI: Homework tab, "Homework" section on Today. Tests: `tests/test_homework.py`.

## Subjects (2026-10-08)
Subjects are not typed in. They exist because a lesson with that title is in the plan: adding a lesson creates the subject (type `minor` until a parent chooses), the lesson editor sets the type, and `PUT /api/kids/grades/subjects/{id}` (body `name`, `code` and/or `kind`) changes it later. Removing the last lesson of a subject hides it and keeps its grades; adding the lesson again brings both back; renaming the last lesson renames the subject. Each subject has a **name** and a **code** (up to 6 characters, shown on the phone with c, m or e beside it); both are edited on the subject, and a new name is carried to its lessons, homework and bag items. Homework and grades pick from the child's subject list (every type) and the hub refuses a subject that is not on it. Grades can only be entered for subjects currently in the plan. Migration 015 removed the subjects that had been typed in by hand (and the grades under them).

## Merge, remove and not relevant (2026-10-08)
Subjects: `POST /api/kids/grades/subjects/{id}/merge` folds a duplicate into the one to keep (lessons, grades, homework and bag items move); `DELETE /api/kids/grades/subjects/{id}` removes a subject with its lessons and grades (trash icon in the UI, with a confirmation). Homework: `PUT /api/kids/homework/{id}` also takes `{dismissed: boolean}` (not relevant); the parent panel shows a "Not relevant" button, a trash icon instead of "Remove", and a collapsed "Not relevant" list with "bring back". See `../../decisions/0001-subjects-come-from-the-plan.md`.


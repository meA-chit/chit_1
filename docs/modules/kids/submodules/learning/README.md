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
German scale 1 (best) to 6. Two graded types, **written exam** and **oral / short test**; subjects are **main** (German, Maths, English) or **other** (Geography, Biology, Music, Sport, Art). A subject's average = the average of each type, combined with the household's weights per kind (default main 50/50, other 30/70 written/oral; editable because schools differ); a subject with one type uses it alone and no grade is ever treated as zero. The trend compares the two latest grades with the earlier ones.
- API: `GET /api/kids/grades/overview?member=`, `PUT /api/kids/grades/weights`, `POST|PUT|DELETE /api/kids/grades/subjects[/{id}]`, `POST /api/kids/grades`, `DELETE /api/kids/grades/{id}`.
- Grades are for parents: no dashboard card, and a child's own view never shows them.
- Data: `kid_subjects`, `kid_grades`, `kid_settings` (migration 010). Seed: `seed/kids/learning.json`.

## Status
Implemented (first version).
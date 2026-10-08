# Kids decision 0001: subjects come from the school-day plan, with three types

- Status: Accepted (2026-10-08)
- Deciders: product owner
- Relates to: `submodules/school` (the plan), `submodules/learning` (grades), migration 015

## Context
Subjects were typed in separately in the grades settings as *main* or *other*, next to a school-day plan that already named every lesson. The two lists drifted apart (the plan had `Mathe`, the subject list `Mathematics`), the homework and bag subject suggestions came from the plan, and a grade could be entered for a subject that is not taught.

## Decision
1. **A subject is a lesson title in the child's plan.** There is no other way to create one. Adding a lesson creates its subject if the title is new (matching is case-insensitive); the same title on other days is the same subject.
2. **Three types: core, minor, elective** (replacing main and other). The type is chosen in the lesson editor ("Subject type") and can be changed on the subject in the grades settings. A new subject starts as `minor` until a parent chooses. Each type has its own written-versus-oral weight (defaults 50, 30, 30).
3. **Leaving the plan hides, it does not delete.** When the last lesson of a subject is removed, the subject is archived: its grades are kept, it disappears from the lists, and nothing new can be graded under it. If the lesson comes back, so do the subject, its type and its grades. Renaming the last lesson renames the subject.
4. **Existing manual subjects were removed** by migration 015, with the grades entered under them. A subject is created for every lesson title already in a plan.
5. Homework and bag-list subject suggestions already come from the plan and are unchanged.

## Options considered
- **Keep manual subjects and link them to lessons.** Two lists to keep in step; rejected because the drift is the problem.
- **Keep two types.** The product owner wants core, minor and elective; electives are usually weighted differently, so each type has its own weight.

## Consequences
- A child with no plan has no subjects and no grades screen content until lessons are added.
- Timetable codes from a school (for example `M`, `Fö_E7/Fö_F7/Fö_L7`) become subject names. Rename the lessons in the plan to rename the subjects.
- The default type is a guess (`minor`): after the migration a parent has to classify each subject once.

## Amendment 2026-10-08: names, codes, and pickers instead of typing
- **Each subject has a full name and a short code** (1 to 6 characters, no spaces, unique per child; migration 016). The name is used in lists and sheets, the code in tight places: the phone's week plan shows the code with the type as a superscript, **c** core, **m** minor, **e** elective (for example Mat<sup>c</sup>). A code is generated when a subject is created (the name itself if it is up to 5 characters, else the initials of several words, else the first letters, made unique) and a parent edits it.
- **Name, code and type are managed on the subject** (grades settings, "Name and code") and may also be set in the lesson editor when a lesson creates the subject. A new **name is carried to the subject's lessons, homework and bag items** so it stays one subject; its grades follow because they belong to the subject.
- **Nobody types a subject again.** Homework (parent panel and phone) and grades pick from the child's subject list, which holds every core, minor and elective subject. The hub refuses a homework subject that is not on the list (by name or by code; the stored value is the subject's name). Homework without a subject is still allowed. Homework written before this rule keeps the text it had.
- The phone receives the subject list (name, code, type) whenever the timetable, homework or grades are shared, so it can label a subject the same way everywhere.

## Amendment 2026-10-08 (2): duplicates, merge and remove
- **Duplicates happen** when the same subject is typed twice in the plan with different names or codes (for example `Sport m/Sport w` and `Sport w/Sport m`). Since a lesson title is a subject, that makes two subjects. The grades settings flag likely duplicates (the same words in another order, or one letter apart) and offer **Merge into** the other with one click, and the "Name and code" panel has a "Merge this subject into another" picker for any pair.
- **Merge** (`POST /api/kids/grades/subjects/{id}/merge`, `{into}`): for the same child only. The duplicate's lessons take the kept subject's name, its grades move over, its homework and bag items follow (a bag item the kept subject already has is not doubled), and the duplicate is deleted. The kept subject keeps its own name, code and type.
- **Remove** (`DELETE /api/kids/grades/subjects/{id}`, a **trash icon**, with a confirmation that says how many lessons and grades go): removes the subject for good with its lessons in the plan, its grades and its bag items. Homework that named it stays and loses the subject. This replaces "removing the last lesson hides the subject": hiding still happens when a lesson is removed from the plan, the bin is the deliberate delete.
- Icon-only trash buttons replace the "Remove" text in subject and plan management, with an accessible name and a tooltip.


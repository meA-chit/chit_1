# Kids module design (final proposal, 2026-10-06)

Artifact: https://claude.ai/artifact/CY7nh8P139NVS6d3CxJuYE (private). The `.dc.html` files here are the board sources (sample data for the Meyer family); `canvas.json` is the canvas index. Not built yet.

Boards: **Main** (today: school-day plan with recess, chores, medication, week tiles), **Stars** (stars, chore configuration, goals), **Grades**, **Health** (medication), **KidView** (the child's own phone screen).

## Decisions
- **Stars are only added.** A chore ends as *Done* (keeps the streak), *Done well* (parent gives a green star) or *Try again* (amber, nothing lost). No red stars: a missed chore stays open, never a penalty. Per chore the parent chooses "star chore" or "tick only".
- **Goals.** Parents set goals with a star cost (movie night 30, sleepover with friends 50, hang out outside the home 100). Progress bars show on the parent view and on the child's own screen. Stars are never spent: they count toward every active goal since a start date; reaching a goal needs a parent's approval.
- **Grades (German system).** Scale 1 (best) to 6. Two types of graded exams: *written exam* and *oral / short test*. Each subject is **main** (German, Maths, English) or **other** (Geography, Biology, Music, Sport, Art). The subject average = the average of each type combined with weights per subject kind (assumed default: main 50/50 written/oral, other 30/70; editable in settings because schools differ). A subject with one type uses it alone. Grades are parents-only by default.
- **School day plan**: typed in by a parent (state `manual`), lessons, recesses, lunch, care group and trips, reusing the commute data from household setup.
- **Medication**: strictest privacy class. Shared screens (TV, timeline) show "Mila, 19:00" without the medicine's name; reminders go to the assigned parent; supply and refill warning are tracked.

## Mapping to submodules
`school` (day plan), `activities` (existing), `learning` (subjects, grades, weights), `rewards` (stars, goals), `kid-view` (the child's screen), new `health` (medication). Chores stay in `planner`; `rewards` reads them through a public contract.

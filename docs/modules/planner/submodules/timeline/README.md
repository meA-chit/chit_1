# Submodule: timeline (module `planner`)

> Code: `modules/planner/submodules/timeline/` · shared helpers: `modules/planner/shared/timeline.ts`

**Purpose.** The family's day on one screen: 06:00 to 22:00, one lane per person plus a shared Family lane, a NOW marker, past dimmed, and the next trip highlighted. On phones it becomes a vertical agenda.

**Day parts (zones).** The window is divided into the household's generic blocks: **Morning 06-10, Day 10-16, Evening 16-20, Relax 20-22** (single source `modules/planner/shared/dayparts.py`, returned by the API). Reminders sit inside their zone band above the lanes (any-time reminders in their own row); lanes only carry what happens on the clock.

**Compact lanes.** Blocks are packed into rows by overlap, so a lane is one row unless things truly overlap. Travel (commute, drop-offs, pick-ups) within 15 minutes of other travel is merged into a single block ("Drop off Mila, Leo"). Blocks too short for a label show a glyph.

**Other days.** `GET /api/planner/timeline/day?date=YYYY-MM-DD` (today up to 14 days ahead; `/today` is the same view). The card has previous/next arrows and a **Back to today** button; other days have no NOW marker and no dimming.

**Data.** `GET /api/planner/timeline/day` builds blocks from the routines entered in household setup (state `manual`): work (with commute for office days), school/care between drop-off and pick-up, trips (by car: the first listed pick-up/drop-off adult; walking or cycling: the child's own "Cycle to school" / "Walk home" blocks), and child activities for the weekday with their commute: independent children get their own trip blocks, parent-accompanied activities put "Take Mila to Football" and "Pick up Mila" on that parent's lane. A commute is only drawn when its mode and travel time were entered. The card merges today's calendar-feed events (client-side by member name; none, several or unknown members go to the Family lane). Household time zone drives "today" and "now".

**Rules.** Nothing is inferred: no work block on a day without a location, no school start without a drop-off time (drawn as an open-ended block), an empty day means "nothing was entered", not "free". Blocks outside the window are clipped.

**Not built.** Cheap-power band (needs the energy forecast), conflict highlighting (e.g. pick-up during work), editing from the timeline.

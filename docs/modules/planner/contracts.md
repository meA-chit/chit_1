# Public contracts: Time & Planner

The only surface other modules may use. Anything not listed here is private.

## Read APIs
- `GET /api/planner/calendar/agenda`: the next 21 days of events from the household's calendar links. Each event: `title`, `start`, `end` (ISO, household time zone), `all_day`, `source`, `category` (`school_care`, `sport_activity`, `family`, ...), `members` (names) and `member_ids` (the people the calendar is attached to; empty means the whole household) and `icon` (an emoji chosen from the title and category, or null). `state` is `available`, `partial`, `stale` or `unavailable`. Other modules read it in-process with `ctx.read("/api/planner/calendar/agenda")` and must cache the answer: it fetches the feeds each time. First consumer: `kids/kid-view` (the child's phone, filtered to the child's own calendars).

## Events published
_None defined yet._

## Events consumed
_None defined yet._

Changes to this file are contract changes: update the module manifest, `docs/core/specifications/` where applicable, and notify the owners of dependent modules (`docs/00-overview/module-map.md`).

## Reminder marks (2026-10-08)
`GET /api/planner/reminders/today` items carry `done` (the dashboard's own mark for today). `POST /api/planner/reminders/{id}/done` (`{done: boolean}`) sets it; "not relevant today" is the existing `POST .../skip`. A child's phone keeps separate marks (kids/kid-view), so the two never overwrite each other.


# UI design system and shell

Code: `core/web/src` (`theme/`, `ui/`, `shell/`, `registry/`). Client entry: `apps/web`. Decision: [ADR-0008](../decisions/0008-web-client-react-typescript-and-hub-api.md).

## Direction
"We got to move into the future." A dark, calm command-deck feel: near-black void, a faint grid, glass panels with HUD corner brackets, cyan/violet signal colours, monospace micro-labels, and slow ambient motion (edge light sweep, pulsing live dot, staggered card entrance). Light theme tokens exist (`data-theme="light"`); dark is the default. Motion respects `prefers-reduced-motion`.

Futuristic must not undermine trust: **every card shows its data state** (`StateBadge`, states from `data-states.yaml`) and provenance footer; empty is never rendered as "free" or zero; failures say "unavailable".

## Rules for module UI
- Import only from `@chit/core`. Use `CardFrame`, `StateBadge`, `Skeleton`, `Empty`. Never hard-code colours, fonts or spacing; use tokens in `theme/tokens.css`.
- A card is registered twice: declared in `module.manifest.yaml` (id, title, sizes, surfaces, data_states, optional `privacy_class`) and exported from the submodule `web/index.ts` (`ModuleWeb`). The manifest alone decides visibility; the shell resolves it through `GET /api/shell`.
- Fetch from your own `/api/<module>/…`; map server `state` to a `DataState`; show provenance lines (source, observed/checked time).
- Cards are lazy-loaded; keep first paint cheap (phones, Raspberry Pi display).
- Sizes `s|m|l|xl` are hints; the shell picks per surface (TV largest, phone smallest) on a 12-column grid.

## Surfaces
| Surface | Behaviour |
|---|---|
| `tv` | No rail, large type, non-interactive, screen-safe, sensitive modules hidden |
| `tablet`, `web` | Left rail + grid; management views |
| `mobile-adult` | Bottom floating tab bar, single column |
| `mobile-kid` | Provisioned by an adult, never inferred from width |
Detection: `?surface=` override, otherwise width (`lib/useSurface.ts`).

## Not yet built (stories needed)
Household/member enablement layers 3–4 in `/api/shell`, a port of the household setup form (still the prototype at `/legacy/household/setup/…`), views routing for ported pages, light/dark switch UI, offline cache, Capacitor shells, accessibility audit.

## Dashboard layout principles (from the 2026-10-06 design review)
Review mock-up: https://claude.ai/artifact/2ih7ubZSLUTDaNjMSpQLo1 (desktop, phone, avatar picker). Inspiration was a dense dark family dashboard; we keep its feel, not its content.

**Feel.** Deep navy, glass cards, one soft glow, mono micro-labels. Every card has the same header (icon chip, title, one-line subtitle, one action on the right). Numbers big and quiet; labels tiny. The next item is highlighted ("Next"); the past fades.

**Bands, top to bottom** (this is what keeps "everything on one screen" organised):
1. **Left rail: who.** Household members with avatars; the selected member is highlighted and re-filters the whole page ("view as"). "Everyone" is the default. Settings and add-person sit at the bottom.
2. **Top bar: what is around us.** Greeting, module navigation (icon + label), weather widget, clock, notifications.
3. **Today timeline: the hero.** 06:00–22:00, one lane per person plus a shared Family lane, a "now" marker, past dimmed, optional cheap-power window. This is the one place the whole day is visible.
4. **Three detail columns:** chores (with streaks) · family planner · Home (energy, climate, suggestions as tabs in one card).

**Anti-clutter rules.** At most five rows per card then "View all". One hue system: colour means *person* (avatar ring, timeline block, calendar dot, chore tag); status uses small pills only. Energy/climate/suggestions share one tabbed card rather than three. Phone: same sections stacked, timeline becomes a vertical agenda with a NOW marker, module nav moves to a bottom bar.

**Rule-compatible deviations from the reference.** No health or live-location panels (sensitive, hidden on shared screens). No device toggles or "Add event" (pilot is read-only): automations appear as *Suggestions*. Forecast values carry a Forecast pill, never Live. Avatars are predefined illustrations, never photos.

**Implementation (2026-10-06).** Shell = `core/web/src/shell` (ribbon, floating module dock, slot-based dashboard, tabbed panel). The ribbon holds the Chit mark and wordmark, the greeting and the `topbar` cards; the dock at the foot of the screen holds module navigation and becomes the full-width bottom bar on phones. Cards declare `slot` (`topbar|timeline|timeline-side|left|center|right`; `timeline-side` is a slim column beside Today, used by the week outlook), optional `group` (cards in the same slot+group become tabs of one panel) and `order` in their manifest. Avatars live in `core/web/src/ui/Avatar.tsx`. The mock-up source is in `docs/design/home-dashboard/`.

**Day parts, not clock times.** The household's generic blocks are Morning 06-10, Day 10-16, Evening 16-20, then Relax. Chores and reminders are planned in these zones, never at exact times. On the timeline the zones are bands above the lanes and hold the reminders; lanes stay compact (single row unless blocks overlap, adjacent travel merged). The timeline can show other days with arrows (next to the title) and a Back to today button; it carries no source footer or state badge. Chores and reminders share one dashboard card with per-row operations (skip for today, edit, remove).

**Data honesty on the dashboard.** Timeline and chores are `manual` (typed in by the household). Weather is fetched by the hub from Open-Meteo and shows `stale`/`unavailable` rather than guessing. Energy, climate and suggestions are `demo` (illustrative, no connectors yet) and labelled so. Not built: cheap-power band on the timeline (needs the energy forecast), Week view, chores 'View all' page, notifications.

**Avatars.** Four adult and four child illustrations (man, woman, man with beard, woman with bun; boy, girl with pigtails, boy with cap, girl with glasses), chosen per member during setup, plus a per-person colour. Stored on the member (`avatar`, `color`); defaults are assigned if none is chosen.


**Navigation and appearance (2026-10-08).** The left rail is the only module navigation (Home and each enabled module, colour per module); "Viewing as" moved to a menu in the top bar; on phones the rail becomes the bottom bar. Appearance has two independent choices, both kept per device (`core/web/src/theme/appearance.ts`, localStorage `chit.appearance`) and applied as `data-theme` (dark, light, or auto = follow the device) and `data-palette` on `<html>`: **Classic** (cyan accent) and **Spectrum** (multi-colour: each module keeps its own colour in the rail, gradients run through every signal colour). A three-icon switch (light, dark, match device) sits at the foot of the rail and in the "Viewing as" menu; the full choice is under Household settings > Appearance. Components use tokens only (`--accent-soft`, `--inset`, `--rail-bg`, `--grad`, `--on-accent`), never fixed dark rgb values.

**Grid page (2026-10-08).** Energy and Devices are one rail entry, "Grid" (`/grid`, view in `modules/energy/submodules/grid`). A module can opt out of the rail with `nav: false` in its manifest (Devices does; its cards still show on Home). Pages that mix live and demo data badge each tile separately.

# Home dashboard design source (2026-10-06)

Static design review mock-up, kept in the repo so it travels with the code. Live copy (private claude.ai Artifact): https://claude.ai/artifact/2ih7ubZSLUTDaNjMSpQLo1

| File | What it shows |
|---|---|
| `Main.dc.html` | Desktop dashboard: member rail, top bar (modules, weather), today timeline, chores / calendar / home panel |
| `Mobile.dc.html` | Phone layout: member strip, vertical agenda with NOW marker, bottom module bar |
| `Setup-Avatars.dc.html` | Household setup step: choose an avatar (4 adult, 4 child) and a colour |
| `Avatar.dc.html` | The nine avatar illustrations (shared by the others) |

These are Design Component files (`.dc.html`): they render in the Design artifact viewer, not directly in a browser. The implemented UI is `core/web` plus the module `web/` folders; this folder is the visual reference, not the source of truth. Principles: `docs/core/ui-design-system.md`.

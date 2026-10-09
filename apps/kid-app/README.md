# Chit Kids (the child's phone app)

An installable web app (no build step, no Apple developer account). It shows the child their own school day, stars and chores, reminders and, if a parent allows, grades and medicine. See [ADR-0012](../../docs/decisions/0012-kid-phone-pairing-and-gateway.md).

It is served only by the hub's **phone gateway**, which exposes this app and `/api/kids/phone/device/*` and nothing else.

## Try it with real household data

1. Start the hub and web client with the gateway on:

   ```bash
   CHIT_PHONE=1 npm run dev:all
   ```

   The hub prints `Phone gateway: http://<your-ip>:8766`. Your phone must be on the same Wi-Fi. (`CHIT_PHONE_PORT` and `CHIT_PHONE_URL` override the port and the address put in the QR.)

2. On your Mac open `http://localhost:5173/household`, go to **Kids' phones**, turn on the phone view for a child, choose what it may show (grades and medicine are off by default), and tap **Pair a phone**.
3. On the child's phone open the **Camera**, scan the QR code and tap the link. Type the 6 digits shown on the Mac screen. The code is valid for 10 minutes and works once; 5 wrong codes lock it.
4. In Safari tap Share, **Add to Home Screen** (keep "Open as Web App" on). The app keeps a one-use link ready while it is open in Safari, so the installed app normally picks the pairing up on first launch.
5. If the installed app asks to be paired anyway (iOS gives it separate storage), tap **Type the codes**, then enter the 8-character **link code** and the 6 digits from the pairing screen on the Mac.

Remove a phone, or switch the child's phone view off (signs out every phone), on the same settings screen.

## Demo mode

`http://<ip>:8766/?demo=1` (add `&now=2026-10-07T09:10` to fix the clock, `&theme=dark` for dark mode) shows built-in sample data, labelled "Demo data" on every screen. It never talks to the hub.

## Notes

- Plain HTTP on the home network for now (ADR-0012 follow-ups: HTTPS, push reminders). Do not share grades or medicine on an untrusted network.
- Icons: `node apps/kid-app/make-icons.mjs`.
- Files the gateway serves are an explicit list in `core/server/chit_server/gateway.py` (`STATIC_ALLOW`).

## Screens and current limits (updated 2026-10-08)
Tabs appear only for sections a parent shares: **Today**, **Plan** (timetable, activities, coming up), **Homework**, **Stars**, **Grades**, **Health**; the avatar opens an "About me" sheet that lists what the parents share. Today changes what leads by time of day and holds the bag checklist. Full table, and what is still missing (pocket money and perks, push, age tiers, child preferences, German text), in `docs/modules/kids/submodules/kid-view/README.md`; the design and the build status of each item are in `docs/modules/kids/kid-experience.md`.

Limits worth knowing before a demo: English strings only; writes are queued while offline and reads fall back to the last saved view; the bag time is fixed at 19:30; calendar events come from the calendars attached to the child (a parents' evening on the school calendar shows up too); tested in a desktop browser at phone and tablet sizes, not yet on a real iPhone or iPad.

## Structure: independent of the web app (2026-10-09)
The kid app imports nothing from the web app or its theme, and has its own stylesheet. It is meant to be rebuilt as a native app later, so the hub is the only shared thing:

| File | Role |
| --- | --- |
| `index.html` | Page shell only |
| `styles.css` | All styling and its own design tokens (edit freely; no sync with the web theme) |
| `app.js` | Screens, state, offline write queue, appearance |
| `data/api.js` | **Data layer**: the endpoint contract (documented at the top), device token and storage, `call()`, `sendOp()` |
| `data/demo.js` | Built-in demo data, same shape as the server's `/view` |
| `fonts/` | Space Grotesk and JetBrains Mono, served locally |

A native client keeps the contract in `data/api.js` (and the shape of `/view`) and replaces everything else. The gateway serves exactly these files (`STATIC_ALLOW` in `core/server/chit_server/gateway.py`): add any new file there.

## Look
Dark by default, **Light** and **Match phone** as choices, and two palettes, **Classic** (cyan) and **Spectrum** (each tab has its own colour in the bottom bar). The child picks them under the avatar > Look; the choice is kept on that phone (`chitkids.appearance`). `?theme=light|dark` and `?palette=spectrum` override for demos. It looks like the web app but is maintained separately.

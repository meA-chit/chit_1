# ADR-0012: Kid phone: parent-enabled pairing (QR + code), device tokens and an isolated phone gateway

- Status: Accepted (scope: pilot on a trusted home network; HTTPS and push are follow-ups below)
- Date: 2026-10-07
- Deciders: product owner, kids module owner
- Relates to: ADR-0007 (this satisfies two of its "new ADR needed" conditions for the child's phone only), ADR-0008/0009 (PWA over a paired hub), open decision 2 (identity, still open for adults)

## Context
A child (10+, secondary school) should see their own school day, stars, reminders and, if a parent allows, grades and medicine on their own phone. There is no Apple developer account, so the client is an installable web app (Add to Home Screen). ADR-0007 keeps the hub on loopback without authentication, and says a second device or children's data over the network needs a new ADR. Opening the whole hub to the network would expose every parent and household route, so that is not an option.

## Decision
1. **Opt-in per child, by a parent.** Household settings gets a "Kids' phones" section (contributed by `kids/kid-view`). Per child: phone view on/off, and what it may show (timetable, reminders, homework and tests, stars and chores; grades and medicine are **off by default**). Stored in `kid_phone_access` (migration 011). Switching a child off is a kill switch: every paired phone is revoked and open pairings cancelled.
2. **Pairing is two factors the parent controls.** The parent taps "Pair a phone"; the parent's screen shows a QR code and a 6-digit code. The QR holds a 128-bit single-use secret in the URL fragment (never sent to a server or logged); the code is **not** in the QR. The phone scans the QR with its camera, opens the app, and the 6 digits are typed on the phone. Pairing expires after 10 minutes, locks after 5 wrong codes, and a new pairing cancels the previous one. Secret and code are stored as hashes only.
3. **Device token.** A successful pairing returns a 256-bit bearer token kept on the phone; the hub stores its sha256. Parents see paired phones (label, paired, last seen) and can remove any of them. Every request re-checks that the device is not revoked and the child's phone view is still on.
4. **Safari to Home Screen (two ways).** iOS gives a Home Screen app its own empty storage, so a pairing made in Safari is not visible to the installed app.
   - *Handoff:* while the app is open in Safari on iOS it keeps a fresh one-use, 15-minute link (`/?h=...`, also in the manifest `start_url`) so installing at any moment carries the pairing; on its first launch the installed app exchanges it for a **rotated** token and the Safari token stops working.
   - *Pair in the installed app:* the pairing screen on the parent's side also shows an 8-character **link code**. The installed app (which cannot scan) takes the link code plus the 6 digits. Same secret strength rule: the link code is a typed form of the QR secret, never enough alone. Wrong guesses are throttled process-wide (20 per 10 minutes, then a pause for everyone) because a typed code is a smaller space than the QR secret.
5. **Isolated listener, not the hub.** The hub stays on `127.0.0.1`. When started with `CHIT_PHONE=1` it also runs the *phone gateway* (default port 8766, `0.0.0.0`) that serves only the kid app files from an explicit allow-list and only routes under `/api/kids/phone/device/`. All parent, household, finance and management routes answer 404 on it (tested). `CHIT_PHONE_URL` overrides the address shown in the QR (hostname or HTTPS proxy).
6. **The server decides what the phone sees.** `GET /api/kids/phone/device/view` builds a child-scoped payload from the parent's settings; an unshared section is absent from the response, and the payload carries no member or household ids. The child can tick their own chore; the star (Done well / Try again) stays a parent decision, and a chore a parent already reviewed cannot be changed from the phone.
7. **Data honesty.** Values are `manual` (entered in Chit). Demo data exists only behind an explicit "demo" mode and is labelled on every screen. The service worker never caches API responses; the app keeps one last snapshot in `localStorage` for offline use and wipes it when the phone is unpaired.

## Options considered
- **Expose the Vite/hub port to the LAN (`CHIT_LAN=1`) and call the normal API.** Rejected: every parent route becomes reachable by anyone on the Wi-Fi.
- **QR only.** A photographed or shoulder-surfed QR would pair. Rejected: the second, on-screen-only factor is cheap.
- **Code only.** Typing a 6-digit code against a guessable address with no secret is brute-forceable. Rejected.
- **Native iOS app.** Needs the developer account the product owner does not have; the PWA covers the pilot.

## Consequences
- The pilot's transport is plain HTTP on the home network: device tokens and the child's data are readable by someone who can sniff that Wi-Fi. Mitigations now: opt-in gateway, short-lived pairing, hashing, revocation, health/grades off by default. **Follow-up:** HTTPS (a local certificate or a hostname behind a TLS proxy via `CHIT_PHONE_URL`) before sharing health data outside a trusted network, and web push for reminders (needs HTTPS).
- iOS Home Screen handoff relies on iOS honouring the manifest/page URL at install time; it is verified on desktop only and must be confirmed on a real iPhone.
- Adults still have no identity (ADR-0007): the parent routes (`/api/kids/phone/*`) are as public as the rest of the loopback hub. Kid pairing does not change that.
- Specification: routes `/api/kids/phone/*` (parent) and `/api/kids/phone/device/*` (phone). Code: `modules/kids/submodules/kid-view/`, `core/store/chit_store/kid_phone.py`, `core/server/chit_server/gateway.py`, `apps/kid-app/`.

## Amendment 2026-10-08: more in the phone payload, and a read hook
- The device view now also carries `activities` (weekly activities, leave-by, and events from the child's own calendars) and `bag` (the derived checklist and the child's items), each behind its own share key (`activities`, `bag`, both on by default). Hidden means absent, as before.
- The hub reads the planner's calendar through `ctx.read("/api/planner/calendar/agenda")`, an in-process call of another module's public read API (`docs/core/cross-module-contracts.md`, `docs/modules/planner/contracts.md`). The gateway resolves such reads against the full router; it still serves only the device routes to the network (tested over HTTP).
- The calendar answer is cached for ten minutes per household and a stale copy is served while it refreshes, so the phone's one-minute refresh never fans out to calendar providers.
- The phone queues its writes while offline (`localStorage`), applies them on screen at once and drops a change the hub refuses.
- The manifests no longer lock portrait, and the viewport allows zoom.


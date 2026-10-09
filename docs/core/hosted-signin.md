# Hosted sign-in: runbook (ADR-0014)

Sign-in is **off** by default (the local hub has no accounts, ADR-0007). It is for the hosted profile: Postgres backend plus `CHIT_AUTH=1`.

## Settings (environment)

| Variable | Meaning |
|---|---|
| `CHIT_AUTH=1` | turn sign-in on (needs `CHIT_STORE_BACKEND=postgres`) |
| `CHIT_DB_URL` / `CHIT_DB_OWNER_URL` | application role / owner role (the owner applies migrations at start-up) |
| `CHIT_MAIL=console\|brevo` | `console` keeps mails in memory (add `CHIT_MAIL_ECHO=1` to print them while developing). `brevo` sends through the API: `BREVO_API_KEY`, `CHIT_MAIL_FROM` (an address on the authenticated sending domain), `CHIT_MAIL_FROM_NAME` |
| `CHIT_TERMS_VERSION`, `CHIT_TERMS_URL` | the Terms version people must accept (change it to ask everyone again) and where they read it |
| `CHIT_COOKIE_SECURE=0` | only for plain-http development; leave on in production |
| `CHIT_TRUSTED_PROXY_HOPS=1` | proxies in front of the hub that set `X-Forwarded-For` / `-Host` (Cloud Run: 1) |
| `CHIT_ALLOWED_ORIGINS` | extra origins allowed to send cookie-carrying requests (development behind the Vite proxy: `http://localhost:5173`) |
| `CHIT_AUTH_PEPPER` | secret mixed into rate-limit keys |
| `CHIT_APP_URL` | public address used in invitation links (operator tool) |

Secrets (`BREVO_API_KEY`, `CHIT_AUTH_PEPPER`, the database URLs) belong in the secret manager, never in the repository or in chat.

## Operator tasks (run yourself, with the OWNER database role)

```bash
export CHIT_DB_OWNER_URL=...  CHIT_APP_URL=https://app.chithome.de  PYTHONPATH=core/store
python -m chit_store.admin_cli create-household --name "Meyer family" --owner-name Nina   # household + the owner's invitation
python -m chit_store.admin_cli pair --household <id> --member <member id>                 # another invitation / lost-mailbox recovery
python -m chit_store.admin_cli list                                                       # who has an account
python -m chit_store.admin_cli disable-account --email nina@example.org                   # block and sign out everywhere
```

An invitation is a **link** and a **6-digit code**, valid 30 minutes, usable once. Send them on **different channels** (link by WhatsApp, code by voice or SMS). The link carries its secret in the URL fragment, so it is never sent to a server or written to a log; the page removes it from the address bar.

The pilot default modules are `household, planner, kids`. Energy (stores provider keys) and health data stay off until a family asks (ADR-0013).

## What a person does

1. Opens the link, types the invitation code.
2. Enters an email address, ticks the Terms, receives a 6-digit code (valid 15 minutes), types it. Signed in for 30 days (sliding).
3. Next time: email, code. No passwords.

The household owner can invite the other adult from the app (`POST /api/auth/invites`); only the owner can invite or transfer ownership, and a transfer needs a fresh email code (`/api/auth/reauth/*`).

## Recovery

A lost mailbox or a new address: run `pair` again for the same member. Completing it replaces whoever held that seat; the old account keeps no access to the household.

## Development

```bash
# hub (scratch database), then the web client with the Vite proxy pointing at it
CHIT_STORE_BACKEND=postgres CHIT_DB_URL=... CHIT_DB_OWNER_URL=... CHIT_AUTH=1 CHIT_COOKIE_SECURE=0 \
CHIT_MAIL=console CHIT_MAIL_ECHO=1 CHIT_ALLOWED_ORIGINS=http://localhost:5173 python -u -m chit_server
npm run dev     # sign-in page at http://localhost:5173/auth/
```
Use `python -u` so the printed codes appear immediately.

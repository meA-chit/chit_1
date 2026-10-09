# ADR-0014: Hosted identity: pairing for enrolment, email code for sign-in

- Status: Proposed
- Date: 2026-10-09
- Deciders: product owner
- Relates to: ADR-0007 (no authentication; this supersedes it **for the hosted profile**, once accepted), ADR-0012 (kid pairing, unchanged), ADR-0013 (hosted profile), ADR-0015 (storage), open decision 2

## Context
The hosted pilot (ADR-0013) needs adults to have identities. Households are created by the operator for invited families. Adults should not manage passwords. Kids must not need accounts. Some adults will belong to more than one household later (separated or blended families), so identity must be global and household membership separate. Terms of Use must be accepted before use.

## Decision
### Model
- **Account** (global): one verified email address.
- **Membership**: `(account, household, household member, role)`; roles are `owner`, `adult`, `kid`. One account may have several memberships. Kids have a membership-like device scope but **no account**.
- **Owner**: the adult who creates the household. Only the owner can delete the household or transfer ownership. These two actions require a fresh email code (re-authentication within the last 10 minutes) and, for deletion, typed confirmation and a soft-delete window (default 14 days).
- Routes **never accept a household id from the client**. The household comes from the session's membership (ADR-0015).

### Enrolment (first login) by pairing
1. An **operator console** (separate secret, never reachable with a household session; shows metadata, never family content) creates a household shell (name, timezone, country) and issues a **pairing** for the owner. An owner can issue the same kind of pairing for another adult from inside the app.
2. A pairing is a **link plus a 6-digit code** shared on **different channels** (for example link by WhatsApp, code by voice or SMS). Both are needed.
3. Opening the link never redeems it. It shows a page where the code is typed, and redemption is a POST. (Chat and mail previews may open links.)
4. Rules: single use, expires after 30 minutes, 5 wrong codes lock it, only hashes stored, a new pairing cancels the previous one for the same invitee. These mirror ADR-0012.
5. After the code, the person must **tick acceptance of the Terms of Use** and enter their **email address**, then verify it with an email code (below). Only then is the account created (or an existing account for that email attached) and the membership bound.

### Sign-in after enrolment: email code
- The person enters their email; the server sends a **6-digit code valid for 15 minutes**, single use.
- Codes are stored hashed; at most 5 attempts; rate limits per email address and per IP; resend cooldown. The response is **identical whether or not the email is known**, so addresses cannot be enumerated.
- Success creates a **device session**: an `HttpOnly`, `Secure`, `SameSite=Lax` cookie, valid 30 days with sliding renewal. A new device or an expired session means a new email code. Sessions can be listed and revoked by the account.
- **No passwords are stored.** Passkeys may be added later as an additional method.

### Terms
- `terms_acceptance(account, terms_version, accepted_at)`. When the version changes, the next sign-in requires acceptance again. Acceptance is checked server-side, not only in the client.

### Email delivery
- Use an **EU transactional email API** (for example Brevo, Postmark or Resend with the EU region) over HTTPS, not SMTP port 25, which GCP blocks. The sending domain is `mail.chithome.de` (ADR-0013), with SPF, DKIM and DMARC required. Deliverability must be tested with Gmail, iCloud, and GMX or web.de.
- Email content contains only the code and a short note; no household or child information.

### Kids
- Unchanged from ADR-0012: parent-enabled pairing, device token, isolated gateway scope. A kid device token can reach only kid routes. Kid data in the cloud follows the same consent and share settings.

### Recovery and support
- Lost mailbox: the operator verifies the person out of band and issues a new pairing. Email change requires a code to both the old and the new address.

## Implementation status (2026-10-09)
Built: tables in migration `004_accounts.sql`, rules in `core/store/chit_store/accounts.py`, the gate in `core/server/chit_server/auth_gate.py`, routes in `auth_routes.py`, the operator tool `chit_store/admin_cli.py`, the sign-in page `apps/web/public/auth/`, and 27 HTTP tests (`core/server/tests/test_auth_http.py`). Sign-in is on only with `CHIT_AUTH=1`; the local hub is unchanged. Runbook: [`docs/core/hosted-signin.md`](../core/hosted-signin.md). Deviations and open points:
- **The operator console is a command-line tool, not an HTTP page.** It uses the owner database role, so there is no operator login to protect and no extra attack surface; an HTTP console can follow if the number of households makes it worthwhile.
- **Mail is sent on a background thread**, so an address with an account and one without answer equally fast. The Brevo sender is written but **not yet verified against the live service** (the sending domain was still being set up); the console mailer is what the tests and local development use.
- **Rate limits** live in `auth_events` (hashed keys): 5 codes per address and 20 per client per hour, 20 pairing tries and 40 code checks per client per hour, plus 5 wrong guesses per pairing or per emailed code.
- **CSRF**: cookies are `SameSite=Lax`; a request that carries the session cookie and an `Origin` must match the host (or `X-Forwarded-Host` behind a trusted proxy, or `CHIT_ALLOWED_ORIGINS`).
- **Not built yet**: household deletion with typed confirmation and a soft-delete window (the re-authentication it needs exists: `require_owner(fresh=True)`); self-service sign-up of a new household (households are created by the operator); an account page for changing email address; audit log of sign-ins.

## Options considered
- **Email magic link only.** Mail scanners and previews can consume links, and non-technical users find them confusing. A typed code avoids both.
- **SMS or phone verification.** Costs money, collects phone numbers (more personal data), and has SIM-swap risk. Rejected.
- **Google or Apple sign-in.** Adds a third-party identity dependency and its own data-processing story; not needed for 10 families. May be added later.
- **Pairing only, no email.** Simpler, but recovery is entirely manual and there is no account to attach to a second household. Rejected.
- **Passwords.** Storage, reset flows and weak-password risk for no benefit here. Rejected.

## Consequences
- A new dependency: an email provider, plus a domain with correct DNS records. Sign-in is unavailable if email delivery fails; the operator can still issue a pairing as a break-glass path.
- Whoever holds both the link and the code can enrol as that invitee until it is redeemed or expires; the owner sees pending pairings and can cancel them.
- ADR-0007's conditions no longer apply to the hosted profile; the loopback profile is unchanged.
- Specification and tests: new `/api/auth/*` routes; tests for code expiry, attempt limits, enumeration safety, terms re-acceptance, owner-only deletion with re-authentication, and a kid token being refused on adult routes.

## Revisit when
- Adults on separate households need the linked-child sharing (a share table keyed by accounts).
- Support load from lost mailboxes grows (add recovery email or passkeys).
- Paying customers: add audit logs of sign-ins and administrative actions.

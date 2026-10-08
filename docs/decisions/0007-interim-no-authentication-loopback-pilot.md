# ADR-0007: Interim — no application authentication while loopback-only

- Status: Accepted (interim; reflects the code on `devs` as of 2026-10-06)
- Date: 2026-10-06
- Supersedes: [ADR-0005](0005-local-single-owner-authentication.md)

## Context
ADR-0005 required a single local owner login, sessions and CSRF. The implementation removed all of it (commit `551b420`) to simplify the pilot; documents kept describing it. The server binds to `127.0.0.1` only.

## Decision
- The pilot runs **without application authentication**, bound to loopback only. Setup, calendar and summary routes are public to anyone who can reach that port on the host.
- This is acceptable **only** while all of the following hold: loopback binding, single-household host, no LAN/public exposure, no real third-party credentials reachable through the API.
- Encryption at rest (ADR-0004) still applies.

## Conditions that force a new ADR before proceeding
- Serving the TV display from another device (e.g. Raspberry Pi) over the LAN.
- Any mobile app or second user device (adult or child).
- Any exposure beyond loopback, or more than one household per deployment.
- Adding finance, health or children's data (sensitive classes) to API responses.
- Per-member roles, audiences or surface-specific enablement (see `docs/core/enablement-and-audiences.md`).

The replacement design must cover identity (households, members, devices/surfaces), transport security, authorisation per audience, shared-display credentials, and recovery.

## Update 2026-10-07
[ADR-0012](0012-kid-phone-pairing-and-gateway.md) allows one opt-in exception: a child's own phone through the isolated phone gateway (`CHIT_PHONE=1`), with parent-enabled pairing and device tokens. The hub itself, and every adult route, remain loopback-only and unauthenticated.

## Consequences
Simpler pilot; the security-privacy rules that assume authentication are marked as **target state** until a new ADR lands. Tests assert public access (`server/tests/test_http_auth.py`); `server/tests/test_auth.py` is a placeholder and should be removed or replaced.

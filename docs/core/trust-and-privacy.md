# Trust and privacy

## Data trust
- Every normalized record carries source, observed time, ingestion time, availability, data state and schema version ([ADR-0003](../decisions/0003-data-provenance-model.md)). States are defined in [`specifications/data-states.yaml`](specifications/data-states.yaml): `measured`, `forecast`, `manual`, `unavailable`, `demo`. Exactly one per value; a label is required on shared displays; colour alone must never distinguish states.
- `observedAt` and `ingestedAt` are never substituted for each other. Stale data may remain visible for context but must not look live. Unknown freshness is `unknown`.
- Missing data is `unavailable`/`unknown`; availability is never inferred from absence.

## Trust boundaries
- **Household:** one household cannot access another's data.
- **Member / audience:** adult, child and guest audiences; sensitive data follows person-specific grants. Children's visible modules are set by an adult.
- **Surface:** tv, tablet, web, mobile-adult, mobile-kid each receive only what their surface profile allows. Shared displays receive screen-safe data.
- **Connector:** least-privilege credentials and entity allowlists; secrets never reach browser code.
- **Cloud:** no household data to cloud processors without an approved purpose and policy.

## Sensitive classes
health, finance, children, location, private calendar details. Default: denied on shared surfaces, explicit per-person consent elsewhere, revocation invalidates caches. Module privacy classes (normal / sensitive / strict) are declared in each module manifest. AI-derived insights over sensitive classes are opt-in and cite evidence.

## Screen-safe policy
The safe projection may show that a person is busy while hiding title, location, notes and attendees. Sensitive categories are hidden by default. A privileged reveal needs an authenticated, authorised interaction and must not persist on the shared screen. Screen-safe masking is applied server-side before a response is built.

## Authentication and authorisation
- **Current:** none; loopback-only interim per [ADR-0007](../decisions/0007-interim-no-authentication-loopback-pilot.md).
- **Target (undesigned):** household and member identity, device/surface credentials, audience-based authorisation, shared-display credential, TLS for any non-loopback access. Required before LAN/TV-over-network, mobile apps, or sensitive modules. Draft capability model: [`specifications/permissions.yaml`](specifications/permissions.yaml).

## Controls
- Encrypt SQLite at rest (SQLCipher, [ADR-0004](../decisions/0004-sqlite-encrypted-local-storage.md)); define key lifecycle and encrypted backups.
- Do not log tokens, private event details, health or finance data, or full provider payloads.
- Audit configuration and permission changes.
- Minimise collection; each module declares what it stores.

## Threats to test
Database/backup disclosure incl. key exposure; cross-household and cross-member access; stale cache revealing revoked data; connector over-permissioning; prompt/content injection from external calendar text; secrets in Git/logs; forecast/demo presented as measured; child-view widening; SSRF through user-supplied feed URLs.

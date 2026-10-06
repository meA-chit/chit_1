# ADR-0009: Hub-first deployment, data classes and optional cloud

- Status: Accepted as direction; identity/transport details blocked on open decision 2
- Date: 2026-10-06
- Builds on: ADR-0001 (local-first), ADR-0004 (encrypted SQLite), ADR-0007 (loopback pilot)

## Context
We want one product that runs fully on a household's own machine, ships as Android/iOS apps, and may later use the cloud for some data. Question: can personal data stay local while other data is in the cloud, and should we start fully cloud for speed?

## Decision

### 1. One deployable: the **household hub**
The hub (`core/server` + modules + encrypted store + built web client) is a single-household unit. The same artefact runs in three **deployment profiles**; no profile-specific code paths:

| Profile | Where | Use |
|---|---|---|
| `local` | Mac/mini-PC/Raspberry Pi in the home | Default. Data never leaves the home unless the household enables a cloud feature. |
| `hosted` | Same container on a cloud VM, one per household | Escape hatch for speed ("start with full cloud"): zero new code, still SQLCipher. Chosen when a household has no always-on device. |
| `dev` | Developer laptop | Vite on :5173 proxying to the hub on :8765. |

Phones and tablets are **clients of a hub**, never a second source of truth. They hold a pairing credential and a small cache for offline reads. Multi-tenant SaaS (many households in one database/Postgres) is explicitly **not** planned; it would need a new ADR.

### 2. Data classes decide residency
Every table/record family declares a class in its module docs and migration header:

| Class | Examples | Residency |
|---|---|---|
| `personal` | members, profiles, health, finance, kid data, calendar feed URLs, device credentials | Hub only, SQLCipher. Never sent to cloud services except as end-to-end encrypted backup blobs. |
| `household` | chores, plans, rewards, preferences, derived insights | Hub; may be included in encrypted backup/sync between the household's own devices. |
| `public` | weather, tariffs, public holidays, forecast caches | Cache anywhere; fetched by the hub server-side with provenance (ADR-0003). |
| `operational` | push tokens, relay routing, update checks, crash reports (scrubbed) | May live in the cloud service. |

So *partial local / partial cloud is feasible* **because the cloud never needs personal data**: it provides reachability and notifications, not storage.

### 3. What the optional Chit cloud service does (later, not built now)
1. **Relay/tunnel** so phones reach the hub away from home (outbound connection from the hub; no open ports).
2. **Push** (APNs/FCM) carrying only an opaque "something changed" signal; content is fetched from the hub.
3. **Encrypted backup** (client-side encrypted with a household-held key; the service stores ciphertext).
4. **Update channel** for signed hub releases.
Each is opt-in per household and can be absent without breaking the product.

### 4. Sync model (phones ↔ hub)
Phones read through the hub API with a read-through cache (TanStack Query persistence). Writes made offline are queued as idempotent commands (`Idempotency-Key`) and replayed; the hub is the authority and resolves conflicts per entity (last-writer-wins for preferences, append-only for measurements). Hub-to-hub or hub-to-cloud replication is **not** in scope; add it only with a story.

### 5. Staging
1. **Now**: `local` profile, loopback only (ADR-0007). Client scaffold done.
2. **Next (blocks mobile and TV-over-LAN)**: identity ADR — household/member/device pairing, TLS (local CA or relay-terminated), per-surface credentials. Until it lands the hub MUST stay on `127.0.0.1`; mobile apps must not be pointed at it.
3. Capacitor shells + pairing flow; PWA.
4. Relay + push + encrypted backup, in that order, only when a story needs them.

## Consequences
- Fast start without a rewrite: "full cloud" is the `hosted` profile of the same hub.
- Privacy-by-architecture: the cloud service is designed so a breach exposes no household content.
- Costs: we own hub updates/backup/observability on household hardware, key management (CHIT_DB_KEY_HEX provisioning, rotation, recovery), and a pairing/transport design before any non-loopback exposure.
- Every new table must state its data class; reviewers reject `personal` data reaching a cloud-bound code path.

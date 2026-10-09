# ADR-0013: Hosted pilot: EU cloud deployment on GCP

- Status: Proposed
- Date: 2026-10-09
- Deciders: product owner
- Relates to: ADR-0001 and ADR-0009 (local-first / hub-first; this adds a `hosted` profile and, once accepted, supersedes them **for that profile only**), ADR-0007 (loopback, no auth; see ADR-0014), ADR-0015 (database), open decisions 2, 14, 15

## Context
The product owner wants to give a small group of invited households (about 5 to 10 families in Germany, each with school-age or older children) a working version next week, and to collect feedback before a wider rollout. Hardware (a home hub) comes later. Households contain children's data, and optionally medication and grades, so the EU data-protection regime applies and the operator is a controller/processor, not just a software vendor.

The code today is a local hub: one household, loopback only, no authentication, SQLite. ADR-0009 describes a `hosted` profile as a possibility but does not decide it.

## Decision
1. **Add a `hosted` deployment profile** (`CHIT_PROFILE=hosted`) next to the local hub. It is multi-household, authenticated (ADR-0014) and backed by Postgres (ADR-0015). The local profile stays as it is until a decision about the home hub is made. A future hub **syncs to** the cloud rather than replacing it; that is out of scope here.
2. **Region: EU only, Frankfurt (`europe-west3`)** for compute, database, storage and backups. Nothing personal leaves the EU. Logs and error reports must not contain personal data, and any third-party processor (email, error tracking) must be EU-hosted or covered by a data processing agreement.
3. **Provider: Google Cloud Platform.**
   - App: **Cloud Run** (stateless container, TLS, scales to zero).
   - Database: **Cloud SQL for PostgreSQL**, managed, with automated backups and point-in-time recovery (ADR-0015).
   - Secrets: Secret Manager. Images: Artifact Registry in the same region.
4. **Domain: `chithome.de`** (registrar: Namecheap, DNS managed there). The product is served at `app.chithome.de`; sign-in email is sent from `mail.chithome.de`. Registrar account has two-factor authentication and auto-renew on.
5. **Keep it portable.** The app ships as a plain Docker image and configuration comes only from environment variables. The database is standard Postgres (`pg_dump` restores anywhere). No GCP-only APIs in application code beyond secret and storage access behind a thin interface.
5. **Pilot guard rails.**
   - Demo seeding (`seed.py`) is disabled in the hosted profile; sign-up creates an empty household.
   - Per-household module enablement is used to ship only the stable subset. **Energy (stores provider credentials) and medication are off by default.**
   - A restore from backup is rehearsed once before the first family is invited.
   - Error tracking and an uptime check are in place before invitation.
   - No high availability for the pilot; a single region and single instance of the database are accepted.
6. **Fallback for the first wave.** If the Postgres port (ADR-0015) is not green at the mid-week decision point, the first 2 or 3 families may run on the **same image with SQLite on a single Compute Engine VM** (persistent disk, daily snapshots, Litestream to an EU bucket). The second wave waits for the Postgres cutover. This fallback is temporary and must not outlive the first wave.
7. **Legal prerequisites** before any family is invited: Terms of Use ([`docs/legal/beta-terms-of-use.md`](../legal/beta-terms-of-use.md), reviewed), a Privacy Notice (Art. 13 GDPR), an Impressum if required, a data processing agreement with Google (and each other processor), and explicit consent where health data is enabled (Art. 9 GDPR).

## Options considered
- **Hetzner (Germany), self-managed.** Considerably cheaper (a small VM is a few euros a month) and a simple EU story. Rejected for the pilot **only because it offers no managed Postgres**: backups, patching and recovery would be the owner's job while the data includes children's information. Still a valid option later; portability (point 4) keeps it open.
- **AWS (Frankfurt).** Comparable features and price to GCP at this scale. No advantage that outweighs the owner's preference and existing familiarity with GCP.
- **Cloud Run with SQLite.** Rejected: SQLite needs a real local disk and file locking; mounted object or network storage is unsafe for it.
- **Stay local-only for the pilot.** Rejected: friends' households cannot run a hub, and hardware is not ready.

## Consequences
- Operating a multi-household service makes the owner a data controller or processor with real obligations (privacy notice, deletion and export on request, breach handling). The Terms and Privacy Notice are part of the deliverable, not an afterthought.
- Cost is dominated by the database tier (roughly tens of euros per month; verify with the pricing calculator). The shared-core micro tier has no SLA and is not used.
- ADR-0001 ("run ... on household-controlled infrastructure") is no longer true of the hosted profile. When this ADR is accepted, update ADR-0001 and ADR-0009 to say so; do not rewrite their history.
- The deployment documentation (`docs/core/`) and the open-decisions list (#14 cloud services scope) must be updated when this is accepted.

## Revisit when
- More than about 50 households, or any paying customer: add high availability, a read replica and a status page.
- Cost or data-residency needs change (consider Hetzner or another EU host with managed Postgres).
- A home hub exists: define sync and the data classes that stay local (open decision 15).

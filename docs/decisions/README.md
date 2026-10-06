# Decisions (ADRs)

Product-wide architecture decision records. Module-level decisions live in `docs/modules/<module>/decisions/`.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-local-first-deployment.md) | Local-first deployment | Accepted |
| [0002](0002-home-assistant-integration.md) | Home Assistant as optional read-only boundary | Accepted |
| [0003](0003-data-provenance-model.md) | Provenance on every normalized record | Accepted |
| [0004](0004-sqlite-encrypted-local-storage.md) | SQLite + SQLCipher local storage | Accepted |
| [0005](0005-local-single-owner-authentication.md) | Single local owner authentication | Superseded by 0007 |
| [0006](0006-modular-architecture-and-mirrored-structure.md) | Modular architecture, mirrored docs/code | Accepted |
| [0007](0007-interim-no-authentication-loopback-pilot.md) | Interim: no authentication while loopback-only | Accepted (interim) |
| [0008](0008-web-client-react-typescript-and-hub-api.md) | React + TypeScript client (Vite, Capacitor for mobile); Python hub behind a manifest-driven API | Accepted |
| [0009](0009-hub-first-deployment-and-data-residency.md) | Hub-first deployment, data classes, optional cloud | Accepted (direction) |
| [0010](0010-dev-data-store-sqlite-runtime-with-json-seed-documents.md) | Dev/pilot store: SQLite at runtime, committed JSON household documents as seed/export | Accepted |
| [0011](0011-energy-provider-connections.md) | Energy provider connections: server-side keys per household, verified before storing | Accepted |

Pending decisions are tracked in [`docs/00-overview/open-decisions.md`](../00-overview/open-decisions.md). Supersede ADRs; do not rewrite history.

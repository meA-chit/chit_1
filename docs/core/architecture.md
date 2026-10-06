# Architecture

Status: describes the **current implementation** and the **modular target**. The larger Next.js/PostgreSQL proposal that previously occupied this file is preserved in [`architecture/target-stack-proposal.md`](architecture/target-stack-proposal.md) and is **not adopted** (see open decisions).

## Style: modular monolith
One deployable application composed of modules (`modules/<id>`) on a shared platform (`core/`). Modules are isolated (no cross-imports), register through manifests and communicate through public contracts and events ([ADR-0006](../decisions/0006-modular-architecture-and-mirrored-structure.md)). Extraction to services is allowed only when a measured need appears.

```
 surfaces: tv | tablet | web | mobile-adult | mobile-kid
        │   (shell composes registered cards/views per household, member, surface)
 core/web ── enablement & layout resolution ── design system
        │
 core/server ── API gateway ── policy (screen-safe, permissions) ── attention service
        │              │
        │        connectors (calendar, weather, tariff, Home Assistant, ...)
        │
 modules/<m>/submodules/<s>/{server,web}   ── own tables & migrations
        │
 core/store ── encrypted SQLite (SQLCipher)
```

## Current implementation
| Concern | Today |
|---|---|
| Hub | Python stdlib `ThreadingHTTPServer`, loopback `127.0.0.1:8765` (`core/server/chit_server`); manifest registry loads each submodule's `server/routes.py`; `GET /api/shell` resolves enablement |
| Storage | SQLite + SQLCipher, key from `CHIT_DB_KEY_HEX`, SQL migrations (`core/store/chit_store/`) |
| Client | React 18 + TypeScript + Vite single-page app (`apps/web`), shell and design system in `core/web`, cards in `modules/*/submodules/*/web` ([ADR-0008](../decisions/0008-web-client-react-typescript-and-hub-api.md)) |
| Mobile | Planned: Capacitor shells over the same bundle + PWA; blocked on identity ([ADR-0009](../decisions/0009-hub-first-deployment-and-data-residency.md)) |
| Auth | None (ADR-0007, interim) |
| Calendar | iCal/webcal fetch with `icalendar`, read-only |
| Weather / energy | Not served yet (prototypes archived); to be rebuilt as server-side connectors |

## Deployment and data residency
Hub-first: one household hub in `local` or `hosted` profile; personal data stays on the hub; the optional cloud service only provides relay, push, encrypted backup and updates. Full detail in ADR-0009.

See [`current-implementation.md`](current-implementation.md) for gaps against the rules.

## Deployment profiles
Local-first (ADR-0001): household-controlled host (Mac Mini or similar), loopback today. Edge display (Raspberry Pi) and mobile clients require the network/auth decisions in ADR-0007 first. A managed cloud profile is a possible future option, not a pilot requirement.

## Technology stack
Not finalised. Python + vanilla JS is what exists; a TypeScript/React stack is proposed in `architecture/target-stack-proposal.md`. Whichever is chosen must support: manifest-driven module registry, card composition, per-surface layouts (including a mobile client), and the encrypted local store. Decision tracked in `docs/00-overview/open-decisions.md`.

## Cross-cutting design
- Data model and provenance: [`data-model.md`](data-model.md), [`specifications/`](specifications/)
- Enablement, UI composition, contracts: [`enablement-and-audiences.md`](enablement-and-audiences.md), [`ui-composition.md`](ui-composition.md), [`cross-module-contracts.md`](cross-module-contracts.md)
- Trust, privacy, security: [`trust-and-privacy.md`](trust-and-privacy.md)
- Connectors: [`connectors.md`](connectors.md)
- Diagrams: [`diagrams/`](diagrams/) (C4 DSL, runtime sequences)

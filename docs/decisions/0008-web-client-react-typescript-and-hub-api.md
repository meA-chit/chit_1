# ADR-0008: React + TypeScript client on one codebase; Python hub kept behind a manifest-driven API

- Status: Accepted (resolves open decisions 1 and 3)
- Date: 2026-10-06

## Context
Chit is UI-heavy, must feel modern and "futuristic", and runs on five surfaces (TV, tablet, web, adult phone, kid phone) from modules built in parallel. The pilot server (Python, SQLCipher, tested) works; the pilot UI (vanilla HTML/JS, no build) cannot host a manifest-driven card shell or ship to phones. The earlier proposal (Next.js + PostgreSQL + Redis) was written for a different product and conflicts with ADR-0001 and ADR-0004.

## Decision
**Client** — TypeScript + React 18 + Vite, a single-page app (`apps/web`) composed from `core/web` and each submodule's `web/index.ts`.
- **React, not Node/Next.js**: the client is a static bundle served by the hub (or a CDN later). There is no SSR need, and a Node runtime on a Raspberry Pi/household box adds weight for nothing. "Node" is only the build tool.
- **One codebase for all surfaces.** Responsive layout plus *surface profiles* (`config/surfaces/*.yaml`) decide what each screen shows. TV is the same app with `?surface=tv`/provisioned surface, chrome hidden, large type.
- **Mobile apps (Android + iOS)**: wrap the same bundle with **Capacitor** (`apps/mobile`, not yet scaffolded), plus a PWA for quick installs. We choose this over React Native because the shell renders registered cards from the web bundle; native rewrites would duplicate every card. Revisit through a new ADR only if a native-only capability (background location, HealthKit, widgets) becomes a story.
- **State/data**: TanStack Query for server state; `motion` for animation; react-router. No global store until a story needs one.
- **Registration without central files**: `apps/web/src/main.tsx` globs `modules/*/submodules/*/web/index.ts`. A module adds a card by (1) declaring it in `module.manifest.yaml`, (2) exporting a renderer from `web/index.ts`. The manifest, not the client code, decides who sees it (non-negotiable rule: enablement is configuration).
- **Cards are code-split** (`React.lazy`) so phones only download cards they render.

**Server (hub)** — Python is kept for now. `core/server/chit_server` is the hub: router, manifest registry, `/api/shell` enablement resolver, static/SPA serving. Submodules contribute routes via `server/routes.py: register(router)`, restricted to `/api/<module-id>/…` and given services only through a `Context` (store, log) — never by importing another module.
- Why not rewrite in TypeScript now: it works, is tested, owns the SQLCipher store, and a rewrite buys no user-visible value. The API is the boundary (`docs/core/specifications/api.openapi.yaml`); the client never depends on the language behind it, so a later port, per module if wanted, is possible.
- Python 3.9 compatibility is retained for the pilot host.

**Design system** lives in `core/web/src/theme` + `ui` (see `docs/core/ui-design-system.md`): dark "void + glass" default, tokens only, data-state badge on every card.

## Consequences
- Two toolchains (Node for build/test of the client, Python for the hub). `npm run check` runs isolation, typecheck, vitest and the python suites.
- `npm run build` must run before the hub serves the UI; in development Vite proxies `/api` to the hub.
- Types for API payloads are hand-written next to each card today. Generate them from OpenAPI when the spec is made authoritative (follow-up story).
- Lint/CI are still missing (see `docs/core/current-implementation.md`).

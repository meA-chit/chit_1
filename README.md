# Chit

Chit is a personal automation and intelligence platform: a local-first logic layer that brings household schedules, chores, weather, smart-home and energy context into a trustworthy shared view.

## Current product direction

The first pilot is an always-visible, read-only household dashboard. It prioritises trustworthy data ingestion, visible provenance, privacy and explainable insights before autonomous actions.

## Documentation

Start with [`docs/00-overview/README.md`](docs/00-overview/README.md); the full map is in [`docs/README.md`](docs/README.md). Docs mirror code: `docs/core` <-> `core/`, `docs/modules/<module>` <-> `modules/<module>`.

- Product vision and context: [`docs/00-overview/`](docs/00-overview/README.md)
- Modules: household, planner, kids, energy, devices, finance — [`docs/modules/`](docs/modules/README.md)
- Platform architecture, enablement, trust and contracts: [`docs/core/`](docs/core/README.md)
- Decisions: [`docs/decisions/`](docs/decisions/README.md) · Open decisions: [`docs/00-overview/open-decisions.md`](docs/00-overview/open-decisions.md)
- Backlog index: [`docs/backlog/`](docs/backlog/README.md) · Pilot scope and roadmap: [`docs/releases/`](docs/releases/pilot-scope.md)
- Agent guidance: [`AGENTS.md`](AGENTS.md)

## Run it

```sh
npm install
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
npm run dev:all   # unencrypted dev database, auto-seeded with the sample household (seed/), UI on http://localhost:5173
npm run check     # isolation + typecheck + vitest + python tests
```
`dev:all` runs the hub on `127.0.0.1:8765` (loopback only, ADR-0007) with `CHIT_STORAGE=plain` and the Vite client. For the encrypted store use `npm run hub` with `CHIT_DB_KEY_HEX` and `CHIT_DB_PATH` (see `core/store/README.md`). Sample data: `seed/README.md`.
`npm run build` type-checks and produces `apps/web/dist`. The hub no longer serves that build (it is API-only; open the web app on port 5173 with `npm run dev`). Serving the built client from the hub, for local-network or wall-display use, is deferred.

## Repository layout

```
apps/web/            client entry (Vite); apps/mobile/ is planned (Capacitor)
core/{server,store,web,contracts}   shared platform
modules/<m>/submodules/<s>/{server,web,tests}   one folder per feature; server/routes.py + web/index.ts self-register
config/              household presets and surface profiles
docs/                mirrors the code; start at docs/00-overview/README.md
dashboard/archive/   archived prototypes (not requirements)
```
Architecture decisions: [ADR-0008](docs/decisions/0008-web-client-react-typescript-and-hub-api.md) (stack), [ADR-0009](docs/decisions/0009-hub-first-deployment-and-data-residency.md) (deployment and data residency). Code migration status: `docs/core/current-implementation.md`.

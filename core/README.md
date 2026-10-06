# `core/` — shared platform

Docs: [`docs/core/`](../docs/core/README.md). Contains the module registry, UI shell and design system, enablement and layout resolution, trust layer, connectors, permissions and shared contracts.

Changes here affect every module: keep them small, separate PRs, and update `docs/core/`.

## Layout
| Folder | Contents |
|---|---|
| `server/chit_server/` | Hub: router, module registry, enablement/shell resolver, static serving. Python (`PYTHONPATH=core/server:core/store`). |
| `store/chit_store/` | Encrypted SQLite repository and migrations. See `store/README.md`. |
| `web/src/` | Design system (`theme`, `ui`), shell, card registry, API client. Public surface: `index.ts` (`@chit/core`). |
| `contracts/` | Manifest schema and shared contracts. |

Docs: [`docs/core/ui-design-system.md`](../docs/core/ui-design-system.md), [ADR-0008](../docs/decisions/0008-web-client-react-typescript-and-hub-api.md), [ADR-0009](../docs/decisions/0009-hub-first-deployment-and-data-residency.md).

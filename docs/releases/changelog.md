# Documentation Changelog

## 2026-10-06

### Added
- Modular documentation structure mirroring code: `docs/00-overview/`, `docs/core/`, `docs/modules/<module>/` (household, planner, kids, energy, devices, finance), module manifests, presets and surface profiles
- Open-decisions register, roadmap (proposed), current-implementation snapshot, attention-and-insights platform doc
- ADR-0006 (modular architecture, proposed) and ADR-0007 (interim no authentication, loopback only)
- Specifications: module enablement, audiences/child roles, per-module entity note

### Changed
- Stories moved next to their module (`docs/modules/<m>/stories/`, `docs/core/stories/`); `backlog.yaml` indexes `module`/`submodule`
- Architecture docs moved to `docs/core/`; ADRs to `docs/decisions/`; specifications to `docs/core/specifications/`; product docs to `docs/00-overview/`; Alfred spec to `docs/modules/planner/time-keeper-spec.md`; previous dev-context doc removed (replaced by overview and current-implementation)
- `architecture-overview.md` replaced by `docs/core/architecture.md` (current + modular); the Next.js/PostgreSQL proposal preserved as a non-adopted proposal
- Trust, privacy and connector documents merged and updated for modules, audiences, surfaces and the removal of authentication
- ADR-0005 marked superseded by ADR-0007; US-303 returned to `draft`
- Personas, glossary, vision and market synthesis extended for modules, couples/finance and children
- OpenAPI updated to implemented routes under `/api`


## 2026-09-23

### Added

- Docs-as-code information architecture
- Repository-level agent instructions
- Product vision, personas, customer journey and glossary
- Machine-readable backlog with 24 implementation-ready stories
- Architecture documents, C4/Structurizr DSL and runtime sequences
- ADRs for local-first deployment, Home Assistant and provenance
- Draft domain, permission, data-state and OpenAPI contracts
- Pilot release scope

### Changed

- Moved `docs/architecture.md` to `docs/architecture/architecture-overview.md`
- Moved `docs/market-synthesis-product-backlog.md` to `docs/product/market-synthesis.md`
- Expanded the repository README with documentation entry points

### Preserved

- Existing assets and archived dashboard prototypes remain unchanged.

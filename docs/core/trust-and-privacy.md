# Trust and privacy

- Data states: `docs/specifications/data-states.yaml`. Every record carries source, observed time, ingestion time, availability, state.
- Screen-safe mode masks sensitive details before data leaves the server for shared surfaces.
- Sensitive classes: health, finance, children, location. Default off for shared surfaces; per-person permissions (`docs/specifications/permissions.yaml`).
- Minimise collection; make AI-derived insights opt-in with visible evidence.
- Authentication is currently not implemented in code; ADR-0005 is stale and must be superseded before any LAN exposure (see open items).

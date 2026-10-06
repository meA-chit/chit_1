# Connectors

External sources (calendar subscriptions, weather, tariffs, Home Assistant, health providers, bank imports, school systems) enter through connectors in `core/server` that emit normalized records with provenance. Modules consume normalized records, never raw provider payloads. Connectors must degrade gracefully, protect secrets server-side (no tokens in browser code) and block unsafe URLs. See also `docs/architecture/integrations.md`.

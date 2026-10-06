# Module contract

A module is a folder under `modules/<id>/` with a `module.manifest.yaml` (schema: `core/contracts/module-manifest.schema.yaml`). The registry discovers modules **only** through manifests.

A manifest declares: id, version, dependencies, privacy class, audiences and surfaces it supports, submodules (each independently enable-able), cards, views, permissions, events published/consumed.

A module must:
- work when any dependency is disabled (cards show `unavailable`);
- own its data and migrations (`<module>_NNN_*.sql`);
- expose server routes under `/api/<module>/...`;
- contribute UI only as registered cards/views;
- list its public read APIs and events in `docs/modules/<id>/contracts.md`.

## Settings sections
A module may contribute sections to another module's settings screen: declare `settings_sections` in the manifest (`id`, `submodule`, `title`, `target`, `order`, `surfaces`) and export the component under `ModuleWeb.settings[id]`. The host renders `<SettingsSections target="..." />`; the shell decides which appear (module enabled, surface). Sections persist themselves through the contributor's own `/api/<module>/…` routes.

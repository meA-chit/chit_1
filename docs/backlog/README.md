# Backlog

`backlog.yaml` is the global index of stories, epics and pilot release slices. Story files live next to the module they change:

- `docs/modules/<module>/stories/US-xxx-*.md`
- `docs/core/stories/US-xxx-*.md` (platform stories)

Each story's front matter carries `module` (and `submodule`). Epics (`epics/`) are cross-module outcome groups for the pilot. Add module-level epics under `docs/modules/<module>/` when a module's stories are written.

`module_coverage` in `backlog.yaml` shows which modules still have no stories (household, kids, finance).

Story IDs are stable; moving a story between folders does not change its ID. Status vocabulary is in `docs/README.md`.

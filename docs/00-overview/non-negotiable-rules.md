# Non-negotiable rules

Product and data rules (inherited from the root `AGENTS.md`, restated so they are in the first folder you read):
1. Read-only first. No messaging, schedule changes, appliance control or other side effects without an approved story.
2. Preserve source, observed time, ingestion time, availability and data state on normalized records. Use only states in `docs/core/specifications/data-states.yaml`.
3. Missing information is `unavailable` or `unknown`. Never infer availability from absence.
4. Never label forecast, manual or demo values as measured.
5. Apply screen-safe presentation before returning data for shared displays.
6. Minimise data; sensitive domains (health, finance, children, location) need explicit per-person permissions and are hidden on shared screens by default.

Modularity rules:
7. **Module isolation.** A module never imports another module's code. It uses public contracts and the event catalog only.
8. **One owner per entity.** See the ownership table in `module-map.md`. Others reference by ID.
9. **Everything is a card or view.** UI contributes registered cards/views; the shell never imports module internals.
10. **Nothing hard-codes who sees what.** Visibility comes from household, member and surface configuration plus permissions.
11. **Graceful absence.** A module works when any other module is disabled; cards render unavailable states.
12. **Docs mirror code.** Change behaviour -> update the module's docs in the same PR.
13. **Migrations are namespaced** `<module>_NNN_description.sql` so parallel branches do not collide.
14. **Shared code lives in `core/`** and changes there need review beyond the module owner.

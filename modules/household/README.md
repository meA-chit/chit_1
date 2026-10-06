# `modules/household` — Household & Members

Documentation for this folder: [`docs/modules/household/`](../../docs/modules/household/README.md). **Read it (and `docs/00-overview/README.md`) before coding here.**

Layout:
- `module.manifest.yaml` — id, submodules, cards, permissions, dependencies (the registry reads this)
- `submodules/<name>/{server,web,tests}/` — implementation
- `shared/` — code used by several submodules of this module only

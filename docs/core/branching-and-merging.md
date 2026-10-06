# Branching and merging

- One branch per module/story: `module/<id>/<short-name>`; periodic merges to `main`.
- `.github/CODEOWNERS` maps paths to owners; `core/` requires review from at least two people.
- Manifests, contracts and `docs/` changes ship in the same PR as the code.
- Migrations are namespaced per module; core migrations use the `core_` prefix.
- Feature-flag incomplete modules via enablement config so `main` always runs.
- CI (to be added): lint, tests per module, manifest schema validation, docs link check.

# Modules

One folder per module. Read `docs/00-overview/README.md` first, then `docs/modules/<module>/README.md`. Each module registers through `module.manifest.yaml`.


## Submodule contract (code)
```
modules/<m>/submodules/<s>/
  server/routes.py   def register(router): router.get("/api/<m>/...")(handler)   # handler(ctx, request) -> (status, dict)
  web/index.ts       export default { module: '<m>', cards: { '<card-id>': lazy(() => import('./Card')) } }
  tests/             test_*.py (run by scripts/test-py.sh) and *.test.ts (vitest)
```
Import only `@chit/core` (web) and `chit_server`/`chit_store` public APIs (python). `npm run check:isolation` fails on cross-module references. A submodule's python files load siblings with `chit_server.loader.load_file_module` because folder names contain hyphens.

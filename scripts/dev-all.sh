#!/bin/sh
# One command for contributors: unencrypted dev hub (auto-seeded, ADR-0010) + web client with hot reload.
cd "$(dirname "$0")/.." || exit 1
export CHIT_STORAGE=plain
trap 'kill 0' INT TERM EXIT
PYTHONPATH=core/server:core/store python3 -m chit_server &
npx vite --config apps/web/vite.config.ts &
wait

#!/bin/sh
# One command for contributors (run with CHIT_LAN=1 to also serve the web client to your local network): unencrypted dev hub (auto-seeded, ADR-0010) + web client with hot reload.
cd "$(dirname "$0")/.." || exit 1
export CHIT_STORAGE=plain
trap 'kill 0' INT TERM EXIT
# Prefer the project virtualenv (python3 -m venv .venv && .venv/bin/pip install -r requirements.txt) so the hub finds its dependencies.
# python.org builds of Python ship without trusted CA certificates; fall back to the macOS bundle so HTTPS feeds (weather, calendars, prices) work.
[ -z "$SSL_CERT_FILE" ] && [ -f /etc/ssl/cert.pem ] && export SSL_CERT_FILE=/etc/ssl/cert.pem
PYTHON=python3
[ -x .venv/bin/python3 ] && PYTHON=.venv/bin/python3
PYTHONPATH=core/server:core/store "$PYTHON" -m chit_server &
npx vite --config apps/web/vite.config.ts &
wait

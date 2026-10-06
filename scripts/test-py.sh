#!/bin/sh
# Run every python test folder in the repo (core + each submodule).
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="core/server:core/store${PYTHONPATH:+:$PYTHONPATH}"
status=0
for dir in $(find core modules -type d -name tests -not -path '*/node_modules/*'); do
  ls "$dir"/test_*.py >/dev/null 2>&1 || continue
  echo "== $dir"
  python3 -m unittest discover -s "$dir" -t "$dir" || status=1
done
exit $status

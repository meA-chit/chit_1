"""Seed everything: household fixtures first, then each submodule's server/seed.py (ADR-0010).

    python -m chit_server.seed        # idempotent
"""
from __future__ import annotations

from pathlib import Path

from .loader import load_file_module
from .paths import MODULES_DIR
from . import registry


def _in_dependency_order(manifests):
    """A module is seeded after the modules it depends on (kids reads the chores planner seeds)."""
    done, ordered = set(), []

    def visit(module_id):
        if module_id in done or module_id not in manifests:
            return
        done.add(module_id)
        for dependency in manifests[module_id].get("depends_on", []):
            visit(dependency)
        ordered.append((module_id, manifests[module_id]))
    for module_id in manifests:
        visit(module_id)
    return ordered


def seed_all(store, manifests=None, modules_dir: Path = MODULES_DIR) -> dict:
    from chit_store.cli import seed_households

    manifests = manifests or registry.load_manifests(modules_dir)
    loaded = {"households": seed_households(store)}
    for module_id, manifest in _in_dependency_order(manifests):
        for submodule in manifest.get("submodules", []):
            seed_file = modules_dir / module_id / "submodules" / submodule["id"] / "server" / "seed.py"
            if seed_file.is_file():
                loaded["%s/%s" % (module_id, submodule["id"])] = load_file_module(seed_file).seed(store)
    return loaded


def main() -> None:
    from chit_store import EncryptedHouseholdStore

    print("seeded:", seed_all(EncryptedHouseholdStore()))


if __name__ == "__main__":
    main()

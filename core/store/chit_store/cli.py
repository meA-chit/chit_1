"""python -m chit_store.cli seed|export  (see seed/README.md and ADR-0010)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .store import EncryptedHouseholdStore

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SEED_DIR = REPO_ROOT / "seed" / "households"
MASKED_URL = "https://calendar.example/REPLACE-ME.ics"


def seed_households(store: EncryptedHouseholdStore, directory: Path = DEFAULT_SEED_DIR) -> list[str]:
    """Load every fixture whose household id is not present yet. Returns the ids loaded."""
    loaded = []
    for path in sorted(directory.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        household_id = (document.get("household") or {}).get("id")
        if household_id:
            try:
                store.get_household_document(household_id)
                continue
            except LookupError:
                pass
        loaded.append(store.save_household_setup(document, preserve_ids=True)["household_id"])
    return loaded


def export_household(store: EncryptedHouseholdStore, which: str, include_urls: bool = False) -> dict:
    household_id = store.latest_household_id() if which == "latest" else which
    if household_id is None:
        raise SystemExit("no household to export")
    document = store.get_household_document(household_id)
    document["household"]["id"] = document.pop("id")
    for key in ("created_at", "updated_at"):
        document.pop(key, None)
    for calendar in document["calendars"]:
        calendar.pop("connection_state", None)
        calendar.pop("last_checked_at", None)
        if not include_urls:
            calendar["subscription_url"] = MASKED_URL
    return document


def main(argv: "list[str] | None" = None) -> None:
    parser = argparse.ArgumentParser(prog="chit_store.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    seed = commands.add_parser("seed", help="load seed/households/*.json that are not in the database yet")
    seed.add_argument("--dir", type=Path, default=DEFAULT_SEED_DIR)
    export = commands.add_parser("export", help="print a household document as JSON")
    export.add_argument("household", nargs="?", default="latest", help="household id or 'latest'")
    export.add_argument("--include-urls", action="store_true", help="keep private calendar feed URLs (do not commit!)")
    args = parser.parse_args(argv)

    store = EncryptedHouseholdStore()
    if args.command == "seed":
        loaded = seed_households(store, args.dir)
        print("seeded: %s" % (", ".join(loaded) if loaded else "nothing new"), file=sys.stderr)
    else:
        json.dump(export_household(store, args.household, args.include_urls), sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()

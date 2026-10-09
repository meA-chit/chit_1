"""Operator tool for the hosted pilot (ADR-0014): create a household, invite people, recover access. Run it yourself with the
OWNER database role; it is not reachable over HTTP and it never prints a code except the one you asked for.

    CHIT_DB_OWNER_URL=... CHIT_APP_URL=https://app.chithome.de \\
      PYTHONPATH=core/store python -m chit_store.admin_cli create-household --name "Meyer family" --owner-name Nina
      ... pair --household <id> --member <id>            (new invitation, also the recovery path for a lost mailbox)
      ... list
      ... disable-account --email nina@example.org       (signs the person out everywhere and blocks sign-in)

An invitation is a LINK and a 6-digit CODE. Send them on different channels (for example the link by WhatsApp, the code by voice).
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

DEFAULT_MODULES = "household,planner,kids"        # pilot default (ADR-0013): energy, devices and finance stay off until asked for


def _store():
    owner = os.environ.get("CHIT_DB_OWNER_URL")
    if not owner:
        raise SystemExit("CHIT_DB_OWNER_URL is not set (this tool needs the owner role, not the application role)")
    os.environ["CHIT_STORE_BACKEND"] = "postgres"
    os.environ["CHIT_DB_URL"] = owner
    os.environ.pop("CHIT_PG_TEST", None)
    from chit_store import EncryptedHouseholdStore

    return EncryptedHouseholdStore()


def _accounts(store):
    from chit_store import mailer
    from chit_store.accounts import Accounts

    return Accounts(store, mailer.ConsoleMailer(), os.environ.get("CHIT_TERMS_VERSION", "2026-10-beta-1"))


def _show(pairing: dict) -> None:
    base = os.environ.get("CHIT_APP_URL", "http://localhost:5173").rstrip("/")
    print("\nInvitation (valid 30 minutes, works once)")
    print("  Link: %s/auth/#p=%s" % (base, pairing["link"]))
    print("  Code: %s     <- send this on a DIFFERENT channel than the link" % pairing["code"])


def create_household(args) -> None:
    store = _store()
    created = store.create_household(args.name, args.owner_name, args.timezone, args.country)
    modules = [m.strip() for m in args.modules.split(",") if m.strip()]
    with store._connection() as connection:
        connection.execute("UPDATE households SET modules_configured = 1 WHERE id = ?", (created["household_id"],))
        for module in modules:
            connection.execute("INSERT INTO household_modules(household_id, module_id) VALUES (?, ?) ON CONFLICT DO NOTHING", (created["household_id"], module))
    pairing = _accounts(store).issue_pairing(created["household_id"], created["owner_member_id"], "owner", "operator")
    print("Household %s created (id %s), owner member %s, modules: %s" % (args.name, created["household_id"], created["owner_member_id"], ", ".join(modules)))
    _show(pairing)


def pair(args) -> None:
    store = _store()
    _show(_accounts(store).issue_pairing(args.household, args.member, args.role, "operator"))


def list_all(args) -> None:
    store = _store()
    with store._connection() as c:
        for hid, name, created in c.execute("SELECT id, name, created_at FROM households ORDER BY seq").fetchall():
            print("%s  %s  (created %s)" % (hid, name, created[:10]))
            for mid, mname, role, access, email in c.execute(
                    "SELECT m.id, m.name, m.role, a.role, x.email FROM household_members m "
                    "LEFT JOIN auth_memberships a ON a.household_id = m.household_id AND a.member_id = m.id "
                    "LEFT JOIN auth_accounts x ON x.id = a.account_id WHERE m.household_id = ? ORDER BY m.seq", (hid,)).fetchall():
                print("    %-24s %-6s %-26s %s" % (mid, role, mname, ("%s: %s" % (access, email)) if email else "no account"))


def disable_account(args) -> None:
    store = _store()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
    with store._connection() as c:
        row = c.execute("UPDATE auth_accounts SET disabled_at = ? WHERE lower(email) = ? AND disabled_at IS NULL RETURNING id", (now, args.email.strip().lower())).fetchone()
        if not row:
            raise SystemExit("no active account with that email")
        c.execute("UPDATE auth_sessions SET revoked_at = ? WHERE account_id = ? AND revoked_at IS NULL", (now, row[0]))
    print("Account disabled and signed out everywhere.")


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("create-household", help="create a household and the owner's invitation")
    c.add_argument("--name", required=True)
    c.add_argument("--owner-name", required=True)
    c.add_argument("--timezone", default="Europe/Berlin")
    c.add_argument("--country", default="DE")
    c.add_argument("--modules", default=DEFAULT_MODULES, help="comma list (default %(default)s)")
    c.set_defaults(run=create_household)
    p = sub.add_parser("pair", help="issue an invitation for an adult household member (also for recovery)")
    p.add_argument("--household", required=True)
    p.add_argument("--member", required=True)
    p.add_argument("--role", choices=("owner", "adult"), default="adult")
    p.set_defaults(run=pair)
    sub.add_parser("list", help="households, members and who has an account").set_defaults(run=list_all)
    d = sub.add_parser("disable-account")
    d.add_argument("--email", required=True)
    d.set_defaults(run=disable_account)
    args = parser.parse_args(argv)
    args.run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

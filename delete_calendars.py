#!/usr/bin/env python3
"""delete_calendars.py -- List and delete Synology calendars via DSM API.

CalDAV does not allow DELETE on calendar collections in Synology (returns 405).
This script uses the native SYNO.Cal.Cal HTTP API instead.

Usage:
    # List all calendars:
    python delete_calendars.py --list

    # Delete by exact display name:
    python delete_calendars.py --delete "Futbol Barsa" "Formula 1"

    # Preview without deleting:
    python delete_calendars.py --delete "Formula 1" --dry-run
"""

import argparse
import sys
import urllib3
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from ics_sync.config import load_config
from ics_sync.dsm_client import DSMSession


def cmd_list(session: DSMSession) -> None:
    cals = session.list_calendars()
    print(f"\nCalendars on your Synology ({len(cals)} total):")
    print("-" * 50)
    for cal in cals:
        shared = "" if cal.get("is_personal", True) else "  [shared]"
        print(f"  * {cal['cal_displayname']}{shared}")
    print("-" * 50)


def cmd_delete(session: DSMSession, names: list[str], dry_run: bool) -> None:
    cals = session.list_calendars()
    cal_map = {c["cal_displayname"]: c for c in cals}

    found = [n for n in names if n in cal_map]
    not_found = [n for n in names if n not in cal_map]

    if not_found:
        print("\nNot found (verify exact name with --list):")
        for n in not_found:
            print(f"  x '{n}'")

    if not found:
        print("\nNothing to delete.")
        return

    print("\nCalendars to delete:")
    for n in found:
        print(f"  * '{n}'")

    if dry_run:
        print("\n[DRY RUN] Nothing deleted. Remove --dry-run to execute.")
        return

    confirm = input("\nConfirm PERMANENT deletion? Type 'si' to proceed: ").strip().lower()
    if confirm != "si":
        print("Cancelled.")
        return

    for name in found:
        cal_id = cal_map[name]["cal_id"]
        ok = session.delete_calendar(cal_id)
        symbol = "OK" if ok else "FAIL"
        print(f"  [{symbol}] '{name}'")

    print("\nDone.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Synology calendars via DSM API")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--list", action="store_true", help="List all calendars")
    parser.add_argument("--delete", nargs="+", metavar="NAME", help="Exact names to delete")
    parser.add_argument("--dry-run", action="store_true", help="Simulate deletion without executing")
    args = parser.parse_args()

    cfg = load_config(args.config)
    c = cfg["caldav"]
    p = urlparse(c["url"])
    base = f"{p.scheme}://{p.netloc}"
    verify = c.get("verify_ssl", True)

    print(f"Connecting to {base} ...")
    try:
        import logging
        session = DSMSession(base, c["username"], c["password"], verify, logging.getLogger("del"))
        print("Login OK\n")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    try:
        if args.delete:
            cmd_delete(session, args.delete, args.dry_run)
        else:
            cmd_list(session)
    finally:
        session.logout()


if __name__ == "__main__":
    main()

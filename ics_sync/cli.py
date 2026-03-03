"""Command-line entry point for ICS → Synology CalDAV sync."""
from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

from caldav import DAVClient

from .config import load_config
from .dsm_client import DSMSession, dsm_ensure_calendars
from .logging_ import setup_logging
from .sync import sync_source


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments and run the full sync pipeline.

    Args:
        argv: Argument list (uses ``sys.argv`` when ``None``).
    """
    parser = argparse.ArgumentParser(
        prog="ics-sync",
        description="Sync external ICS feeds to Synology Calendar via CalDAV",
    )
    parser.add_argument(
        "--config", default="config.json", help="Path to config.json (default: config.json)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch ICS feeds but do not write any changes to CalDAV",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable DEBUG-level logging"
    )
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    log = setup_logging(args.verbose, cfg.get("log_file"))

    caldav_cfg = cfg["caldav"]
    url: str = caldav_cfg["url"]
    username: str = caldav_cfg["username"]
    password: str = caldav_cfg["password"]
    verify_ssl: bool = caldav_cfg.get("verify_ssl", True)

    log.info(f"Connecting to CalDAV at {url} as '{username}'")
    try:
        client = DAVClient(
            url=url,
            username=username,
            password=password,
            ssl_verify_cert=verify_ssl,
        )
        principal = client.principal()
        log.info("CalDAV connection OK")
    except Exception as exc:
        log.error(f"CalDAV connection failed: {exc}")
        log.error(
            "Check: NAS hostname/port, username/password, "
            "CalDAV enabled in DSM Control Panel"
        )
        sys.exit(1)

    # DSM pre-flight: ensure all target calendars exist and are visible in
    # Synology Calendar UI + iOS.  Calendars created via CalDAV make_calendar()
    # are invisible in the UI — creating them via DSM API first fixes this.
    if not args.dry_run:
        parsed = urlparse(url)
        dsm_base = f"{parsed.scheme}://{parsed.netloc}"
        calendar_names = [s["calendar_name"] for s in cfg.get("sources", [])]
        try:
            dsm = DSMSession(dsm_base, username, password, verify_ssl, log)
            dsm_ensure_calendars(dsm, calendar_names, log)
        except RuntimeError as exc:
            log.warning(f"DSM pre-flight skipped: {exc}")
        except Exception as exc:
            log.warning(f"DSM pre-flight error (will rely on CalDAV fallback): {exc}")

    total: dict[str, int] = {
        "created": 0, "updated": 0, "deleted": 0, "errors": 0, "skipped": 0,
    }
    for source in cfg.get("sources", []):
        try:
            stats = sync_source(
                source, principal, dry_run=args.dry_run, log=log, verify_ssl=verify_ssl
            )
        except BaseException as exc:
            log.error(
                f"[{source.get('calendar_name', '?')}] Fatal error, skipping source: {exc}"
            )
            total["errors"] += 1
            continue
        for k in total:
            total[k] += stats[k]

    log.info(
        f"Sync complete — total: "
        f"created={total['created']}, updated={total['updated']}, "
        f"skipped={total['skipped']}, deleted={total['deleted']}, "
        f"errors={total['errors']}"
    )
    if total["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

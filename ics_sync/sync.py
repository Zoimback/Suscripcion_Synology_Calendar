"""Core sync engine — orchestrates ICS fetch → CalDAV upsert / delete."""
from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone

from icalendar import Calendar

from .caldav_helpers import get_existing_uids, get_or_create_calendar
from .fetcher import fetch_ics
from .grouping import build_ics_for_group, group_vevents

# ---------------------------------------------------------------------------
# Internal retry helpers
# ---------------------------------------------------------------------------

_MAX_ATTEMPTS = 3
_RETRY_DELAY = 5  # seconds between retry attempts


def _to_utc(dt_prop):
    """Coerce a vObject date/datetime property to a timezone-aware datetime."""
    d = getattr(dt_prop, "dt", dt_prop)
    if hasattr(d, "tzinfo") and d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def _save_with_retry(event, ics_data: bytes) -> bool:
    """Overwrite *event.data* with *ics_data* and call ``save()``.

    Returns:
        ``True``  — the server accepted the update.
        ``False`` — all retries exhausted.

    ``AttributeError`` from the caldav library means the server returned an
    empty body on a 2xx response; that counts as success.
    """
    for attempt in range(_MAX_ATTEMPTS):
        try:
            event.data = ics_data
            event.save()
            return True
        except AttributeError:
            return True  # empty-body 2xx — event was stored OK
        except Exception:
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_RETRY_DELAY)
    return False


def _put_with_retry(caldav_cal, ics_data: bytes, obj_id: str) -> bool | None:
    """PUT *ics_data* to *caldav_cal* at a deterministic *obj_id* URL.

    Returns:
        ``True``  — success.
        ``None``  — ``OSError`` (Windows-only socket quirk; skip gracefully).
        ``False`` — server error after all retries.
    """
    for attempt in range(_MAX_ATTEMPTS):
        try:
            caldav_cal.save_event(ics_data, no_overwrite=False, obj_id=obj_id)
            return True
        except AttributeError:
            return True  # empty-body 2xx — event stored
        except OSError:
            return None  # Windows socket issue — not a real failure
        except Exception:
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_RETRY_DELAY)
    return False


# ---------------------------------------------------------------------------
# Upsert logic (single VEVENT group)
# ---------------------------------------------------------------------------

def _upsert_group(
    uid: str,
    vevents: list,
    source_cal: Calendar,
    caldav_cal,
    existing_uids: dict,
    log: logging.Logger,
    calendar_name: str,
) -> str:
    """Upsert one VEVENT group (master + optional overrides).

    Returns one of: ``'created'``, ``'updated'``, ``'skipped'``, ``'error'``.
    """
    ics_data = build_ics_for_group(source_cal, vevents)
    master = vevents[0]

    # ---- UPDATE path -------------------------------------------------------
    if uid in existing_uids:
        existing_event = existing_uids[uid]
        existing_cal = Calendar.from_ical(existing_event.data)
        existing_master = next(
            (c for c in existing_cal.walk() if c.name == "VEVENT"), None
        )

        src_lastmod = master.get("LAST-MODIFIED") or master.get("DTSTAMP")
        dst_lastmod = (
            existing_master.get("LAST-MODIFIED") or existing_master.get("DTSTAMP")
            if existing_master
            else None
        )

        # Force an update when DTSTART changed — Google Calendar re-exports the
        # RRULE master segment when a recurring event is modified, making a pure
        # LAST-MODIFIED comparison unreliable.
        src_dtstart = master.get("DTSTART")
        dst_dtstart = existing_master.get("DTSTART") if existing_master else None
        dtstart_changed = bool(
            src_dtstart
            and dst_dtstart
            and _to_utc(src_dtstart) != _to_utc(dst_dtstart)
        )

        if not dtstart_changed and src_lastmod and dst_lastmod:
            if _to_utc(src_lastmod) <= _to_utc(dst_lastmod):
                return "skipped"

        saved = _save_with_retry(existing_event, ics_data)
        if not saved and len(vevents) > 1:
            # Fallback: push master first, then accumulate overrides one-by-one.
            _save_with_retry(existing_event, build_ics_for_group(source_cal, [master]))
            accepted: list = []
            for override in vevents[1:]:
                candidate = [master] + accepted + [override]
                if _save_with_retry(existing_event, build_ics_for_group(source_cal, candidate)):
                    accepted.append(override)
                else:
                    log.debug(
                        f"[{calendar_name}] Skipped incompatible override "
                        f"RECURRENCE-ID={override.get('RECURRENCE-ID')} UID={uid}"
                    )

        log.debug(f"[{calendar_name}] Updated UID={uid} ({len(vevents)} component(s))")
        return "updated"

    # ---- CREATE path -------------------------------------------------------
    # Use a deterministic URL (MD5 of base UID) so re-runs are idempotent.
    obj_id = hashlib.md5(uid.encode()).hexdigest()
    result = _put_with_retry(caldav_cal, ics_data, obj_id)

    if result is None:
        log.warning(f"[{calendar_name}] OSError (Windows-only) skipped UID={uid}")
        return "skipped"

    if result is False and len(vevents) > 1:
        # Full group rejected (Synology 500 on some RECURRENCE-ID combos).
        # Establish the master first, then accumulate overrides one-by-one.
        master_data = build_ics_for_group(source_cal, [master])
        result = _put_with_retry(caldav_cal, master_data, obj_id)
        if result is True:
            accepted = []
            for override in vevents[1:]:
                candidate = build_ics_for_group(
                    source_cal, [master] + accepted + [override]
                )
                if _put_with_retry(caldav_cal, candidate, obj_id) is True:
                    accepted.append(override)
                else:
                    log.debug(
                        f"[{calendar_name}] Skipped incompatible override "
                        f"RECURRENCE-ID={override.get('RECURRENCE-ID')} UID={uid}"
                    )
            log.warning(
                f"[{calendar_name}] Group fallback: master + "
                f"{len(accepted)}/{len(vevents) - 1} override(s) accepted UID={uid}"
            )

    if result is False:
        log.error(f"[{calendar_name}] Failed to upsert UID={uid}")
        return "error"

    n_overrides = len(vevents) - 1
    label = f" + {n_overrides} override(s)" if n_overrides else ""
    log.debug(f"[{calendar_name}] Created UID={uid}{label}")
    return "created"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sync_source(
    source: dict,
    principal,
    *,
    dry_run: bool,
    log: logging.Logger,
    verify_ssl: bool = True,
) -> dict[str, int]:
    """Sync one ICS source to its target CalDAV calendar.

    Args:
        source:     Source dict from ``config.json`` with keys ``url``,
                    ``calendar_name`` and optionally ``delete_removed_events``.
        principal:  Authenticated CalDAV principal from ``DAVClient``.
        dry_run:    When ``True``, fetch ICS but make no CalDAV changes.
        log:        Logger instance.
        verify_ssl: Passed through to :func:`fetch_ics`.

    Returns:
        Stats dict with keys ``created``, ``updated``, ``deleted``,
        ``errors``, ``skipped``.
    """
    stats: dict[str, int] = {
        "created": 0, "updated": 0, "deleted": 0, "errors": 0, "skipped": 0,
    }

    url: str = source["url"]
    calendar_name: str = source["calendar_name"]
    delete_removed: bool = source.get("delete_removed_events", False)

    log.info(f"[{calendar_name}] Fetching ICS from {url}")
    try:
        source_cal = fetch_ics(url, verify_ssl=verify_ssl)
    except Exception as exc:
        log.error(f"[{calendar_name}] Failed to fetch ICS: {exc}")
        stats["errors"] += 1
        return stats

    source_events = group_vevents(source_cal)
    log.info(f"[{calendar_name}] Found {len(source_events)} event(s) to sync")

    if dry_run:
        log.info(f"[{calendar_name}] DRY RUN — no changes will be made")
        return stats

    caldav_cal = get_or_create_calendar(principal, calendar_name, log)
    existing_uids = get_existing_uids(caldav_cal)
    log.info(f"[{calendar_name}] {len(existing_uids)} event(s) already in CalDAV")

    for uid, vevents in source_events.items():
        try:
            outcome = _upsert_group(
                uid, vevents, source_cal, caldav_cal, existing_uids, log, calendar_name
            )
            stats[outcome] += 1
        except Exception as exc:
            log.error(f"[{calendar_name}] Error upserting UID={uid}: {exc}")
            stats["errors"] += 1

    if delete_removed:
        removed_uids = set(existing_uids.keys()) - set(source_events.keys())
        for uid in removed_uids:
            for attempt in range(_MAX_ATTEMPTS):
                try:
                    existing_uids[uid].delete()
                    stats["deleted"] += 1
                    log.debug(f"[{calendar_name}] Deleted removed event UID={uid}")
                    break
                except Exception as exc:
                    if attempt < _MAX_ATTEMPTS - 1:
                        time.sleep(_RETRY_DELAY)
                        continue
                    log.error(f"[{calendar_name}] Error deleting UID={uid}: {exc}")
                    stats["errors"] += 1

    log.info(
        f"[{calendar_name}] Done — "
        f"created={stats['created']}, updated={stats['updated']}, "
        f"skipped={stats['skipped']}, deleted={stats['deleted']}, "
        f"errors={stats['errors']}"
    )
    return stats

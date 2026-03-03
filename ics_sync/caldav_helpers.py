"""CalDAV helper utilities for Synology Calendar integration."""
from __future__ import annotations

import logging
import re
import unicodedata

from icalendar import Calendar

# Synology Calendar UI creates calendars with short random IDs (e.g. 'ceuoklky').
# CalDAV make_calendar() creates them with UUID IDs that are invisible in the UI.
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-", re.I)


def _norm(s: str) -> str:
    """Normalize unicode and casefold *s* for locale-insensitive name comparison."""
    return unicodedata.normalize("NFC", s or "").casefold()


def get_or_create_calendar(principal, calendar_name: str, log: logging.Logger):
    """Return the named CalDAV calendar, preferring the short-ID (visible) one.

    When both a short-ID calendar and a UUID-ID calendar share the same display
    name, the short-ID one (created via Synology UI / DSM API) is returned
    because it is the one visible in iOS Calendar.
    """
    name_norm = _norm(calendar_name)
    matches = [cal for cal in principal.calendars() if _norm(cal.name) == name_norm]

    if not matches:
        log.warning(
            f"Calendar '{calendar_name}' not found — "
            "creating via CalDAV fallback (may be invisible in UI)"
        )
        return principal.make_calendar(name=calendar_name)

    # Prefer short-ID (Synology-created) over UUID (CalDAV-created).
    non_uuid = [c for c in matches if not _UUID_RE.search(str(c.url))]
    chosen = non_uuid[0] if non_uuid else matches[0]

    if len(matches) > 1:
        chosen_id = str(chosen.url).rstrip("/").split("/")[-1]
        log.debug(
            f"'{calendar_name}': {len(matches)} duplicates found, using '{chosen_id}'"
        )
    else:
        log.debug(f"Found calendar: '{calendar_name}'")

    return chosen


def get_existing_uids(caldav_calendar) -> dict[str, object]:
    """Return a ``{UID: caldav_event}`` mapping for all events in *caldav_calendar*."""
    uid_map: dict[str, object] = {}
    try:
        events = caldav_calendar.events()
    except Exception:
        events = []

    for ev in events:
        try:
            cal = Calendar.from_ical(ev.data)
            for component in cal.walk():
                if component.name == "VEVENT":
                    uid = str(component.get("UID", ""))
                    if uid:
                        uid_map[uid] = ev
        except Exception:
            continue

    return uid_map

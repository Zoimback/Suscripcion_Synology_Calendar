"""Pure VEVENT grouping logic — no I/O, fully unit-testable.

Handles Google Calendar quirks:

* Recurrence overrides with modified UIDs
  (``base_uid_R<YYYYMMDD>T<HHMMSS>Z@host``).
* Multiple RRULE masters exported for the same series when it is modified —
  only the master with the latest DTSTART is kept.
* Orphan groups (only RECURRENCE-ID overrides, no master VEVENT) are
  discarded. Synology silently drops them, causing infinite re-creates on
  every sync run.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime

from icalendar import Calendar

_GOOGLE_RECUR_RE = re.compile(r"_R\d{8}T\d{6}Z?(?=@|$)")


def base_uid(uid: str) -> str:
    """Strip a Google-style ``_R<date>T<time>`` suffix to get the canonical UID."""
    return _GOOGLE_RECUR_RE.sub("", uid)


def _dtstart_as_date(vevent):
    """Return DTSTART as a ``date`` for comparison; ``datetime.min.date()`` if absent."""
    dtstart = vevent.get("DTSTART")
    if dtstart is None:
        return datetime.min.date()
    dt = dtstart.dt
    return dt.date() if isinstance(dt, datetime) else dt


def group_vevents(source_cal: Calendar) -> dict[str, list]:
    """Parse *source_cal* and return a ``{uid: [master, override…]}`` mapping.

    Rules:

    * Non-recurring (standalone) events use their **full** UID as key.
    * RRULE masters and RECURRENCE-ID overrides share the *base* UID.
    * When multiple RRULE masters share the same base UID (Google split-series
      export), only the master with the **latest DTSTART** is retained.
    * Orphan groups — only RECURRENCE-ID overrides, no master — are dropped.
    """
    groups: dict[str, list] = {}

    for component in source_cal.walk():
        if component.name != "VEVENT":
            continue

        uid = str(component.get("UID", ""))
        if not uid:
            uid = str(uuid.uuid4())
            component.add("UID", uid)

        b_uid = base_uid(uid)
        has_rrule = component.get("RRULE") is not None
        is_override = component.get("RECURRENCE-ID") is not None

        if is_override or has_rrule:
            # Normalise UID to the canonical base form for the whole group.
            del component["UID"]
            component.add("UID", b_uid)

            if is_override:
                groups.setdefault(b_uid, [])
                groups[b_uid].append(component)
            else:
                # RRULE master — keep only the one with the latest DTSTART.
                existing = groups.get(b_uid, [])
                overrides = [c for c in existing if c.get("RECURRENCE-ID") is not None]
                masters = [c for c in existing if c.get("RECURRENCE-ID") is None]
                latest = max(masters + [component], key=_dtstart_as_date)
                groups[b_uid] = [latest] + overrides
        else:
            # Standalone / non-recurring — preserve the full UID as the key.
            existing = groups.get(uid, [])
            groups[uid] = [component] + [c for c in existing if c is not component]

    # Discard orphan groups (only overrides, no master RRULE/VEVENT).
    orphan_keys = [
        k for k, evs in groups.items()
        if not any(ev.get("RECURRENCE-ID") is None for ev in evs)
    ]
    for k in orphan_keys:
        del groups[k]

    return groups


def build_ics_for_group(source_cal: Calendar, vevents: list) -> bytes:
    """Wrap one or more VEVENTs into a single VCALENDAR, preserving VTIMEZONEs.

    RFC 5545 requires master + RECURRENCE-ID overrides to be stored as one
    CalDAV object.  Sending overrides as standalone objects is rejected by
    Synology CalDAV.
    """
    from icalendar import Calendar as _Cal  # local import avoids circular refs

    new_cal = _Cal()
    new_cal.add("PRODID", "-//SynologyICSSync//EN")
    new_cal.add("VERSION", "2.0")

    # Collect TZID references from every event in the group.
    event_tzids: set[str] = set()
    for vevent in vevents:
        for prop in vevent.values():
            if hasattr(prop, "params") and "TZID" in prop.params:
                event_tzids.add(prop.params["TZID"])

    for component in source_cal.walk():
        if component.name == "VTIMEZONE":
            if str(component.get("TZID", "")) in event_tzids:
                new_cal.add_component(component)

    for vevent in vevents:
        new_cal.add_component(vevent)

    return new_cal.to_ical()

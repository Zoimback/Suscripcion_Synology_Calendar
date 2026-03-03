#!/usr/bin/env python3
"""Backward-compatible entry point for ICS → Synology CalDAV sync.

All logic lives in ``ics_sync/``.  This file exists only for convenience
so the script can still be launched as::

    python sync_ics_to_caldav.py [--config config.json] [--dry-run] [--verbose]

For direct module invocation use::

    python -m ics_sync.cli [options]
"""
from ics_sync.cli import main

if __name__ == "__main__":
    main()

"""ics_sync — ICS subscription calendar → Synology CalDAV sync package.

Public API
----------
The most commonly used symbols are re-exported here for convenience:

    from ics_sync import main, sync_source, load_config

For command-line usage, see ``ics_sync.cli`` or run::

    python -m ics_sync.cli --help
"""
from .cli import main
from .config import load_config
from .grouping import base_uid, build_ics_for_group, group_vevents
from .sync import sync_source

__all__ = [
    "main",
    "load_config",
    "base_uid",
    "build_ics_for_group",
    "group_vevents",
    "sync_source",
]

"""Logging setup for ICS → CalDAV sync."""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    verbose: bool,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Configure root logging and return the ``ics-sync`` logger.

    Args:
        verbose:  Enable DEBUG-level output when True; INFO otherwise.
        log_file: Optional path to a log file.  Failures to open the file are
                  non-fatal — logging falls back to stdout only.
    """
    level = logging.DEBUG if verbose else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        try:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
        except OSError as exc:
            print(
                f"[WARN] Cannot open log file '{log_file}': {exc}"
                " — logging to stdout only",
                flush=True,
            )

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )
    return logging.getLogger("ics-sync")

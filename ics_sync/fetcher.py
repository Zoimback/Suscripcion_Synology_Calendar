"""HTTP ICS feed fetcher with automatic retry and exponential back-off."""
import time

import requests
from icalendar import Calendar


def fetch_ics(
    url: str,
    *,
    timeout: int = 30,
    verify_ssl: bool = True,
    retries: int = 3,
) -> Calendar:
    """Download and parse an ICS calendar from *url*.

    Retries up to *retries* times with exponential back-off (2 s, 4 s …) on
    any transient failure.

    Args:
        url:        Full HTTP/HTTPS URL of the ICS feed.
        timeout:    Request timeout in seconds (per attempt).
        verify_ssl: Verify TLS certificates.  Set False only for self-signed
                    NAS certificates.
        retries:    Maximum number of attempts before raising.

    Returns:
        Parsed :class:`icalendar.Calendar` object.

    Raises:
        The last exception raised after all retries are exhausted.
    """
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                url,
                timeout=timeout,
                verify=verify_ssl,
                headers={"User-Agent": "SynologyICSSync/1.0"},
                stream=True,
            )
            response.raise_for_status()
            raw = b"".join(response.iter_content(chunk_size=65_536))
            return Calendar.from_ical(raw)
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(2 ** attempt)  # 2 s, 4 s
    raise last_exc

"""Lightweight Synology DSM HTTP API client for calendar management.

Calendars created via this API appear in Synology Calendar UI and iOS.
Calendars created via CalDAV ``make_calendar()`` are invisible in the UI —
hence we always create them through this client first.
"""
from __future__ import annotations

import logging

import requests


class DSMSession:
    """Session wrapper around the Synology DSM HTTP API (``SYNO.Cal.Cal``).

    Typical usage::

        session = DSMSession(base_url, username, password, verify_ssl, log)
        session.create_calendar("My Calendar")
        session.logout()
    """

    DSM_COLORS: list[str] = [
        "#e5604f", "#e07931", "#cc9a28", "#7faa12", "#23a267",
        "#0099cc", "#3d5fa8", "#8860c4", "#c95ea5", "#626f80",
    ]

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool,
        log: logging.Logger,
    ) -> None:
        self.base = base_url
        self.verify = verify_ssl
        self.log = log
        self.headers: dict[str, str] = {}
        self._session = requests.Session()
        self._login(username, password)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _login(self, username: str, password: str) -> None:
        """Authenticate against DSM and store the SynoToken."""
        params = dict(
            api="SYNO.API.Auth",
            version="6",
            method="login",
            account=username,
            passwd=password,
            session="Calendar",
            format="cookie",
            enable_syno_token="yes",
        )
        r = self._session.get(
            f"{self.base}/webapi/auth.cgi",
            params=params,
            verify=self.verify,
            timeout=15,
        )
        data = r.json()
        if not data.get("success"):
            code = data.get("error", {}).get("code", "?")
            if code == 403:
                raise RuntimeError(
                    "DSM 2FA is enabled. Use an app-specific password "
                    "(DSM > Account > Security > App Passwords) in config.json."
                )
            raise RuntimeError(f"DSM login failed (code {code}).")
        self.headers["X-SYNO-TOKEN"] = data["data"].get("synotoken", "")

    def logout(self) -> None:
        """Log out and invalidate the DSM session."""
        try:
            self._session.get(
                f"{self.base}/webapi/auth.cgi",
                params=dict(
                    api="SYNO.API.Auth",
                    version="6",
                    method="logout",
                    session="Calendar",
                ),
                headers=self.headers,
                verify=self.verify,
                timeout=10,
            )
        except Exception:
            pass  # best-effort logout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _api(self, **params) -> dict:
        """Make a GET request to DSM entry.cgi and return the JSON response."""
        r = self._session.get(
            f"{self.base}/webapi/entry.cgi",
            params=params,
            headers=self.headers,
            verify=self.verify,
            timeout=15,
        )
        return r.json()

    # ------------------------------------------------------------------
    # Calendar operations
    # ------------------------------------------------------------------

    def list_calendars(self) -> list[dict]:
        """Return the raw list of calendar dicts from the DSM API."""
        data = self._api(api="SYNO.Cal.Cal", version="1", method="list")
        if not data.get("success"):
            return []
        return data.get("data", [])

    def existing_calendar_names(self) -> set[str]:
        """Return the display names of all calendars on the NAS."""
        return {cal["cal_displayname"] for cal in self.list_calendars()}

    def create_calendar(self, name: str, color: str = "#0099cc") -> bool:
        """Create a calendar via DSM API.  Returns ``True`` on success."""
        data = self._api(
            api="SYNO.Cal.Cal", version="1", method="create", name=name, color=color
        )
        return data.get("success", False)

    def delete_calendar(self, cal_id: str) -> bool:
        """Delete a calendar by its internal ``cal_id``.  Returns ``True`` on success."""
        data = self._api(
            api="SYNO.Cal.Cal", version="1", method="delete", cal_id=cal_id
        )
        return data.get("success", False)


# ---------------------------------------------------------------------------
# High-level helpers
# ---------------------------------------------------------------------------

def dsm_ensure_calendars(
    dsm: DSMSession,
    calendar_names: list[str],
    log: logging.Logger,
) -> None:
    """Create any missing calendars via the DSM API.

    Calendars created here appear in Synology Calendar UI and are visible in
    iOS Calendar via CalDAV.  This must run before the CalDAV upsert so the
    target calendar exists and is visible.
    """
    existing = dsm.existing_calendar_names()
    colors = DSMSession.DSM_COLORS
    for i, name in enumerate(calendar_names):
        if name not in existing:
            color = colors[i % len(colors)]
            ok = dsm.create_calendar(name, color=color)
            if ok:
                log.info(f"Created calendar via DSM API: '{name}' (color {color})")
            else:
                log.warning(
                    f"DSM could not create calendar '{name}' — CalDAV fallback will be used"
                )
        else:
            log.debug(f"Calendar already exists in DSM: '{name}'")

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import urllib.request
import urllib.error

from app.core.config import settings

logger = logging.getLogger(__name__)

_RELAY_ON = "ON"
_RELAY_OFF = "OFF"


class RelayService:
    """Handles communication with the ESP32 relay board over HTTP."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.esp_is_reachable: bool = False
        self.last_status_ts: float = 0.0
        self._demo_mode: bool = settings.demo_mode

    # ------------------------------------------------------------------
    # Demo mode
    # ------------------------------------------------------------------

    def set_demo_mode(self, enabled: bool) -> None:
        with self._lock:
            self._demo_mode = enabled
            settings.demo_mode = enabled  # update shared settings too
        logger.info("Demo mode set to %s", enabled)

    @property
    def demo_mode(self) -> bool:
        return self._demo_mode

    # ------------------------------------------------------------------
    # Internal HTTP helper
    # ------------------------------------------------------------------

    def _get(self, path: str, timeout: Optional[float] = None) -> Optional[str]:
        """Send a GET request to the ESP32 and return the response body or None on failure."""
        if timeout is None:
            timeout = settings.esp32_timeout
        url = f"http://{settings.esp32_host}:{settings.esp32_port}{path}"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return body
        except Exception as exc:
            logger.warning("ESP32 request failed (%s): %s", url, exc)
            return None

    # ------------------------------------------------------------------
    # Relay control
    # ------------------------------------------------------------------

    def turn_on(self, ch: int) -> bool:
        """Activate relay for channel *ch*. Returns True on success."""
        if self._demo_mode:
            logger.debug("Demo mode: turn_on ch=%d (no-op)", ch)
            self.esp_is_reachable = True
            return True
        result = self._get(f"/relay?ch={ch}&state=ON")
        ok = result is not None
        self.esp_is_reachable = ok
        self.last_status_ts = time.time()
        return ok

    def turn_off(self, ch: int) -> bool:
        """Deactivate relay for channel *ch*. Returns True on success."""
        if self._demo_mode:
            logger.debug("Demo mode: turn_off ch=%d (no-op)", ch)
            self.esp_is_reachable = True
            return True
        result = self._get(f"/relay?ch={ch}&state=OFF")
        ok = result is not None
        self.esp_is_reachable = ok
        self.last_status_ts = time.time()
        return ok

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_esp32_status(self) -> Optional[str]:
        """Return raw status string from ESP32 or None if unreachable."""
        if self._demo_mode:
            self.esp_is_reachable = True
            self.last_status_ts = time.time()
            return "demo"
        result = self._get("/status")
        if result is not None:
            self.esp_is_reachable = True
        else:
            self.esp_is_reachable = False
        self.last_status_ts = time.time()
        return result


relay_service = RelayService()

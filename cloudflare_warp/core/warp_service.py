"""Core WARP service layer: wraps warp-cli if present, falls back to simulation."""

import subprocess
import shutil
import platform
import threading
import time
from enum import Enum


class WarpStatus(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    DISCONNECTING = "Disconnecting"
    ERROR = "Error"


class WarpService:
    """Manages Cloudflare WARP connection state.

    Tries to use the real warp-cli executable when available;
    otherwise simulates state changes for development/demo purposes.
    """

    _WARP_CLI_PATHS = [
        r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe",
        "/usr/bin/warp-cli",
        "/usr/local/bin/warp-cli",
    ]

    def __init__(self):
        self._status = WarpStatus.DISCONNECTED
        self._cli_path = self._detect_cli()
        self._lock = threading.Lock()
        self._callbacks = []
        self._connection_info = {
            "ip": "",
            "city": "",
            "country": "",
            "colo": "",
            "account_type": "WARP",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def status(self) -> WarpStatus:
        with self._lock:
            return self._status

    @property
    def connection_info(self) -> dict:
        with self._lock:
            return dict(self._connection_info)

    @property
    def is_real_client(self) -> bool:
        return self._cli_path is not None

    def connect(self):
        """Start a connection (async)."""
        threading.Thread(target=self._do_connect, daemon=True).start()

    def disconnect(self):
        """Disconnect (async)."""
        threading.Thread(target=self._do_disconnect, daemon=True).start()

    def add_status_callback(self, callback):
        """Register a callable(WarpStatus) to be notified on status changes."""
        self._callbacks.append(callback)

    def remove_status_callback(self, callback):
        self._callbacks.remove(callback)

    def refresh_status(self):
        """Refresh status from warp-cli (if available)."""
        if self._cli_path:
            threading.Thread(target=self._poll_cli_status, daemon=True).start()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_cli(self):
        for path in self._WARP_CLI_PATHS:
            if shutil.which(path) or (platform.system() == "Windows" and _path_exists(path)):
                return path
        return None

    def _set_status(self, new_status: WarpStatus):
        with self._lock:
            if self._status == new_status:
                return
            self._status = new_status
        for cb in list(self._callbacks):
            try:
                cb(new_status)
            except Exception:
                pass

    def _do_connect(self):
        self._set_status(WarpStatus.CONNECTING)
        if self._cli_path:
            ok = self._run_cli(["connect"])
            if ok:
                self._poll_cli_status(wait=True)
            else:
                self._set_status(WarpStatus.ERROR)
        else:
            # Simulate connection delay
            time.sleep(2)
            with self._lock:
                self._connection_info.update({
                    "ip": "104.18.0.1",
                    "city": "San Francisco",
                    "country": "US",
                    "colo": "SFO",
                })
            self._set_status(WarpStatus.CONNECTED)

    def _do_disconnect(self):
        self._set_status(WarpStatus.DISCONNECTING)
        if self._cli_path:
            self._run_cli(["disconnect"])
            time.sleep(1)
            self._poll_cli_status()
        else:
            time.sleep(1)
            with self._lock:
                self._connection_info.update({
                    "ip": "", "city": "", "country": "", "colo": "",
                })
            self._set_status(WarpStatus.DISCONNECTED)

    def _run_cli(self, args: list) -> bool:
        try:
            result = subprocess.run(
                [self._cli_path] + args,
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _poll_cli_status(self, wait=False):
        if wait:
            time.sleep(1)
        try:
            result = subprocess.run(
                [self._cli_path, "status"],
                capture_output=True, text=True, timeout=10,
            )
            output = result.stdout.lower()
            if "connected" in output:
                self._set_status(WarpStatus.CONNECTED)
            elif "connecting" in output:
                self._set_status(WarpStatus.CONNECTING)
            else:
                self._set_status(WarpStatus.DISCONNECTED)
        except Exception:
            self._set_status(WarpStatus.ERROR)


def _path_exists(path: str) -> bool:
    import os
    return os.path.isfile(path)

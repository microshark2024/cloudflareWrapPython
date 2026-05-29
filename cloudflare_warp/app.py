"""Application coordinator – wires together the service, window and tray."""

import sys
from typing import Optional

from cloudflare_warp.core.warp_service import WarpService
from cloudflare_warp.core.config import Config
from cloudflare_warp.ui.main_window import MainWindow
from cloudflare_warp.ui.tray_icon import TrayIcon


class App:
    def __init__(self):
        self._cfg = Config()
        self._svc = WarpService()
        self._window: Optional[MainWindow] = None
        self._tray: Optional[TrayIcon] = None

    def run(self):
        # Initial status poll (no-op when no real CLI)
        self._svc.refresh_status()

        # Main window
        self._window = MainWindow(self._svc, self._cfg)

        # System tray (best-effort; silently skipped if pystray unavailable)
        self._tray = TrayIcon(
            warp_service=self._svc,
            show_window_callback=self._show_window,
            quit_callback=self._quit,
        )
        self._tray.start()

        # Popup behaviour: always start hidden; tray icon click reveals the window
        self._window.withdraw()

        self._window.mainloop()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _show_window(self):
        if self._window:
            self._window.after(0, self._window.show_popup)

    def _quit(self):
        if self._tray:
            self._tray.stop()
        if self._window:
            self._window.after(0, self._window.destroy)
        sys.exit(0)

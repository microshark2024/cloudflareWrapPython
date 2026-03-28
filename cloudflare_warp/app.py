"""Application coordinator – wires together the service, window and tray."""

import sys
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

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
        self._qt_app: Optional[QApplication] = None

    def run(self):
        # Create the QApplication (must exist before any widgets)
        self._qt_app = QApplication.instance() or QApplication(sys.argv)

        # Initial status poll (no-op when no real CLI)
        self._svc.refresh_status()

        # Main window
        start_min = self._cfg.get("start_minimized", False)
        self._window = MainWindow(self._svc, self._cfg)

        # System tray
        self._tray = TrayIcon(
            warp_service=self._svc,
            show_window_callback=self._show_window,
            quit_callback=self._quit,
        )
        self._tray.start()

        if start_min:
            self._window.hide()
        else:
            self._window.show()

        # Enter the Qt event loop
        sys.exit(self._qt_app.exec())

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _show_window(self):
        if self._window:
            QTimer.singleShot(0, self._window.show)
            QTimer.singleShot(0, self._window.raise_)
            QTimer.singleShot(0, self._window.activateWindow)

    def _quit(self):
        if self._tray:
            self._tray.stop()
        if self._qt_app:
            self._qt_app.quit()

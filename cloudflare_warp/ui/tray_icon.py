"""System-tray icon (uses Qt QSystemTrayIcon)."""

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from cloudflare_warp.core.warp_service import WarpStatus
from . import theme as T


def _make_icon(status: WarpStatus) -> QIcon:
    """Create a 64×64 tray icon reflecting the current status."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    if status == WarpStatus.CONNECTED:
        color = QColor(0, 174, 224)
    elif status in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
        color = QColor(245, 166, 35)
    elif status == WarpStatus.ERROR:
        color = QColor(231, 76, 60)
    else:
        color = QColor(244, 129, 32)  # Cloudflare orange

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(color))
    p.setPen(color)
    # Simple stylised cloud shape
    p.drawEllipse(4, 24, 28, 26)
    p.drawEllipse(14, 14, 32, 32)
    p.drawEllipse(32, 24, 28, 26)
    p.drawRect(8, 36, 48, 14)
    p.end()

    return QIcon(pixmap)


class TrayIcon:
    """Manages the system-tray icon lifecycle using Qt."""

    def __init__(self, warp_service, show_window_callback, quit_callback):
        self._svc = warp_service
        self._show_cb = show_window_callback
        self._quit_cb = quit_callback
        self._tray: QSystemTrayIcon | None = None

    def start(self):
        """Create and show the tray icon."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self._tray = QSystemTrayIcon()
        self._tray.setIcon(_make_icon(self._svc.status))
        self._tray.setToolTip("Cloudflare WARP")

        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {T.BG_CARD};
                color: {T.TEXT_PRIMARY};
                border: 1px solid {T.SEPARATOR};
            }}
            QMenu::item:selected {{
                background-color: {T.BG_HOVER};
            }}
        """)

        show_action = QAction("Show", menu)
        show_action.triggered.connect(self._show_cb)
        menu.addAction(show_action)
        menu.addSeparator()

        connect_action = QAction("Connect", menu)
        connect_action.triggered.connect(self._svc.connect)
        menu.addAction(connect_action)

        disconnect_action = QAction("Disconnect", menu)
        disconnect_action.triggered.connect(self._svc.disconnect)
        menu.addAction(disconnect_action)

        menu.addSeparator()
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._on_quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

        self._svc.add_status_callback(self._on_status_change)

    def stop(self):
        if self._tray:
            self._tray.hide()
            self._tray = None

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_cb()

    def _on_quit(self):
        self.stop()
        self._quit_cb()

    def _on_status_change(self, new_status: WarpStatus):
        if self._tray:
            self._tray.setIcon(_make_icon(new_status))
            labels = {
                WarpStatus.CONNECTED: "Cloudflare WARP – Connected",
                WarpStatus.CONNECTING: "Cloudflare WARP – Connecting…",
                WarpStatus.DISCONNECTING: "Cloudflare WARP – Disconnecting…",
                WarpStatus.ERROR: "Cloudflare WARP – Error",
            }
            self._tray.setToolTip(labels.get(new_status, "Cloudflare WARP"))

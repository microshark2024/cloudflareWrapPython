"""System-tray icon (uses pystray + Pillow)."""

import threading
from PIL import Image, ImageDraw

from cloudflare_warp.core.warp_service import WarpStatus
from . import theme as T


def _make_icon_image(status: WarpStatus) -> Image.Image:
    """Create a 64×64 tray icon reflecting the current status."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if status == WarpStatus.CONNECTED:
        color = (0, 174, 224, 255)   # blue
    elif status in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
        color = (245, 166, 35, 255)  # yellow/orange
    elif status == WarpStatus.ERROR:
        color = (231, 76, 60, 255)
    else:
        color = (244, 129, 32, 255)  # Cloudflare orange

    # Draw a simple cloud icon
    draw.ellipse([4, 24, 32, 50], fill=color)
    draw.ellipse([14, 14, 46, 46], fill=color)
    draw.ellipse([32, 24, 60, 50], fill=color)
    draw.rectangle([8, 36, 56, 50], fill=color)

    return img


class TrayIcon:
    """Manages the system-tray icon lifecycle."""

    def __init__(self, warp_service, show_window_callback, quit_callback):
        self._svc = warp_service
        self._show_cb = show_window_callback
        self._quit_cb = quit_callback
        self._icon = None
        self._thread = None

    def start(self):
        """Spawn the tray icon in a background thread."""
        try:
            import pystray
        except ImportError:
            return

        status = self._svc.status
        icon_img = _make_icon_image(status)
        menu = self._build_menu(pystray)

        self._icon = pystray.Icon(
            "cloudflare_warp",
            icon_img,
            "Cloudflare WARP",
            menu,
        )

        self._svc.add_status_callback(self._on_status_change)

        self._thread = threading.Thread(
            target=self._icon.run, daemon=True,
        )
        self._thread.start()

    def stop(self):
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    def _build_menu(self, pystray):
        return pystray.Menu(
            pystray.MenuItem("Show", self._on_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Connect",
                lambda icon, item: self._svc.connect(),
            ),
            pystray.MenuItem(
                "Disconnect",
                lambda icon, item: self._svc.disconnect(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )

    def _on_show(self, icon, item):
        self._show_cb()

    def _on_quit(self, icon, item):
        self.stop()
        self._quit_cb()

    def _on_status_change(self, new_status: WarpStatus):
        if self._icon:
            try:
                self._icon.icon = _make_icon_image(new_status)
                labels = {
                    WarpStatus.CONNECTED: "Cloudflare WARP – Connected",
                    WarpStatus.CONNECTING: "Cloudflare WARP – Connecting…",
                    WarpStatus.DISCONNECTING: "Cloudflare WARP – Disconnecting…",
                    WarpStatus.ERROR: "Cloudflare WARP – Error",
                }
                self._icon.title = labels.get(new_status, "Cloudflare WARP")
            except Exception:
                pass

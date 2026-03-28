"""Main application window – matches Cloudflare WARP's desktop UI."""

import math
import tkinter as tk
from tkinter import ttk
from typing import Callable

from cloudflare_warp.core.warp_service import WarpStatus
from . import theme as T


# ---------------------------------------------------------------------------
# Helper: rounded-rectangle drawing on a Canvas
# ---------------------------------------------------------------------------

def _round_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius=20, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ---------------------------------------------------------------------------
# Animated toggle (power) button
# ---------------------------------------------------------------------------

class ToggleButton(tk.Canvas):
    """Circular power button with an animated glow ring."""

    _ANIM_STEPS = 20
    _ANIM_INTERVAL_MS = 25

    def __init__(self, master, on_click: Callable, **kwargs):
        size = T.TOGGLE_CANVAS_SIZE
        super().__init__(
            master,
            width=size, height=size,
            bg=T.BG_DARK, highlightthickness=0,
            **kwargs,
        )
        self._on_click = on_click
        self._cx = size // 2
        self._cy = size // 2
        self._status = WarpStatus.DISCONNECTED
        self._anim_step = 0
        self._anim_id = None
        self._hover = False

        # Draw initial state
        self._draw()
        self.bind("<ButtonRelease-1>", self._handle_click)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self._hover = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_status(self, status: WarpStatus):
        self._status = status
        self._stop_anim()
        if status in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
            self._start_anim()
        else:
            self._draw()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _handle_click(self, _event):
        if self._status not in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
            self._on_click()

    def _set_hover(self, state: bool):
        self._hover = state
        if self._status not in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
            self._draw()

    def _start_anim(self):
        self._anim_step = 0
        self._tick_anim()

    def _stop_anim(self):
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None

    def _tick_anim(self):
        self._anim_step = (self._anim_step + 1) % self._ANIM_STEPS
        self._draw()
        self._anim_id = self.after(self._ANIM_INTERVAL_MS, self._tick_anim)

    def _draw(self):
        self.delete("all")
        cx, cy = self._cx, self._cy
        status = self._status
        step = self._anim_step / self._ANIM_STEPS  # 0..1

        # ---- colour selection ----
        if status == WarpStatus.CONNECTED:
            main_color = T.CONNECTED_BLUE
            glow_color = "#005580"
        elif status in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
            # Pulsing between orange and blue
            t = (math.sin(step * 2 * math.pi) + 1) / 2
            main_color = _lerp_hex(T.ORANGE, T.CONNECTED_BLUE, t)
            glow_color = _lerp_hex("#804010", "#003355", t)
        elif status == WarpStatus.ERROR:
            main_color = "#e74c3c"
            glow_color = "#5a1010"
        else:  # DISCONNECTED
            main_color = T.ORANGE if not self._hover else T.ORANGE_DARK
            glow_color = "#804010"

        # ---- outer glow layers ----
        r = T.TOGGLE_GLOW_R
        for i in range(4):
            alpha_scale = 0.12 - i * 0.025
            gr = r + i * 5
            color = _dim_hex(main_color, alpha_scale)
            self.create_oval(
                cx - gr, cy - gr, cx + gr, cy + gr,
                fill=color, outline="",
            )

        # ---- outer ring ----
        r = T.TOGGLE_RADIUS
        self.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=glow_color, outline=main_color, width=3,
        )

        # ---- inner circle ----
        ri = T.TOGGLE_INNER_R
        inner_fill = _dim_hex(main_color, 0.25)
        self.create_oval(
            cx - ri, cy - ri, cx + ri, cy + ri,
            fill=inner_fill, outline="",
        )

        # ---- power / lightning icon ----
        if status in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
            # Spinning arc
            start_angle = step * 360
            self.create_arc(
                cx - 28, cy - 28, cx + 28, cy + 28,
                start=start_angle, extent=270,
                style="arc", outline=main_color, width=4,
            )
        elif status == WarpStatus.CONNECTED:
            # Lightning bolt
            pts = self._lightning(cx, cy, 24, main_color)
            self.create_polygon(pts, fill=main_color, outline="")
        else:
            # Power symbol
            self._draw_power(cx, cy, 22, main_color)

    def _draw_power(self, cx, cy, r, color):
        # Arc (top-open circle)
        gap = 40
        self.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=90 + gap // 2, extent=360 - gap,
            style="arc", outline=color, width=3,
        )
        # Vertical line
        self.create_line(cx, cy - r - 4, cx, cy - r + 10, fill=color, width=3)

    @staticmethod
    def _lightning(cx, cy, size, _color):
        s = size
        return [
            cx + s * 0.1, cy - s,
            cx - s * 0.4, cy + s * 0.15,
            cx + s * 0.05, cy + s * 0.15,
            cx - s * 0.1, cy + s,
            cx + s * 0.4, cy - s * 0.15,
            cx - s * 0.05, cy - s * 0.15,
        ]


# ---------------------------------------------------------------------------
# Info card widget
# ---------------------------------------------------------------------------

class InfoCard(tk.Frame):
    """Rounded card showing connection details (IP, city, data centre)."""

    def __init__(self, master, **kwargs):
        super().__init__(master, bg=T.BG_CARD, **kwargs)
        self.configure(padx=16, pady=12)

        self._ip_var = tk.StringVar(value="")
        self._loc_var = tk.StringVar(value="")
        self._colo_var = tk.StringVar(value="")

        row0 = tk.Frame(self, bg=T.BG_CARD)
        row0.pack(fill="x")
        tk.Label(row0, text="Your IP address", font=T.FONT_SMALL,
                 fg=T.TEXT_SECONDARY, bg=T.BG_CARD).pack(side="left")
        tk.Label(row0, textvariable=self._ip_var, font=T.FONT_SMALL,
                 fg=T.TEXT_PRIMARY, bg=T.BG_CARD).pack(side="right")

        tk.Frame(self, bg=T.SEPARATOR, height=1).pack(fill="x", pady=6)

        row1 = tk.Frame(self, bg=T.BG_CARD)
        row1.pack(fill="x")
        tk.Label(row1, text="Location", font=T.FONT_SMALL,
                 fg=T.TEXT_SECONDARY, bg=T.BG_CARD).pack(side="left")
        tk.Label(row1, textvariable=self._loc_var, font=T.FONT_SMALL,
                 fg=T.TEXT_PRIMARY, bg=T.BG_CARD).pack(side="right")

        tk.Frame(self, bg=T.SEPARATOR, height=1).pack(fill="x", pady=6)

        row2 = tk.Frame(self, bg=T.BG_CARD)
        row2.pack(fill="x")
        tk.Label(row2, text="Cloudflare data center", font=T.FONT_SMALL,
                 fg=T.TEXT_SECONDARY, bg=T.BG_CARD).pack(side="left")
        tk.Label(row2, textvariable=self._colo_var, font=T.FONT_SMALL,
                 fg=T.TEXT_PRIMARY, bg=T.BG_CARD).pack(side="right")

    def update_info(self, info: dict):
        self._ip_var.set(info.get("ip", "–"))
        city = info.get("city", "")
        country = info.get("country", "")
        self._loc_var.set(f"{city}, {country}" if city else "–")
        self._colo_var.set(info.get("colo", "–"))


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(tk.Tk):
    """Primary Cloudflare WARP window."""

    def __init__(self, warp_service, config):
        super().__init__()
        self._svc = warp_service
        self._cfg = config

        self.title(T.WINDOW_TITLE)
        self.geometry(f"{T.WINDOW_WIDTH}x{T.WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(bg=T.BG_DARK)

        # On close: minimise to tray (handled in app.py)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._svc.add_status_callback(self._on_status_change)
        self._refresh_display(self._svc.status)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ---- top bar ----
        top = tk.Frame(self, bg=T.BG_DARK)
        top.pack(fill="x", padx=20, pady=(18, 0))

        logo_frame = tk.Frame(top, bg=T.BG_DARK)
        logo_frame.pack(side="left")
        self._draw_logo(logo_frame)
        tk.Label(
            logo_frame, text="WARP", font=(T.FONT_FAMILY, 18, "bold"),
            fg=T.TEXT_PRIMARY, bg=T.BG_DARK,
        ).pack(side="left", padx=(6, 0))

        # Settings gear button (top right)
        settings_btn = tk.Label(
            top, text="⚙", font=(T.FONT_FAMILY, 18),
            fg=T.TEXT_SECONDARY, bg=T.BG_DARK, cursor="hand2",
        )
        settings_btn.pack(side="right")
        settings_btn.bind("<ButtonRelease-1>", self._open_settings)
        settings_btn.bind("<Enter>", lambda e: settings_btn.config(fg=T.TEXT_PRIMARY))
        settings_btn.bind("<Leave>", lambda e: settings_btn.config(fg=T.TEXT_SECONDARY))

        # ---- divider ----
        tk.Frame(self, bg=T.SEPARATOR, height=1).pack(fill="x", padx=20, pady=(14, 0))

        # ---- toggle area ----
        toggle_frame = tk.Frame(self, bg=T.BG_DARK)
        toggle_frame.pack(pady=(24, 0))
        self._toggle = ToggleButton(toggle_frame, on_click=self._on_toggle)
        self._toggle.pack()

        # ---- status label ----
        self._status_var = tk.StringVar(value="Disconnected")
        self._status_label = tk.Label(
            self, textvariable=self._status_var,
            font=T.FONT_STATUS, fg=T.TEXT_SECONDARY, bg=T.BG_DARK,
        )
        self._status_label.pack(pady=(10, 0))

        # ---- sub-status (e.g., "Click to connect") ----
        self._sub_var = tk.StringVar(value="Tap to connect and protect your\ninternet activity.")
        self._sub_label = tk.Label(
            self, textvariable=self._sub_var,
            font=T.FONT_INFO, fg=T.TEXT_MUTED, bg=T.BG_DARK,
            justify="center", wraplength=260,
        )
        self._sub_label.pack(pady=(6, 0))

        # ---- info card (hidden until connected) ----
        self._info_card = InfoCard(self)
        # Packed conditionally in _refresh_display

        # ---- spacer ----
        tk.Frame(self, bg=T.BG_DARK).pack(fill="both", expand=True)

        # ---- bottom bar ----
        self._build_bottom_bar()

    def _draw_logo(self, parent):
        """Draw the Cloudflare 'cloud' logo in miniature on a Canvas."""
        c = tk.Canvas(parent, width=28, height=22,
                      bg=T.BG_DARK, highlightthickness=0)
        c.pack(side="left")
        # Simple stylised cloud shape
        c.create_oval(2, 8, 14, 20, fill=T.ORANGE, outline="")
        c.create_oval(6, 4, 22, 18, fill=T.ORANGE, outline="")
        c.create_oval(14, 8, 26, 20, fill=T.ORANGE, outline="")
        c.create_rectangle(4, 14, 24, 20, fill=T.ORANGE, outline="")

    def _build_bottom_bar(self):
        bottom = tk.Frame(self, bg=T.BG_CARD)
        bottom.pack(fill="x", side="bottom")

        # Account type badge
        acct = self._cfg.get("account_type", "free").upper()
        badge_text = "WARP+" if acct == "warp_plus" else "WARP Free"
        self._acct_label = tk.Label(
            bottom, text=badge_text,
            font=(T.FONT_FAMILY, 9, "bold"),
            fg=T.ORANGE, bg=T.BG_CARD,
        )
        self._acct_label.pack(side="left", padx=16, pady=10)

        # Connection indicator dot
        self._dot_canvas = tk.Canvas(
            bottom, width=10, height=10,
            bg=T.BG_CARD, highlightthickness=0,
        )
        self._dot_canvas.pack(side="right", padx=(0, 6), pady=10)
        self._status_dot = self._dot_canvas.create_oval(
            1, 1, 9, 9, fill=T.TEXT_MUTED, outline="",
        )

        self._conn_label = tk.Label(
            bottom, text="Not connected",
            font=T.FONT_SMALL, fg=T.TEXT_MUTED, bg=T.BG_CARD,
        )
        self._conn_label.pack(side="right", padx=(0, 4), pady=10)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_toggle(self):
        if self._svc.status == WarpStatus.CONNECTED:
            self._svc.disconnect()
        else:
            self._svc.connect()

    def _on_status_change(self, new_status: WarpStatus):
        # Must update GUI from the main thread
        self.after(0, self._refresh_display, new_status)

    def _on_close(self):
        # Minimise to tray (tray icon is set up in app.py);
        # if no tray support, destroy.
        self.withdraw()

    def _open_settings(self, _event=None):
        from cloudflare_warp.ui.settings_dialog import SettingsDialog
        SettingsDialog(self, self._svc, self._cfg)

    # ------------------------------------------------------------------
    # Display refresh
    # ------------------------------------------------------------------

    def _refresh_display(self, status: WarpStatus):
        self._toggle.set_status(status)

        status_texts = {
            WarpStatus.DISCONNECTED: ("Disconnected", T.TEXT_SECONDARY,
                                      "Tap to connect and protect your\ninternet activity."),
            WarpStatus.CONNECTING:   ("Connecting…",  T.CONNECTING_YELLOW,
                                      "Establishing a secure tunnel…"),
            WarpStatus.CONNECTED:    ("Connected",    T.CONNECTED_BLUE,
                                      "Your internet activity is protected."),
            WarpStatus.DISCONNECTING:("Disconnecting…", T.TEXT_SECONDARY,
                                      "Closing the secure tunnel…"),
            WarpStatus.ERROR:        ("Error",         T.ERROR_RED,
                                      "Could not connect. Please retry."),
        }
        label, color, sub = status_texts.get(
            status, ("Unknown", T.TEXT_MUTED, ""))
        self._status_var.set(label)
        self._status_label.config(fg=color)
        self._sub_var.set(sub)

        # Show/hide info card
        if status == WarpStatus.CONNECTED:
            self._info_card.pack(fill="x", padx=20, pady=(12, 0))
            self._info_card.update_info(self._svc.connection_info)
        else:
            self._info_card.pack_forget()

        # Dot indicator
        dot_colors = {
            WarpStatus.CONNECTED: T.SUCCESS_GREEN,
            WarpStatus.CONNECTING: T.CONNECTING_YELLOW,
            WarpStatus.DISCONNECTING: T.CONNECTING_YELLOW,
            WarpStatus.ERROR: T.ERROR_RED,
        }
        dot_color = dot_colors.get(status, T.TEXT_MUTED)
        self._dot_canvas.itemconfig(self._status_dot, fill=dot_color)
        self._conn_label.config(
            text=label,
            fg=dot_color if status == WarpStatus.CONNECTED else T.TEXT_MUTED,
        )


# ---------------------------------------------------------------------------
# Colour utilities
# ---------------------------------------------------------------------------

def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _lerp_hex(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def _dim_hex(color: str, alpha: float) -> str:
    """Blend color toward BG_DARK by alpha."""
    r, g, b = _hex_to_rgb(color)
    bg_r, bg_g, bg_b = _hex_to_rgb(T.BG_DARK)
    return _rgb_to_hex(bg_r + (r - bg_r) * alpha, bg_g + (g - bg_g) * alpha, bg_b + (b - bg_b) * alpha)

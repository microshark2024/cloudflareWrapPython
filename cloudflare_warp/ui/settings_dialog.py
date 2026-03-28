"""Settings dialog – mirrors Cloudflare WARP preferences panel."""

import tkinter as tk
from tkinter import ttk

from cloudflare_warp.core.warp_service import WarpService, WarpStatus
from cloudflare_warp.core.config import Config
from . import theme as T


class SettingsDialog(tk.Toplevel):
    """Modal settings window."""

    def __init__(self, parent, warp_service: WarpService, config: Config):
        super().__init__(parent)
        self._svc = warp_service
        self._cfg = config

        self.title("WARP Settings")
        self.geometry("380x520")
        self.resizable(False, False)
        self.configure(bg=T.BG_DARK)
        self.transient(parent)
        self.grab_set()

        self._build()
        self._load_values()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self):
        # Title bar
        title = tk.Label(self, text="Settings", font=T.FONT_TITLE,
                         fg=T.TEXT_PRIMARY, bg=T.BG_DARK)
        title.pack(pady=(20, 0), padx=20, anchor="w")

        tk.Frame(self, bg=T.SEPARATOR, height=1).pack(fill="x", padx=20, pady=12)

        # Notebook (tabs)
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Custom.TNotebook", background=T.BG_DARK, borderwidth=0)
        style.configure("Custom.TNotebook.Tab",
                         background=T.BG_CARD, foreground=T.TEXT_SECONDARY,
                         padding=(14, 6), font=T.FONT_BODY)
        style.map("Custom.TNotebook.Tab",
                  background=[("selected", T.BG_DARK)],
                  foreground=[("selected", T.TEXT_PRIMARY)])

        nb = ttk.Notebook(self, style="Custom.TNotebook")
        nb.pack(fill="both", expand=True, padx=16, pady=0)

        self._build_general_tab(nb)
        self._build_dns_tab(nb)
        self._build_split_tunnel_tab(nb)
        self._build_account_tab(nb)

        # Save / Cancel
        btn_frame = tk.Frame(self, bg=T.BG_DARK)
        btn_frame.pack(fill="x", padx=20, pady=16)

        cancel_btn = tk.Button(
            btn_frame, text="Cancel", font=T.FONT_BODY,
            bg=T.BG_CARD, fg=T.TEXT_SECONDARY, relief="flat",
            activebackground=T.BG_HOVER, activeforeground=T.TEXT_PRIMARY,
            cursor="hand2", command=self.destroy, padx=14, pady=6,
        )
        cancel_btn.pack(side="right", padx=(6, 0))

        save_btn = tk.Button(
            btn_frame, text="Save", font=(T.FONT_FAMILY, 11, "bold"),
            bg=T.ORANGE, fg="white", relief="flat",
            activebackground=T.ORANGE_DARK, activeforeground="white",
            cursor="hand2", command=self._save, padx=14, pady=6,
        )
        save_btn.pack(side="right")

    def _build_general_tab(self, nb):
        frame = self._tab_frame(nb, "General")

        self._start_minimized_var = tk.BooleanVar()
        self._start_on_login_var = tk.BooleanVar()
        self._show_notif_var = tk.BooleanVar()

        _checkbox(frame, "Start minimized", self._start_minimized_var)
        _checkbox(frame, "Launch at startup", self._start_on_login_var)
        _checkbox(frame, "Show notifications", self._show_notif_var)

    def _build_dns_tab(self, nb):
        frame = self._tab_frame(nb, "DNS")

        tk.Label(frame, text="DNS mode", font=T.FONT_BODY,
                 fg=T.TEXT_SECONDARY, bg=T.BG_DARK).pack(anchor="w", pady=(0, 6))

        self._dns_var = tk.StringVar()
        modes = [
            ("WARP (recommended)", "warp"),
            ("DNS over HTTPS (DoH)", "doh"),
            ("DNS over TLS (DoT)", "dot"),
            ("Off", "off"),
        ]
        for label, value in modes:
            _radio(frame, label, self._dns_var, value)

    def _build_split_tunnel_tab(self, nb):
        frame = self._tab_frame(nb, "Split Tunnel")

        tk.Label(frame, text="Mode", font=T.FONT_BODY,
                 fg=T.TEXT_SECONDARY, bg=T.BG_DARK).pack(anchor="w", pady=(0, 6))

        self._tunnel_mode_var = tk.StringVar()
        _radio(frame, "Exclude IPs from WARP", self._tunnel_mode_var, "exclude")
        _radio(frame, "Include only these IPs in WARP", self._tunnel_mode_var, "include")

        tk.Label(frame, text="IP ranges (one per line)",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_DARK).pack(
            anchor="w", pady=(12, 4))
        self._ips_text = tk.Text(
            frame, height=6, bg=T.BG_CARD, fg=T.TEXT_PRIMARY,
            insertbackground=T.TEXT_PRIMARY, font=(T.FONT_FAMILY, 10),
            relief="flat", padx=6, pady=6,
        )
        self._ips_text.pack(fill="x")

    def _build_account_tab(self, nb):
        frame = self._tab_frame(nb, "Account")

        tk.Label(frame, text="Account type", font=T.FONT_BODY,
                 fg=T.TEXT_SECONDARY, bg=T.BG_DARK).pack(anchor="w", pady=(0, 6))

        self._acct_var = tk.StringVar()
        _radio(frame, "WARP (free)", self._acct_var, "free")
        _radio(frame, "WARP+ (paid)", self._acct_var, "warp_plus")

        # Status indicator
        connected = self._svc.status == WarpStatus.CONNECTED
        status_color = T.SUCCESS_GREEN if connected else T.ERROR_RED
        status_text = "Connected" if connected else "Not connected"
        tk.Label(frame, text=f"Status: {status_text}", font=T.FONT_BODY,
                 fg=status_color, bg=T.BG_DARK).pack(anchor="w", pady=(20, 0))

        # Version info
        from cloudflare_warp import __version__
        tk.Label(frame, text=f"Version {__version__}", font=T.FONT_SMALL,
                 fg=T.TEXT_MUTED, bg=T.BG_DARK).pack(anchor="w", pady=(8, 0))

    # ------------------------------------------------------------------
    # Values
    # ------------------------------------------------------------------

    def _load_values(self):
        self._start_minimized_var.set(self._cfg.get("start_minimized", False))
        self._start_on_login_var.set(self._cfg.get("start_on_login", False))
        self._show_notif_var.set(self._cfg.get("show_notifications", True))
        self._dns_var.set(self._cfg.get("dns_mode", "warp"))
        self._tunnel_mode_var.set(self._cfg.get("split_tunnel_mode", "exclude"))
        self._acct_var.set(self._cfg.get("account_type", "free"))

        ips = self._cfg.get("split_tunnel_ips", [])
        self._ips_text.insert("1.0", "\n".join(ips))

    def _save(self):
        self._cfg.set("start_minimized", self._start_minimized_var.get())
        self._cfg.set("start_on_login", self._start_on_login_var.get())
        self._cfg.set("show_notifications", self._show_notif_var.get())
        self._cfg.set("dns_mode", self._dns_var.get())
        self._cfg.set("split_tunnel_mode", self._tunnel_mode_var.get())
        self._cfg.set("account_type", self._acct_var.get())

        raw_ips = self._ips_text.get("1.0", tk.END).strip()
        ips = [ip.strip() for ip in raw_ips.splitlines() if ip.strip()]
        self._cfg.set("split_tunnel_ips", ips)
        self.destroy()

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _tab_frame(self, nb, label) -> tk.Frame:
        f = tk.Frame(nb, bg=T.BG_DARK, padx=16, pady=14)
        nb.add(f, text=label)
        return f


# ---------------------------------------------------------------------------
# Convenience widget constructors
# ---------------------------------------------------------------------------

def _checkbox(parent, text, var):
    cb = tk.Checkbutton(
        parent, text=text, variable=var,
        font=T.FONT_BODY, fg=T.TEXT_PRIMARY, bg=T.BG_DARK,
        selectcolor=T.BG_CARD, activebackground=T.BG_DARK,
        activeforeground=T.TEXT_PRIMARY, relief="flat",
    )
    cb.pack(anchor="w", pady=4)


def _radio(parent, text, var, value):
    rb = tk.Radiobutton(
        parent, text=text, variable=var, value=value,
        font=T.FONT_BODY, fg=T.TEXT_PRIMARY, bg=T.BG_DARK,
        selectcolor=T.BG_CARD, activebackground=T.BG_DARK,
        activeforeground=T.TEXT_PRIMARY, relief="flat",
    )
    rb.pack(anchor="w", pady=2)

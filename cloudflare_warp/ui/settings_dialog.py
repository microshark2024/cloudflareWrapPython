"""Settings dialog – mirrors Cloudflare WARP preferences panel using Qt."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QWidget, QCheckBox, QRadioButton, QButtonGroup, QTextEdit,
    QPushButton, QFrame, QSizePolicy,
)

from cloudflare_warp.core.warp_service import WarpService, WarpStatus
from cloudflare_warp.core.config import Config
from . import theme as T


# ---------------------------------------------------------------------------
# Shared QSS snippets
# ---------------------------------------------------------------------------

_TAB_QSS = f"""
QTabWidget::pane {{
    border: none;
    background-color: {T.BG_DARK};
}}
QTabBar::tab {{
    background: {T.BG_CARD};
    color: {T.TEXT_SECONDARY};
    padding: 6px 14px;
    border: none;
    font-size: {T.FONT_BODY_SIZE}pt;
}}
QTabBar::tab:selected {{
    background: {T.BG_DARK};
    color: {T.TEXT_PRIMARY};
}}
QTabBar::tab:hover {{
    color: {T.TEXT_PRIMARY};
}}
"""

_CHECKBOX_QSS = f"""
QCheckBox {{
    color: {T.TEXT_PRIMARY};
    spacing: 8px;
    font-size: {T.FONT_BODY_SIZE}pt;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {T.TEXT_SECONDARY};
    border-radius: 3px;
    background: {T.BG_CARD};
}}
QCheckBox::indicator:checked {{
    background: {T.ORANGE};
    border-color: {T.ORANGE};
}}
QCheckBox::indicator:hover {{
    border-color: {T.TEXT_PRIMARY};
}}
"""

_RADIO_QSS = f"""
QRadioButton {{
    color: {T.TEXT_PRIMARY};
    spacing: 8px;
    font-size: {T.FONT_BODY_SIZE}pt;
    background: transparent;
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border: 2px solid {T.TEXT_SECONDARY};
    border-radius: 9px;
    background: {T.BG_CARD};
}}
QRadioButton::indicator:checked {{
    background: {T.ORANGE};
    border-color: {T.ORANGE};
}}
QRadioButton::indicator:hover {{
    border-color: {T.TEXT_PRIMARY};
}}
"""


class SettingsDialog(QDialog):
    """Modal settings window styled like Cloudflare WARP preferences."""

    def __init__(self, parent, warp_service: WarpService, config: Config):
        super().__init__(parent)
        self._svc = warp_service
        self._cfg = config

        self.setWindowTitle("WARP Settings")
        self.setFixedSize(380, 520)
        self.setStyleSheet(f"QDialog {{ background-color: {T.BG_DARK}; }}")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._build()
        self._load_values()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(0)

        # Title
        title = QLabel("Settings")
        title.setFont(QFont(T.FONT_FAMILY, T.FONT_TITLE_SIZE, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {T.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {T.SEPARATOR}; margin-top: 12px; margin-bottom: 12px;")
        layout.addWidget(sep)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(_TAB_QSS)
        layout.addWidget(self._tabs, stretch=1)

        self._build_general_tab()
        self._build_dns_tab()
        self._build_split_tunnel_tab()
        self._build_account_tab()

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 16, 0, 0)
        btn_row.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setFont(QFont(T.FONT_FAMILY, T.FONT_BODY_SIZE, QFont.Weight.Bold))
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {T.ORANGE};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {T.ORANGE_DARK};
            }}
            QPushButton:pressed {{
                background-color: {T.ORANGE_PRESSED};
            }}
        """)
        save_btn.clicked.connect(self._save)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont(T.FONT_FAMILY, T.FONT_BODY_SIZE))
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {T.BG_CARD};
                color: {T.TEXT_SECONDARY};
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {T.BG_HOVER};
                color: {T.TEXT_PRIMARY};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)

        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    # -- tabs -------------------------------------------------------------

    def _build_general_tab(self):
        page = self._tab_page("General")
        layout = page.layout()

        self._start_minimized_cb = QCheckBox("Start minimized")
        self._start_on_login_cb = QCheckBox("Launch at startup")
        self._show_notif_cb = QCheckBox("Show notifications")

        for cb in (self._start_minimized_cb, self._start_on_login_cb, self._show_notif_cb):
            cb.setStyleSheet(_CHECKBOX_QSS)
            cb.setFont(QFont(T.FONT_FAMILY, T.FONT_BODY_SIZE))
            layout.addWidget(cb)

        layout.addStretch()

    def _build_dns_tab(self):
        page = self._tab_page("DNS")
        layout = page.layout()

        heading = QLabel("DNS mode")
        heading.setFont(QFont(T.FONT_FAMILY, T.FONT_BODY_SIZE))
        heading.setStyleSheet(f"color: {T.TEXT_SECONDARY}; background: transparent; padding-bottom: 6px;")
        layout.addWidget(heading)

        self._dns_group = QButtonGroup(self)
        modes = [
            ("WARP (recommended)", "warp"),
            ("DNS over HTTPS (DoH)", "doh"),
            ("DNS over TLS (DoT)", "dot"),
            ("Off", "off"),
        ]
        self._dns_radios = {}
        for label, value in modes:
            rb = QRadioButton(label)
            rb.setStyleSheet(_RADIO_QSS)
            rb.setFont(QFont(T.FONT_FAMILY, T.FONT_BODY_SIZE))
            self._dns_group.addButton(rb)
            self._dns_radios[value] = rb
            layout.addWidget(rb)

        layout.addStretch()

    def _build_split_tunnel_tab(self):
        page = self._tab_page("Split Tunnel")
        layout = page.layout()

        heading = QLabel("Mode")
        heading.setFont(QFont(T.FONT_FAMILY, T.FONT_BODY_SIZE))
        heading.setStyleSheet(f"color: {T.TEXT_SECONDARY}; background: transparent; padding-bottom: 6px;")
        layout.addWidget(heading)

        self._tunnel_group = QButtonGroup(self)
        self._tunnel_radios = {}
        for label, value in [
            ("Exclude IPs from WARP", "exclude"),
            ("Include only these IPs in WARP", "include"),
        ]:
            rb = QRadioButton(label)
            rb.setStyleSheet(_RADIO_QSS)
            rb.setFont(QFont(T.FONT_FAMILY, T.FONT_BODY_SIZE))
            self._tunnel_group.addButton(rb)
            self._tunnel_radios[value] = rb
            layout.addWidget(rb)

        ip_heading = QLabel("IP ranges (one per line)")
        ip_heading.setFont(QFont(T.FONT_FAMILY, T.FONT_SMALL_SIZE))
        ip_heading.setStyleSheet(f"color: {T.TEXT_SECONDARY}; background: transparent; padding-top: 12px; padding-bottom: 4px;")
        layout.addWidget(ip_heading)

        self._ips_text = QTextEdit()
        self._ips_text.setMaximumHeight(120)
        self._ips_text.setFont(QFont(T.FONT_FAMILY, 10))
        self._ips_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {T.BG_CARD};
                color: {T.TEXT_PRIMARY};
                border: none;
                border-radius: 4px;
                padding: 6px;
            }}
        """)
        layout.addWidget(self._ips_text)
        layout.addStretch()

    def _build_account_tab(self):
        page = self._tab_page("Account")
        layout = page.layout()

        heading = QLabel("Account type")
        heading.setFont(QFont(T.FONT_FAMILY, T.FONT_BODY_SIZE))
        heading.setStyleSheet(f"color: {T.TEXT_SECONDARY}; background: transparent; padding-bottom: 6px;")
        layout.addWidget(heading)

        self._acct_group = QButtonGroup(self)
        self._acct_radios = {}
        for label, value in [("WARP (free)", "free"), ("WARP+ (paid)", "warp_plus")]:
            rb = QRadioButton(label)
            rb.setStyleSheet(_RADIO_QSS)
            rb.setFont(QFont(T.FONT_FAMILY, T.FONT_BODY_SIZE))
            self._acct_group.addButton(rb)
            self._acct_radios[value] = rb
            layout.addWidget(rb)

        # Status indicator
        connected = self._svc.status == WarpStatus.CONNECTED
        status_color = T.SUCCESS_GREEN if connected else T.ERROR_RED
        status_text = "Connected" if connected else "Not connected"
        status_lbl = QLabel(f"Status: {status_text}")
        status_lbl.setFont(QFont(T.FONT_FAMILY, T.FONT_BODY_SIZE))
        status_lbl.setStyleSheet(f"color: {status_color}; background: transparent; padding-top: 20px;")
        layout.addWidget(status_lbl)

        # Version
        from cloudflare_warp import __version__
        ver_lbl = QLabel(f"Version {__version__}")
        ver_lbl.setFont(QFont(T.FONT_FAMILY, T.FONT_SMALL_SIZE))
        ver_lbl.setStyleSheet(f"color: {T.TEXT_MUTED}; background: transparent; padding-top: 8px;")
        layout.addWidget(ver_lbl)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Values
    # ------------------------------------------------------------------

    def _load_values(self):
        self._start_minimized_cb.setChecked(self._cfg.get("start_minimized", False))
        self._start_on_login_cb.setChecked(self._cfg.get("start_on_login", False))
        self._show_notif_cb.setChecked(self._cfg.get("show_notifications", True))

        dns_mode = self._cfg.get("dns_mode", "warp")
        if dns_mode in self._dns_radios:
            self._dns_radios[dns_mode].setChecked(True)

        tunnel_mode = self._cfg.get("split_tunnel_mode", "exclude")
        if tunnel_mode in self._tunnel_radios:
            self._tunnel_radios[tunnel_mode].setChecked(True)

        acct = self._cfg.get("account_type", "free")
        if acct in self._acct_radios:
            self._acct_radios[acct].setChecked(True)

        ips = self._cfg.get("split_tunnel_ips", [])
        self._ips_text.setPlainText("\n".join(ips))

    def _save(self):
        self._cfg.set("start_minimized", self._start_minimized_cb.isChecked())
        self._cfg.set("start_on_login", self._start_on_login_cb.isChecked())
        self._cfg.set("show_notifications", self._show_notif_cb.isChecked())

        for value, rb in self._dns_radios.items():
            if rb.isChecked():
                self._cfg.set("dns_mode", value)
                break

        for value, rb in self._tunnel_radios.items():
            if rb.isChecked():
                self._cfg.set("split_tunnel_mode", value)
                break

        for value, rb in self._acct_radios.items():
            if rb.isChecked():
                self._cfg.set("account_type", value)
                break

        raw_ips = self._ips_text.toPlainText().strip()
        ips = [ip.strip() for ip in raw_ips.splitlines() if ip.strip()]
        self._cfg.set("split_tunnel_ips", ips)

        self.accept()

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _tab_page(self, label) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background-color: {T.BG_DARK};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        self._tabs.addTab(page, label)
        return page

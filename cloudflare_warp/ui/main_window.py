"""Main application window – matches Cloudflare WARP's desktop UI using Qt."""

import math

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QRectF, QPointF,
    Signal, QSize,
)
from PySide6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QRadialGradient,
    QPainterPath, QLinearGradient, QFontMetrics, QCursor, QScreen,
)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSizePolicy, QSpacerItem, QFrame, QApplication,
)

from cloudflare_warp.core.warp_service import WarpStatus
from . import theme as T


# ---------------------------------------------------------------------------
# Animated toggle (power) button – QPainter based
# ---------------------------------------------------------------------------

class ToggleButton(QWidget):
    """Circular power button with an animated glow ring."""

    clicked = Signal()
    _ANIM_INTERVAL_MS = 25
    _ANIM_PHASE_STEP = 0.035     # phase increment per tick (controls spin speed)

    def __init__(self, parent=None):
        super().__init__(parent)
        size = T.TOGGLE_CANVAS_SIZE
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMouseTracking(True)

        self._status = WarpStatus.DISCONNECTED
        self._hover = False
        self._pressed = False
        self._anim_phase = 0.0          # 0..1 cyclic
        self._press_scale = 1.0         # click-shrink effect

        # Animation timer for connecting/disconnecting pulse
        self._timer = QTimer(self)
        self._timer.setInterval(self._ANIM_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)

        # Press animation
        self._press_anim = QPropertyAnimation(self, b"pressScale")
        self._press_anim.setDuration(100)
        self._press_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # -- Qt property for press animation ----------------------------------
    def _get_press_scale(self):
        return self._press_scale

    def _set_press_scale(self, v):
        self._press_scale = v
        self.update()

    pressScale = Property(float, _get_press_scale, _set_press_scale)

    # -- public API --------------------------------------------------------
    def set_status(self, status: WarpStatus):
        self._status = status
        if status in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
            if not self._timer.isActive():
                self._anim_phase = 0.0
                self._timer.start()
        else:
            self._timer.stop()
        self.update()

    # -- events ------------------------------------------------------------
    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self._press_anim.stop()
            self._press_anim.setStartValue(1.0)
            self._press_anim.setEndValue(0.93)
            self._press_anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._pressed:
            self._pressed = False
            self._press_anim.stop()
            self._press_anim.setStartValue(self._press_scale)
            self._press_anim.setEndValue(1.0)
            self._press_anim.start()
            if self._status not in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
                self.clicked.emit()
        super().mouseReleaseEvent(event)

    # -- internal ----------------------------------------------------------
    def _tick(self):
        self._anim_phase = (self._anim_phase + self._ANIM_PHASE_STEP) % 1.0
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx, cy = w / 2, h / 2

        # apply press scale
        if self._press_scale != 1.0:
            p.translate(cx, cy)
            p.scale(self._press_scale, self._press_scale)
            p.translate(-cx, -cy)

        status = self._status
        phase = self._anim_phase

        # ---- colour selection ----
        if status == WarpStatus.CONNECTED:
            main_color = QColor(T.CONNECTED_BLUE)
            glow_color = QColor("#005580")
        elif status in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
            t = (math.sin(phase * 2 * math.pi) + 1) / 2
            main_color = _lerp_qcolor(QColor(T.ORANGE), QColor(T.CONNECTED_BLUE), t)
            glow_color = _lerp_qcolor(QColor("#804010"), QColor("#003355"), t)
        elif status == WarpStatus.ERROR:
            main_color = QColor(T.ERROR_RED)
            glow_color = QColor("#5a1010")
        else:  # DISCONNECTED
            main_color = QColor(T.ORANGE) if not self._hover else QColor(T.ORANGE_DARK)
            glow_color = QColor("#804010")

        # ---- outer glow (radial gradient) ----
        grad = QRadialGradient(cx, cy, T.TOGGLE_GLOW_R + 15)
        gc = QColor(main_color)
        gc.setAlpha(60)
        grad.setColorAt(0.0, gc)
        gc2 = QColor(main_color)
        gc2.setAlpha(20)
        grad.setColorAt(0.6, gc2)
        gc3 = QColor(T.BG_DARK)
        gc3.setAlpha(0)
        grad.setColorAt(1.0, gc3)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        gr = T.TOGGLE_GLOW_R + 15
        p.drawEllipse(QPointF(cx, cy), gr, gr)

        # ---- outer ring ----
        r = T.TOGGLE_RADIUS
        p.setBrush(QBrush(glow_color))
        p.setPen(QPen(main_color, 3))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # ---- inner filled circle ----
        ri = T.TOGGLE_INNER_R
        inner_c = QColor(main_color)
        inner_c.setAlpha(55)
        p.setBrush(QBrush(inner_c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), ri, ri)

        # ---- icon ----
        p.setPen(Qt.PenStyle.NoPen)
        if status in (WarpStatus.CONNECTING, WarpStatus.DISCONNECTING):
            self._draw_spinner(p, cx, cy, 28, main_color, phase)
        elif status == WarpStatus.CONNECTED:
            self._draw_lightning(p, cx, cy, 24, main_color)
        else:
            self._draw_power(p, cx, cy, 22, main_color)

        p.end()

    # ---- icon drawing helpers -------------------------------------------

    @staticmethod
    def _draw_spinner(p: QPainter, cx, cy, r, color, phase):
        """Spinning arc indicator."""
        pen = QPen(color, 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        start_angle = int(phase * 360 * 16)
        span_angle = 270 * 16
        rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        p.drawArc(rect, start_angle, span_angle)

    @staticmethod
    def _draw_lightning(p: QPainter, cx, cy, s, color):
        """Lightning bolt icon (connected state)."""
        path = QPainterPath()
        pts = [
            QPointF(cx + s * 0.1, cy - s),
            QPointF(cx - s * 0.4, cy + s * 0.15),
            QPointF(cx + s * 0.05, cy + s * 0.15),
            QPointF(cx - s * 0.1, cy + s),
            QPointF(cx + s * 0.4, cy - s * 0.15),
            QPointF(cx - s * 0.05, cy - s * 0.15),
        ]
        path.moveTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        path.closeSubpath()
        p.setBrush(QBrush(color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)

    @staticmethod
    def _draw_power(p: QPainter, cx, cy, r, color):
        """Power symbol icon (disconnected state)."""
        pen = QPen(color, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        # Arc (gap at top)
        gap = 40
        rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        start = (90 + gap // 2) * 16
        span = (360 - gap) * 16
        p.drawArc(rect, start, span)
        # Vertical line
        p.drawLine(QPointF(cx, cy - r - 4), QPointF(cx, cy - r + 10))


# ---------------------------------------------------------------------------
# Info card widget
# ---------------------------------------------------------------------------

class InfoCard(QFrame):
    """Rounded card showing connection details."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            InfoCard {{
                background-color: {T.BG_CARD};
                border-radius: 10px;
                padding: 12px 16px;
            }}
        """)
        self.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(0)

        self._ip_label = self._add_row(layout, "Your IP address", "")
        self._add_separator(layout)
        self._loc_label = self._add_row(layout, "Location", "")
        self._add_separator(layout)
        self._colo_label = self._add_row(layout, "Cloudflare data center", "")

    def update_info(self, info: dict):
        self._ip_label.setText(info.get("ip", "–"))
        city = info.get("city", "")
        country = info.get("country", "")
        self._loc_label.setText(f"{city}, {country}" if city else "–")
        self._colo_label.setText(info.get("colo", "–"))

    def _add_row(self, layout, label_text, value_text) -> QLabel:
        row = QWidget(self)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 6, 0, 6)

        lbl = QLabel(label_text, row)
        lbl.setStyleSheet(f"color: {T.TEXT_SECONDARY}; font-size: {T.FONT_SMALL_SIZE}pt; background: transparent;")
        lbl.setFont(QFont(T.FONT_FAMILY, T.FONT_SMALL_SIZE))

        val = QLabel(value_text, row)
        val.setStyleSheet(f"color: {T.TEXT_PRIMARY}; font-size: {T.FONT_SMALL_SIZE}pt; background: transparent;")
        val.setFont(QFont(T.FONT_FAMILY, T.FONT_SMALL_SIZE))
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        row_layout.addWidget(lbl)
        row_layout.addWidget(val)
        layout.addWidget(row)
        return val

    @staticmethod
    def _add_separator(layout):
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {T.SEPARATOR};")
        layout.addWidget(sep)


# ---------------------------------------------------------------------------
# Cloud logo widget (mini Cloudflare cloud)
# ---------------------------------------------------------------------------

class CloudLogo(QWidget):
    """Miniature Cloudflare cloud drawn with QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 22)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        orange = QColor(T.ORANGE)
        p.setBrush(QBrush(orange))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2, 8, 12, 12)
        p.drawEllipse(6, 4, 16, 14)
        p.drawEllipse(14, 8, 12, 12)
        p.drawRect(4, 14, 20, 6)
        p.end()


# ---------------------------------------------------------------------------
# Settings gear button (hover effect)
# ---------------------------------------------------------------------------

class GearButton(QLabel):
    """Gear icon label with hover highlight."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("⚙", parent)
        self.setFont(QFont(T.FONT_FAMILY, 18))
        self.setStyleSheet(f"color: {T.TEXT_SECONDARY}; background: transparent;")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def enterEvent(self, event):
        self.setStyleSheet(f"color: {T.TEXT_PRIMARY}; background: transparent;")

    def leaveEvent(self, event):
        self.setStyleSheet(f"color: {T.TEXT_SECONDARY}; background: transparent;")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Primary Cloudflare WARP window (positioned bottom-right like the real client)."""

    def __init__(self, warp_service, config):
        super().__init__()
        self._svc = warp_service
        self._cfg = config

        self.title(T.WINDOW_TITLE)
        self.resizable(False, False)
        self.configure(bg=T.BG_DARK)

        # Popup behaviour: remove OS title bar and taskbar entry
        self.overrideredirect(True)
        self._position_popup()

        # Auto-hide when the application loses focus to another window
        self.bind("<FocusOut>", self._on_focus_out)
        self._hide_check_id = None

        self._build_ui()
        self._svc.add_status_callback(self._on_status_change)
        self._refresh_display(self._svc.status)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---- top bar ----
        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {T.BG_DARK};")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 18, 20, 0)

        # Logo + WARP text
        logo_area = QWidget()
        logo_layout = QHBoxLayout(logo_area)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(6)

        logo = CloudLogo()
        logo_layout.addWidget(logo)

        warp_label = QLabel("WARP")
        warp_label.setFont(QFont(T.FONT_FAMILY, 18, QFont.Weight.Bold))
        warp_label.setStyleSheet(f"color: {T.TEXT_PRIMARY}; background: transparent;")
        logo_layout.addWidget(warp_label)

        top_layout.addWidget(logo_area)
        top_layout.addStretch()

        # Settings gear
        self._gear = GearButton()
        self._gear.clicked.connect(self._open_settings)
        top_layout.addWidget(self._gear)

        main_layout.addWidget(top_bar)

        # ---- divider ----
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {T.SEPARATOR}; margin: 0 20px;")
        div_container = QWidget()
        div_container.setStyleSheet(f"background: {T.BG_DARK};")
        div_l = QHBoxLayout(div_container)
        div_l.setContentsMargins(20, 14, 20, 0)
        div_l.addWidget(divider)
        main_layout.addWidget(div_container)

        # ---- toggle area ----
        toggle_container = QWidget()
        toggle_container.setStyleSheet(f"background-color: {T.BG_DARK};")
        tc_layout = QVBoxLayout(toggle_container)
        tc_layout.setContentsMargins(0, 24, 0, 0)
        tc_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._toggle = ToggleButton()
        self._toggle.clicked.connect(self._on_toggle)
        tc_layout.addWidget(self._toggle, alignment=Qt.AlignmentFlag.AlignHCenter)
        main_layout.addWidget(toggle_container)

        # ---- status label ----
        self._status_label = QLabel("Disconnected")
        self._status_label.setFont(QFont(T.FONT_FAMILY, T.FONT_STATUS_SIZE, QFont.Weight.Bold))
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"color: {T.TEXT_SECONDARY}; background: {T.BG_DARK}; padding-top: 10px;")
        main_layout.addWidget(self._status_label)

        # ---- sub-status ----
        self._sub_label = QLabel("Tap to connect and protect your\ninternet activity.")
        self._sub_label.setFont(QFont(T.FONT_FAMILY, T.FONT_INFO_SIZE))
        self._sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub_label.setWordWrap(True)
        self._sub_label.setFixedWidth(260)
        self._sub_label.setStyleSheet(f"color: {T.TEXT_MUTED}; background: {T.BG_DARK}; padding-top: 6px;")

        sub_container = QWidget()
        sub_container.setStyleSheet(f"background: {T.BG_DARK};")
        sub_l = QHBoxLayout(sub_container)
        sub_l.setContentsMargins(0, 0, 0, 0)
        sub_l.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        sub_l.addWidget(self._sub_label)
        main_layout.addWidget(sub_container)

        # ---- info card ----
        info_container = QWidget()
        info_container.setStyleSheet(f"background: {T.BG_DARK};")
        info_l = QHBoxLayout(info_container)
        info_l.setContentsMargins(20, 12, 20, 0)
        self._info_card = InfoCard()
        info_l.addWidget(self._info_card)
        main_layout.addWidget(info_container)

        # ---- spacer ----
        main_layout.addStretch()

        # ---- bottom bar ----
        self._build_bottom_bar(main_layout)

    def _build_bottom_bar(self, main_layout):
        bottom = QFrame()
        bottom.setStyleSheet(f"background-color: {T.BG_CARD}; border-top: 1px solid {T.SEPARATOR};")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(16, 10, 16, 10)

        # Account type badge
        acct = self._cfg.get("account_type", "free")
        badge_text = "WARP+" if acct == "warp_plus" else "WARP Free"
        self._acct_label = QLabel(badge_text)
        self._acct_label.setFont(QFont(T.FONT_FAMILY, T.FONT_SMALL_SIZE, QFont.Weight.Bold))
        self._acct_label.setStyleSheet(f"color: {T.ORANGE}; background: transparent;")
        bottom_layout.addWidget(self._acct_label)

        bottom_layout.addStretch()

        # Connection indicator label
        self._conn_label = QLabel("Not connected")
        self._conn_label.setFont(QFont(T.FONT_FAMILY, T.FONT_SMALL_SIZE))
        self._conn_label.setStyleSheet(f"color: {T.TEXT_MUTED}; background: transparent;")
        bottom_layout.addWidget(self._conn_label)

        # Connection dot
        self._dot = DotIndicator()
        bottom_layout.addWidget(self._dot)

        main_layout.addWidget(bottom)

    # ------------------------------------------------------------------
    # Window positioning (bottom-right near system tray)
    # ------------------------------------------------------------------

    def _position_near_tray(self):
        """Place the window in the bottom-right corner of the primary screen,
        matching the Cloudflare WARP client's default position."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        x = available.x() + available.width() - self.width() - 12
        y = available.y() + available.height() - self.height() - 12
        self.move(x, y)

    # ------------------------------------------------------------------
    # Popup positioning & visibility
    # ------------------------------------------------------------------

    def _position_popup(self):
        """Position the window at the bottom-right corner near the system tray."""
        self.update_idletasks()
        w = T.WINDOW_WIDTH
        h = T.WINDOW_HEIGHT
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = sw - w - 20
        y = sh - h - 60
        self.geometry(f"{w}x{h}+{x}+{y}")

    def show_popup(self):
        """Show the popup window positioned near the system tray."""
        self._position_popup()
        self.deiconify()
        self.lift()
        self.focus_force()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_toggle(self):
        if self._svc.status == WarpStatus.CONNECTED:
            self._svc.disconnect()
        else:
            self._svc.connect()

    def _on_status_change(self, new_status: WarpStatus):
        """Thread-safe status update via QTimer.singleShot."""
        QTimer.singleShot(0, lambda s=new_status: self._refresh_display(s))

    def _on_focus_out(self, _event):
        """Schedule a check to auto-hide when focus leaves the application."""
        if self._hide_check_id is not None:
            self.after_cancel(self._hide_check_id)
        self._hide_check_id = self.after(200, self._check_focus_and_hide)

    def _check_focus_and_hide(self):
        """Hide the popup if no widget in this application has focus."""
        self._hide_check_id = None
        if not self.winfo_ismapped():
            return
        if self.focus_get() is None:
            self.withdraw()

    def _open_settings(self, _event=None):
        from cloudflare_warp.ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self, self._svc, self._cfg)
        dlg.exec()

    # ------------------------------------------------------------------
    # Display refresh
    # ------------------------------------------------------------------

    def _refresh_display(self, status: WarpStatus):
        self._toggle.set_status(status)

        status_texts = {
            WarpStatus.DISCONNECTED:  ("Disconnected",    T.TEXT_SECONDARY,
                                       "Tap to connect and protect your\ninternet activity."),
            WarpStatus.CONNECTING:    ("Connecting…",     T.CONNECTING_YELLOW,
                                       "Establishing a secure tunnel…"),
            WarpStatus.CONNECTED:     ("Connected",       T.CONNECTED_BLUE,
                                       "Your internet activity is protected."),
            WarpStatus.DISCONNECTING: ("Disconnecting…",  T.TEXT_SECONDARY,
                                       "Closing the secure tunnel…"),
            WarpStatus.ERROR:         ("Error",           T.ERROR_RED,
                                       "Could not connect. Please retry."),
        }

        label, color, sub = status_texts.get(
            status, ("Unknown", T.TEXT_MUTED, ""))
        self._status_label.setText(label)
        self._status_label.setStyleSheet(
            f"color: {color}; background: {T.BG_DARK}; padding-top: 10px;")
        self._sub_label.setText(sub)

        # Show/hide info card
        if status == WarpStatus.CONNECTED:
            self._info_card.setVisible(True)
            self._info_card.update_info(self._svc.connection_info)
        else:
            self._info_card.setVisible(False)

        # Dot indicator
        dot_colors = {
            WarpStatus.CONNECTED: T.SUCCESS_GREEN,
            WarpStatus.CONNECTING: T.CONNECTING_YELLOW,
            WarpStatus.DISCONNECTING: T.CONNECTING_YELLOW,
            WarpStatus.ERROR: T.ERROR_RED,
        }
        dot_color = dot_colors.get(status, T.TEXT_MUTED)
        self._dot.set_color(dot_color)
        self._conn_label.setText(label)
        fg = dot_color if status == WarpStatus.CONNECTED else T.TEXT_MUTED
        self._conn_label.setStyleSheet(f"color: {fg}; background: transparent;")


# ---------------------------------------------------------------------------
# Small connection-status dot
# ---------------------------------------------------------------------------

class DotIndicator(QWidget):
    """10×10 coloured circle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._color = QColor(T.TEXT_MUTED)

    def set_color(self, hex_color: str):
        self._color = QColor(hex_color)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(self._color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 8, 8)
        p.end()


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def _lerp_qcolor(c1: QColor, c2: QColor, t: float) -> QColor:
    """Linearly interpolate between two QColors."""
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue() + (c2.blue() - c1.blue()) * t),
    )

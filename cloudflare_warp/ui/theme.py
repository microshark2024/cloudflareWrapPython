"""Visual design tokens matching Cloudflare WARP's colour palette."""

import platform

# ---------------------------------------------------------------------------
# Colours – sampled from the real Cloudflare WARP desktop client
# ---------------------------------------------------------------------------
BG_DARK = "#1b1c2e"          # main window background
BG_CARD = "#242535"          # card / secondary surface
BG_HOVER = "#2e2f47"         # hover state

ORANGE = "#f48120"           # Cloudflare brand orange
ORANGE_DARK = "#d06a10"      # pressed/active state

CONNECTED_BLUE = "#00aee0"   # toggle glow when connected
CONNECTING_YELLOW = "#f5a623"

TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#a0a0c0"
TEXT_MUTED = "#606080"

SEPARATOR = "#2e2f47"
SUCCESS_GREEN = "#27ae60"
ERROR_RED = "#e74c3c"

# ---------------------------------------------------------------------------
# Fonts  (cross-platform sans-serif)
# ---------------------------------------------------------------------------
_sys = platform.system()
if _sys == "Windows":
    FONT_FAMILY = "Segoe UI"
elif _sys == "Darwin":
    FONT_FAMILY = "SF Pro Text"
else:
    FONT_FAMILY = "Noto Sans"

FONT_TITLE_SIZE = 22
FONT_STATUS_SIZE = 14
FONT_BODY_SIZE = 11
FONT_SMALL_SIZE = 9
FONT_INFO_SIZE = 10

# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 340
WINDOW_HEIGHT = 580
WINDOW_TITLE = "Cloudflare WARP"

# ---------------------------------------------------------------------------
# Toggle button geometry (drawn via QPainter)
# ---------------------------------------------------------------------------
TOGGLE_CANVAS_SIZE = 200
TOGGLE_RADIUS = 80          # outer ring radius
TOGGLE_INNER_R = 62         # inner circle
TOGGLE_GLOW_R = 90          # outer glow radius

# ---------------------------------------------------------------------------
# Colour utilities (pure-Python, no GUI dependency)
# ---------------------------------------------------------------------------

def hex_to_rgb(h: str):
    """Convert a hex colour string to an (r, g, b) tuple."""
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    """Convert (r, g, b) integers to a hex colour string."""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def lerp_hex(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex colours by factor *t* (0-1)."""
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(
        r1 + (r2 - r1) * t,
        g1 + (g2 - g1) * t,
        b1 + (b2 - b1) * t,
    )


def dim_hex(color: str, alpha: float) -> str:
    """Blend *color* toward BG_DARK by *alpha* (0 = background, 1 = color)."""
    r, g, b = hex_to_rgb(color)
    bg_r, bg_g, bg_b = hex_to_rgb(BG_DARK)
    return rgb_to_hex(
        bg_r + (r - bg_r) * alpha,
        bg_g + (g - bg_g) * alpha,
        bg_b + (b - bg_b) * alpha,
    )

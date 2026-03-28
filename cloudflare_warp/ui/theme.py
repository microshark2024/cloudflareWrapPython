"""Visual design tokens matching Cloudflare WARP's colour palette."""

# ---------------------------------------------------------------------------
# Colours
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
# Fonts  (font families that exist on most systems)
# ---------------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"       # falls back gracefully on non-Windows
FONT_TITLE = (FONT_FAMILY, 22, "bold")
FONT_STATUS = (FONT_FAMILY, 14, "bold")
FONT_BODY = (FONT_FAMILY, 11)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_INFO = (FONT_FAMILY, 10)

# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 340
WINDOW_HEIGHT = 580
WINDOW_TITLE = "Cloudflare WARP"

# ---------------------------------------------------------------------------
# Toggle button geometry (drawn on a Canvas)
# ---------------------------------------------------------------------------
TOGGLE_CANVAS_SIZE = 200
TOGGLE_RADIUS = 80          # outer ring radius
TOGGLE_INNER_R = 62         # inner circle
TOGGLE_GLOW_R = 90          # outer glow radius

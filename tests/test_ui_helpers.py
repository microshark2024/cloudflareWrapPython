"""Tests for UI helper functions (no display required)."""

import pytest

# Import only pure-Python helpers – avoid importing Qt widgets directly
from cloudflare_warp.ui.theme import hex_to_rgb, rgb_to_hex, lerp_hex, dim_hex
from cloudflare_warp.ui import theme as T


class TestColourHelpers:
    def test_hex_to_rgb_white(self):
        assert hex_to_rgb("#ffffff") == (255, 255, 255)

    def test_hex_to_rgb_black(self):
        assert hex_to_rgb("#000000") == (0, 0, 0)

    def test_hex_to_rgb_orange(self):
        r, g, b = hex_to_rgb(T.ORANGE)
        assert r > g > b   # orange has high R, medium G, low B

    def test_rgb_to_hex_roundtrip(self):
        original = "#1b2c3d"
        r, g, b = hex_to_rgb(original)
        assert rgb_to_hex(r, g, b) == original

    def test_lerp_hex_at_zero(self):
        result = lerp_hex("#ff0000", "#0000ff", 0.0)
        assert result == "#ff0000"

    def test_lerp_hex_at_one(self):
        result = lerp_hex("#ff0000", "#0000ff", 1.0)
        assert result == "#0000ff"

    def test_lerp_hex_at_half(self):
        result = lerp_hex("#000000", "#ffffff", 0.5)
        r, g, b = hex_to_rgb(result)
        assert 120 <= r <= 136
        assert 120 <= g <= 136
        assert 120 <= b <= 136

    def test_dim_hex_alpha_zero_returns_background(self):
        result = dim_hex(T.ORANGE, 0.0)
        assert result == T.BG_DARK

    def test_dim_hex_alpha_one_returns_color(self):
        result = dim_hex(T.ORANGE, 1.0)
        assert result == T.ORANGE

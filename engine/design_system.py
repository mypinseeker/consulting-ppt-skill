"""
Design System — Brand Palette + Color Math + Typography Constants
=================================================================
Core principle: Max 3 brand hues. All differentiation via shade/tint.
"""

from pptx.dml.color import RGBColor
from pptx.util import Pt


def _hex_to_rgb(hex_str: str) -> tuple:
    """Convert '#RRGGBB' to (r, g, b) tuple."""
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_pptx(r: int, g: int, b: int) -> RGBColor:
    return RGBColor(min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b)))


def _shade(rgb: tuple, factor: float) -> tuple:
    """Darken: factor 0.0=black, 1.0=original."""
    return tuple(int(c * factor) for c in rgb)


def _tint(rgb: tuple, factor: float) -> tuple:
    """Lighten: factor 0.0=original, 1.0=white."""
    return tuple(int(c + (255 - c) * factor) for c in rgb)


def rgb_luminance(r, g, b) -> float:
    """WCAG relative luminance."""
    def lin(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(c1: tuple, c2: tuple) -> float:
    """WCAG contrast ratio between two (r,g,b) tuples."""
    l1, l2 = rgb_luminance(*c1), rgb_luminance(*c2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def is_dark(rgb_color: RGBColor) -> bool:
    """Check if a color is dark enough to need white text."""
    return rgb_luminance(rgb_color[0], rgb_color[1], rgb_color[2]) < 0.2


class BrandPalette:
    """
    3-color brand palette with auto-generated shades, tints, and neutrals.

    Usage:
        brand = BrandPalette("#00377B", "#009FDB", "#FFD100")
        brand.primary      # RGBColor dark blue
        brand.shade_90     # Darkest shade of primary
        brand.tint_05      # Near-white tint of primary
        brand.accent_dark  # Muted accent
    """

    def __init__(self, primary: str, secondary: str, accent: str,
                 font_family: str = "Arial"):
        p = _hex_to_rgb(primary)
        s = _hex_to_rgb(secondary)
        a = _hex_to_rgb(accent)

        # ── 3 Brand Colors ──
        self.primary   = _rgb_to_pptx(*p)
        self.secondary = _rgb_to_pptx(*s)
        self.accent    = _rgb_to_pptx(*a)

        # ── Primary Shades & Tints (6 levels) ──
        self.shade_90 = _rgb_to_pptx(*_shade(p, 0.75))   # darkest
        self.shade_70 = _rgb_to_pptx(*_shade(p, 0.85))   # dark-mid
        self.shade_50 = _rgb_to_pptx(*_tint(p, 0.25))    # mid
        self.tint_30  = _rgb_to_pptx(*_tint(s, 0.40))    # light (from secondary)
        self.tint_15  = _rgb_to_pptx(*_tint(s, 0.65))    # very light
        self.tint_05  = _rgb_to_pptx(*_tint(s, 0.88))    # near-white bg

        # ── Accent Shades ──
        self.accent_dark = _rgb_to_pptx(*_shade(a, 0.80))  # muted gold/dark accent

        # ── Neutrals ──
        self.white      = RGBColor(0xFF, 0xFF, 0xFF)
        self.black      = RGBColor(0x00, 0x00, 0x00)
        self.charcoal   = RGBColor(0x2C, 0x3E, 0x50)
        self.light_gray = RGBColor(0xF5, 0xF5, 0xF5)
        self.mid_gray   = RGBColor(0x95, 0xA5, 0xA6)
        self.dark_gray  = RGBColor(0x7F, 0x8C, 0x8D)

        # ── Semantic Aliases ──
        self.positive = self.secondary       # "good" / "stay" / "current"
        self.negative = self.shade_90        # "bad" / "switch" / "risk"
        self.warning  = self.accent          # "caution" / "highlight"

        # ── Typography ──
        self.font_family = font_family

        # ── 7-Dimension Chart Colors ──
        self.dim_colors = [
            self.secondary,     # Dimension 1
            self.primary,       # Dimension 2
            self.shade_50,      # Dimension 3
            self.accent,        # Dimension 4
            self.shade_70,      # Dimension 5
            self.tint_30,       # Dimension 6
            self.accent_dark,   # Dimension 7
        ]

        # ── Dark color set (for contrast logic) ──
        self._dark_colors = {
            self.primary, self.secondary, self.accent,
            self.shade_90, self.shade_70, self.shade_50,
            self.charcoal, self.accent_dark,
        }

    def text_on(self, bg_color: RGBColor) -> RGBColor:
        """Return the best text color (white or charcoal) for a given background."""
        if bg_color in self._dark_colors:
            return self.white
        # Fallback: compute luminance
        if is_dark(bg_color):
            return self.white
        return self.charcoal

    def label_on(self, bg_color: RGBColor) -> RGBColor:
        """Return label color (slightly muted) for a given background."""
        if bg_color in self._dark_colors or is_dark(bg_color):
            return self.white
        return self.dark_gray


# ── Font Size Constants ──

FONT = {
    'title':        Pt(20),
    'subtitle':     Pt(12),
    'kpi_value':    Pt(36),
    'kpi_label':    Pt(10),
    'body':         Pt(11),
    'body_small':   Pt(9),
    'chart_label':  Pt(8),
    'table_header': Pt(9),
    'table_body':   Pt(9),
    'caption':      Pt(7),
    'section_num':  Pt(48),
    'section_title':Pt(28),
    'cover_title':  Pt(36),
    'cover_sub':    Pt(16),
    'closing':      Pt(42),
}

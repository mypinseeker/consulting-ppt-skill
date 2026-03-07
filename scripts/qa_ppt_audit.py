#!/usr/bin/env python3
"""
QA Audit for McKinsey-style PPT decks
======================================
Checks every slide/shape for:
  1. Contrast — dark text on dark background (unreadable)
  2. Missing units — bare numbers without $, M, %, mo, etc.
  3. Empty text frames — shapes with no visible content
  4. Font consistency — non-Arial fonts
  5. Tiny text — font size < 7pt
  6. Source/footnote — content slides should have source line
"""

import sys, os, re
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor

# ── Color helpers ──

def rgb_luminance(r, g, b):
    """Relative luminance (WCAG formula)."""
    def linearize(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(c1, c2):
    """WCAG contrast ratio between two (r,g,b) tuples."""
    l1 = rgb_luminance(*c1)
    l2 = rgb_luminance(*c2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def get_shape_bg_rgb(shape):
    """Try to extract background color from shape fill."""
    try:
        if shape.fill and shape.fill.type is not None:
            fc = shape.fill.fore_color
            if fc and fc.type is not None:
                rgb = fc.rgb
                return (rgb[0], rgb[1], rgb[2])  # RGBColor to tuple
    except Exception:
        pass
    return None


def get_font_rgb(font):
    """Extract font color as (r,g,b) tuple."""
    try:
        if font.color and font.color.rgb:
            rgb = font.color.rgb
            return (rgb[0], rgb[1], rgb[2])
    except Exception:
        pass
    return None


# ── Number/unit detection ──

# Bare number patterns: just digits with optional decimal, no unit suffix
BARE_NUMBER_RE = re.compile(
    r'(?<![$/€£¥%])(?<!\w)'          # not preceded by currency or word char
    r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'  # number like 94.2 or 10,500
    r'(?!\s*[%$MmKkBbyr])'            # not followed by unit
    r'(?!\s*(?:month|site|band|slide|scenario|region|point|step|year))'
    r'(?!\.\d)'                        # not mid-decimal
)

# Strings that are clearly not data (dates, slide numbering, etc.)
IGNORE_PATTERNS = [
    r'^0\d$',           # section numbers like "01", "02"
    r'^\d{1,2}$',       # single/double digit (could be numbering)
    r'March|2026|Confidential|Project Meridian|Source:|Note:',
]

def has_bare_number(text):
    """Check if text contains numbers without units."""
    # Skip non-data text
    for pat in IGNORE_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return False

    # Skip if text already has units
    if re.search(r'\$.*M|\bM\b|%|months?|sites?|bands?|years?', text, re.IGNORECASE):
        return False

    matches = BARE_NUMBER_RE.findall(text)
    # Filter out small numbers that are likely counts/labels
    significant = [m for m in matches if float(m.replace(',', '')) >= 2.0]
    return len(significant) > 0


# ── Main audit ──

class Issue:
    def __init__(self, severity, slide_num, shape_name, description, text_preview=""):
        self.severity = severity  # CRITICAL / WARNING / INFO
        self.slide_num = slide_num
        self.shape_name = shape_name
        self.description = description
        self.text_preview = text_preview[:60] if text_preview else ""

    def __str__(self):
        preview = f' "{self.text_preview}"' if self.text_preview else ''
        return f"  [{self.severity}] Slide {self.slide_num} | {self.shape_name}: {self.description}{preview}"


def audit_pptx(filepath):
    """Run full QA audit on a PPTX file."""
    prs = Presentation(filepath)
    issues = []
    slide_count = len(prs.slides)

    for slide_idx, slide in enumerate(prs.slides, 1):
        shape_count = 0
        has_source = False

        for shape in slide.shapes:
            shape_name = shape.name or f"Shape_{shape.shape_id}"
            shape_count += 1

            # Get shape background
            bg_rgb = get_shape_bg_rgb(shape)

            # Check text frames
            if shape.has_text_frame:
                tf = shape.text_frame
                full_text = tf.text.strip()

                # Check for source/footnote
                if any(kw in full_text.lower() for kw in ['source:', 'note:', 'confidential']):
                    has_source = True

                for para in tf.paragraphs:
                    para_text = para.text.strip()
                    if not para_text:
                        continue

                    # Font checks
                    font = para.font
                    font_rgb = get_font_rgb(font)
                    font_size = font.size
                    font_name = font.name

                    # 1. CONTRAST CHECK
                    if bg_rgb and font_rgb:
                        ratio = contrast_ratio(font_rgb, bg_rgb)
                        if ratio < 2.0:
                            issues.append(Issue("CRITICAL", slide_idx, shape_name,
                                f"Very low contrast ({ratio:.1f}:1) — text likely invisible. "
                                f"BG=#{bg_rgb[0]:02X}{bg_rgb[1]:02X}{bg_rgb[2]:02X} "
                                f"Font=#{font_rgb[0]:02X}{font_rgb[1]:02X}{font_rgb[2]:02X}",
                                para_text))
                        elif ratio < 3.0:
                            issues.append(Issue("WARNING", slide_idx, shape_name,
                                f"Low contrast ({ratio:.1f}:1) — hard to read. "
                                f"BG=#{bg_rgb[0]:02X}{bg_rgb[1]:02X}{bg_rgb[2]:02X} "
                                f"Font=#{font_rgb[0]:02X}{font_rgb[1]:02X}{font_rgb[2]:02X}",
                                para_text))

                    # 2. BARE NUMBERS (missing units)
                    if has_bare_number(para_text):
                        issues.append(Issue("WARNING", slide_idx, shape_name,
                            "Number without unit ($M, %, etc.)",
                            para_text))

                    # 3. FONT CONSISTENCY
                    if font_name and font_name != 'Arial' and font_name not in ('Calibri',):
                        issues.append(Issue("INFO", slide_idx, shape_name,
                            f"Non-standard font: {font_name}",
                            para_text))

                    # 4. TINY TEXT
                    if font_size and font_size < Pt(7):
                        issues.append(Issue("WARNING", slide_idx, shape_name,
                            f"Very small text: {font_size.pt:.0f}pt",
                            para_text))

            # Check chart data labels
            if shape.has_chart:
                chart = shape.chart
                for s_idx, series in enumerate(chart.series):
                    try:
                        dl = series.data_labels
                        if dl.show_value:
                            fmt = dl.number_format or ''
                            if fmt and '$' not in fmt and '%' not in fmt and 'M' not in fmt:
                                issues.append(Issue("WARNING", slide_idx, shape_name,
                                    f"Chart series {s_idx} data labels may lack units (format: '{fmt}')"))
                    except Exception:
                        pass

        # 5. EMPTY SLIDE
        if shape_count < 2:
            issues.append(Issue("WARNING", slide_idx, "-",
                f"Slide has only {shape_count} shape(s) — possibly empty"))

        # 6. MISSING SOURCE (skip cover/divider/closing slides)
        if slide_idx not in (1, slide_count) and not has_source:
            # Check if it's a section divider (usually all dark bg)
            is_divider = False
            for shape in slide.shapes:
                bg = get_shape_bg_rgb(shape)
                if bg and bg == (0x00, 0x37, 0x7B):  # TIGO_DARK full-bleed
                    if shape.width > Emu(Pt(500).emu):
                        is_divider = True
                        break

            if not is_divider:
                issues.append(Issue("INFO", slide_idx, "-",
                    "No source/footnote found on content slide"))

    return issues, slide_count


def main():
    # Accept files from command line, or scan current directory
    if len(sys.argv) > 1:
        ppt_files_full = [f for f in sys.argv[1:] if f.endswith('.pptx')]
    else:
        # Default: scan for .pptx in current directory and output/
        ppt_files_full = []
        for d in ['.', 'output', 'output/v20260306']:
            full_d = os.path.join(os.path.dirname(__file__), '..', d)
            if os.path.isdir(full_d):
                for f in sorted(os.listdir(full_d)):
                    if f.endswith('.pptx'):
                        ppt_files_full.append(os.path.join(full_d, f))

    if not ppt_files_full:
        print("Usage: python qa_ppt_audit.py [file1.pptx file2.pptx ...]")
        print("       Or place .pptx files in output/ directory")
        return 0

    total_critical = 0
    total_warning = 0
    total_info = 0

    for filepath in ppt_files_full:
        filename = os.path.basename(filepath)
        if not os.path.exists(filepath):
            print(f"\n!! MISSING: {filepath}")
            continue

        issues, slide_count = audit_pptx(filepath)
        criticals = [i for i in issues if i.severity == 'CRITICAL']
        warnings = [i for i in issues if i.severity == 'WARNING']
        infos = [i for i in issues if i.severity == 'INFO']

        total_critical += len(criticals)
        total_warning += len(warnings)
        total_info += len(infos)

        status = "FAIL" if criticals else ("WARN" if warnings else "PASS")
        print(f"\n{'='*70}")
        print(f"  {filename} ({slide_count} slides) — {status}")
        print(f"  CRITICAL: {len(criticals)} | WARNING: {len(warnings)} | INFO: {len(infos)}")
        print(f"{'='*70}")

        for issue in criticals:
            print(issue)
        for issue in warnings:
            print(issue)
        for issue in infos:
            print(issue)

    print(f"\n{'='*70}")
    print(f"  TOTAL: {total_critical} CRITICAL | {total_warning} WARNING | {total_info} INFO")
    gate = "PASS" if total_critical == 0 else "FAIL"
    print(f"  QA GATE: {gate}")
    print(f"{'='*70}")

    return 1 if total_critical > 0 else 0


if __name__ == '__main__':
    sys.exit(main())

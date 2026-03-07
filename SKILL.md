---
name: consulting-ppt
description: >
  Generate McKinsey-quality PowerPoint presentations with python-pptx.
  Enforces strict brand palette (max 3 hues), Action Titles, embedded charts,
  KPI metric boxes, insight callouts, and automated QA audit.
  Combines McKinsey consulting methodology with elite presentation design.
license: MIT
metadata:
  author: mypinseeker
  version: "1.0.0"
  last_updated: "2026-03-07"
  architecture: "Design System + Reusable Engine + QA Gate"
---

# Consulting PPT Skill v1.0

Generate professional, McKinsey-quality PowerPoint presentations programmatically
using python-pptx. Every deck follows a strict design system with automated QA.

---

## CRITICAL RULES (Claude MUST follow)

### Rule 1: Max 3 Brand Hues + Neutrals
- User defines **exactly 3 brand colors** (primary, secondary, accent)
- ALL chart/shape/text colors derive from these 3 via shade/tint
- Differentiation by **lightness**, never by adding new hues
- Neutrals (white, grays, charcoal, black) are always allowed
- **Violation**: Using red, green, orange, purple etc. outside the brand palette

### Rule 2: Action Titles (Conclusions, Not Topics)
- Every slide title is a **complete sentence stating the conclusion**
- BAD: "Market Analysis", "Cost Comparison", "Timeline"
- GOOD: "Switching vendors costs 22-57% more than staying"
- GOOD: "Migration creates a 16-month competitive gap"
- Subtitle provides context/scope, title provides the insight

### Rule 3: Every Number Has a Unit
- Chart data labels: `$#,##0.0"M"` or `#,##0"%"` — never bare `#,##0.0`
- KPI boxes: "+$54.0M" not "+54.0"
- Tables: column headers include unit `($M)`, `(%)`, `(months)`
- Insight text: "$29.5M" not "29.5 units"
- **Exception**: counts that are self-evident ("10,500 sites", "4 bands")

### Rule 4: Contrast Ratio >= 3:1
- All text must have >= 3:1 contrast against its background
- Dark background (any brand color, charcoal) => WHITE text
- Light background (white, light gray, tints) => CHARCOAL text
- **Never**: yellow on blue, gray on red, blue on blue
- Run `qa_ppt_audit.py` to verify — 0 CRITICAL required

### Rule 5: Charts Occupy 60-70% of Slide
- Charts are not decoration — they ARE the content
- Minimum chart height: 3.0 inches on a 7.5-inch slide
- Data labels on every bar/point — the audience reads labels, not axes
- One chart per slide (two max for comparison layouts)

### Rule 6: Information Density 50-70 chars/sq inch
- McKinsey pages are dense but not cluttered
- Empty space > 2 sq inches => add insight box or data annotation
- Cover/divider slides are the exception (low density OK)

---

## File Structure

```
consulting-ppt-skill/
  SKILL.md              # This file — skill definition and rules
  README.md             # Quick start guide
  engine/
    design_system.py    # Brand palette, color math, font constants
    slide_builders.py   # Reusable slide templates (cover, KPI, chart, etc.)
    chart_helpers.py    # Bar, stacked, area chart builders
    table_helpers.py    # McKinsey-style tables
  scripts/
    qa_ppt_audit.py     # Automated QA: contrast, units, density
  references/
    design-specs.md     # Detailed design specifications
    layouts.md          # 7 McKinsey page layout types
    color-guide.md      # How to derive shade/tint palette from 3 brand colors
  examples/
    tco_example.py      # Complete TCO presentation example
```

---

## Quick Start

### 1. Define Your Brand

```python
from engine.design_system import BrandPalette

brand = BrandPalette(
    primary   = "#00377B",  # Dark blue
    secondary = "#009FDB",  # Bright blue
    accent    = "#FFD100",  # Yellow
    font_family = "Arial",
)
```

The system auto-generates 6 shades of primary, 2 shades of accent,
plus neutral grays — all derived from your 3 colors.

### 2. Build Slides

```python
from engine.slide_builders import DeckBuilder

deck = DeckBuilder(brand)

deck.add_cover("RAN TCO Analysis", "5-Year Stay vs Switch Model")

deck.add_kpi_slide(
    title="Switching costs 22-57% more than staying across all scenarios",
    kpis=[
        ("+57%", "S1: Bogota", "$54.0M delta"),
        ("+47%", "S2: 3-Region", "$62.1M delta"),
        ("+22%", "S3: Full Network", "$106.0M delta"),
    ]
)

deck.add_chart_slide(
    title="Migration and multi-vendor costs dominate the switching premium",
    chart_type="stacked_bar",
    categories=["S1", "S2", "S3", "S4"],
    series=[("Migration", [22.9, 31.6, 110.0, 176.0]), ...],
    y_axis_title="Cost ($M)",
)

deck.add_insight_slide(
    title="Three actions to capture value without switching risk",
    insights=[
        ("1", "STAY & NEGOTIATE", "Leverage RFP pressure for 10-15% better pricing"),
        ("2", "MODERNIZE", "Use savings to fund 5G acceleration"),
        ("3", "STRATEGIC RESERVE", "Maintain diversification option for future"),
    ]
)

deck.save("output.pptx")
```

### 3. Run QA

```bash
python scripts/qa_ppt_audit.py output.pptx
```

Must pass with 0 CRITICAL before delivery.

---

## Design System Details

### Color Derivation

From 3 brand colors, the system generates:

```
Primary (#00377B):
  shade_90  = darken 20%     # Deepest tone
  shade_70  = darken 10%     # Dark-mid
  shade_50  = lighten 15%    # Mid tone
  tint_30   = lighten 40%    # Light
  tint_15   = lighten 60%    # Very light
  tint_05   = lighten 85%    # Near-white (backgrounds)

Accent (#FFD100):
  accent_dark = darken 20%   # Muted gold (for secondary data)

Neutrals (always available):
  white, light_gray (#F5F5F5), mid_gray (#95A5A6),
  dark_gray (#7F8C8D), charcoal (#2C3E50), black
```

### Semantic Color Mapping

```python
# Charts — Stay vs Switch or Positive vs Negative
positive = brand.secondary   # Bright blue
negative = brand.shade_90    # Darkest primary
warning  = brand.accent      # Yellow

# 7-dimension stacked charts — all from brand palette
dim_colors = [
    brand.secondary,    # Dimension 1
    brand.primary,      # Dimension 2
    brand.shade_50,     # Dimension 3
    brand.accent,       # Dimension 4
    brand.shade_70,     # Dimension 5
    brand.tint_30,      # Dimension 6
    brand.accent_dark,  # Dimension 7
]
```

### Typography

```
Slide title:     20pt, Bold, Primary color
Subtitle:        12pt, Regular, Dark gray
KPI value:       36pt, Bold, White (on dark bg)
KPI label:       10pt, Regular, White (on dark bg)
Body text:       11pt, Regular, Charcoal
Chart labels:    8pt, Regular
Table header:    9pt, Bold, White on Primary
Table body:      9pt, Regular, Charcoal
Source/footer:   7pt, Regular, Mid gray
```

### Slide Templates

| Template | Layout | Use When |
|----------|--------|----------|
| `cover` | Full dark bg, title + subtitle + date | Opening slide |
| `section_divider` | Full dark bg, number + title | Between sections |
| `kpi_row` | Action title + 3-4 KPI boxes + chart | Executive summary |
| `chart_full` | Action title + chart (60-70%) + insight box | Data story |
| `chart_table` | Action title + chart left + table right | Dimension breakdown |
| `deep_dive` | Action title + bar chart + horizontal bars | Per-scenario detail |
| `risk_matrix` | Action title + 2x2 matrix + legend | Risk assessment |
| `timeline` | Action title + phase bars + comparison | Timeline analysis |
| `recommendation` | Action title + 3 numbered action cards | Closing recommendation |
| `closing` | Full dark bg, "Thank You" | Final slide |

---

## QA Audit Checks

The `qa_ppt_audit.py` script checks:

| Check | Severity | Rule |
|-------|----------|------|
| Contrast < 2.0:1 | CRITICAL | Text invisible on background |
| Contrast < 3.0:1 | WARNING | Hard to read |
| Bare number (no unit) | WARNING | Missing $M, %, months etc. |
| Non-standard font | INFO | Font != brand font_family |
| Font size < 7pt | WARNING | Too small to read |
| Chart labels without units | WARNING | Data labels format check |
| Empty slide (< 2 shapes) | WARNING | Possibly blank |
| Missing source/footnote | INFO | Content slide lacks citation |

**Gate**: 0 CRITICAL to pass. WARNINGs reviewed manually.

---

## Workflow Integration

### With mckinsey-consultant skill
This skill handles STEP 7 (PPT generation) and STEP 8 (iteration/QA) of the
mckinsey-consultant workflow. Use mckinsey-consultant for STEP 1-6 (problem
definition, issue tree, hypotheses, dummy pages, data collection).

### With elite-powerpoint-designer skill
This skill incorporates the Financial Elite style from elite-powerpoint-designer
but enforces stricter color discipline (3-hue max) and adds automated QA.

### Standalone
Can be used independently for any data-driven presentation where you have
structured data and want McKinsey-quality output.

---

## Requirements

```bash
pip install python-pptx
```

Optional (for QA audit color analysis):
```bash
pip install Pillow
```

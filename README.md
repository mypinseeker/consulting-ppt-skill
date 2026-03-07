# consulting-ppt

McKinsey-quality PowerPoint generator for Claude Code.

A reusable skill that produces professional, data-driven presentations with strict brand discipline, embedded charts, and automated QA.

## Install

```bash
npx skills add mypinseeker/consulting-ppt-skill@consulting-ppt
```

Or clone directly:

```bash
git clone https://github.com/mypinseeker/consulting-ppt-skill.git
```

## Usage

### As a Claude Code Skill

After installation, Claude Code automatically loads the skill. Just say:

> "Create a McKinsey-style presentation comparing Option A vs Option B using my brand colors #00377B, #009FDB, #FFD100"

### As a Python Library

```bash
pip install python-pptx
```

```python
from engine import BrandPalette, DeckBuilder

brand = BrandPalette("#00377B", "#009FDB", "#FFD100")
deck = DeckBuilder(brand)

deck.add_cover("Project Title", "Subtitle here", date="March 2026")
deck.add_chart_slide(
    title="Option B costs 40% more than Option A across all scenarios",
    chart_type="bar",
    categories=["Q1", "Q2", "Q3", "Q4"],
    series=[("Revenue", [10.2, 12.5, 15.1, 18.3])],
    y_axis_title="Revenue ($M)",
    insight="Q4 shows strongest growth at +21% QoQ",
)
deck.add_closing("Thank You")

deck.save("output.pptx")
```

### QA Audit

```bash
python scripts/qa_ppt_audit.py output.pptx
```

## Design Rules

1. **Max 3 brand hues** + neutral grays. No random colors.
2. **Action Titles** — every title is a conclusion, not a topic.
3. **Every number has a unit** — `$54.0M`, not `54.0`.
4. **Contrast ratio >= 3:1** on all text.
5. **Charts occupy 60-70%** of the slide area.
6. **QA gate: 0 CRITICAL** before delivery.

## Project Structure

```
consulting-ppt-skill/
  SKILL.md              # Skill definition (loaded by Claude Code)
  README.md             # This file
  engine/
    __init__.py
    design_system.py    # BrandPalette, color math, font constants
    slide_builders.py   # DeckBuilder with 10+ slide templates
  scripts/
    qa_ppt_audit.py     # Automated QA checker
  references/
    design-specs.md     # McKinsey design specifications
    layouts.md          # 7 page layout types
    color-guide.md      # 3-color palette derivation guide
  examples/
    tco_example.py      # Full TCO presentation example
```

## Slide Templates

| Template | Method | Description |
|----------|--------|-------------|
| Cover | `add_cover()` | Full dark background, title + subtitle |
| Section Divider | `add_section_divider()` | Dark background, section number + title |
| KPI Row | `add_kpi_slide()` | Action title + 3-4 metric boxes |
| Chart | `add_chart_slide()` | Bar/stacked/area chart + insight box |
| Table | `add_table_slide()` | Full-width data table |
| Recommendation | `add_recommendation_slide()` | 3 numbered action cards |
| Closing | `add_closing()` | Thank you slide |

## License

MIT

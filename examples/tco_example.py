#!/usr/bin/env python3
"""
Example: TCO Presentation using consulting-ppt skill engine
============================================================
Demonstrates all slide templates with sample data.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine import BrandPalette, DeckBuilder

# ── Define brand ──
brand = BrandPalette(
    primary="#00377B",    # Tigo dark blue
    secondary="#009FDB",  # Tigo bright blue
    accent="#FFD100",     # Tigo yellow
    font_family="Arial",
)

# ── Build deck ──
deck = DeckBuilder(brand)

# 1. Cover
deck.add_cover(
    "RAN TCO Analysis:\nStay vs Switch",
    "A 14-Dimension Total Cost of Ownership Model\nfor Vendor Decision",
    date="March 2026",
)

# 2. Section divider
deck.add_section_divider("Executive\nSummary", number="1")

# 3. KPI slide
deck.add_kpi_slide(
    title="Switching vendors costs 22-57% more than staying across all scenarios",
    subtitle="5-Year TCO Delta: Stay vs Switch",
    kpis=[
        ("+57%", "Scenario 1", "Delta: +$54.0M"),
        ("+47%", "Scenario 2", "Delta: +$62.1M"),
        ("+22%", "Scenario 3", "Delta: +$106.0M"),
        ("+50%", "Scenario 4", "Delta: +$235.3M"),
    ],
    source="Source: TCO Model v2, Baseline Parameters",
)

# 4. Bar chart slide
deck.add_chart_slide(
    title="Migration and multi-vendor costs dominate the switching premium",
    chart_type="bar",
    categories=["Migration", "Multi-Vendor", "Risk", "Tech Debt", "Toolchain", "Timeline"],
    series=[("Cost ($M)", [110.0, 0.0, 8.8, 11.9, 14.4, 8.0])],
    y_axis_title="Cost ($M)",
    insight="Migration alone costs $110M for full network — each of 10,500 "
            "sites requires antenna modification, RF retuning, and testing.",
    source="Source: TCO Model v2 — Full Network Baseline Scenario",
)

# 5. Stacked bar chart
deck.add_chart_slide(
    title="Regional scenarios carry multi-vendor overhead; full network avoids it",
    chart_type="stacked_bar",
    categories=["S1: Bogota", "S2: 3-Region", "S3: Full", "S4: Pessimistic"],
    series=[
        ("Procurement", [84.8, 118.7, 423.8, 447.3]),
        ("Migration", [22.9, 31.6, 110.0, 176.0]),
        ("Multi-Vendor", [29.5, 29.5, 0.0, 0.0]),
        ("Other Hidden", [11.0, 14.1, 43.1, 82.9]),
    ],
    y_axis_title="5-Year TCO ($M)",
    source="Source: TCO Model v2 — All values in $M",
)

# 6. Table slide
deck.add_table_slide(
    title="Full network switch costs $106M more than staying — even with 10% procurement discount",
    headers=["Metric", "S1: BOG ($M)", "S2: 3-Reg ($M)", "S3: Full ($M)", "S4: Pessim ($M)"],
    rows=[
        ["Stay TCO", "$94.2M", "$131.8M", "$470.9M", "$470.9M"],
        ["Switch TCO", "$148.1M", "$193.9M", "$576.9M", "$706.2M"],
        ["Delta", "+$54.0M", "+$62.1M", "+$106.0M", "+$235.3M"],
        ["Delta %", "+57.3%", "+47.1%", "+22.5%", "+50.0%"],
    ],
    source="Source: TCO Model v2",
)

# 7. Recommendation
deck.add_recommendation_slide(
    title="Recommendation: Stay with current vendor and negotiate improved terms",
    recommendations=[
        ("1", "STAY & NEGOTIATE", "Leverage competitive pressure from\nRFP process for 10-15% better pricing"),
        ("2", "MODERNIZE IN-PLACE", "Use negotiated savings to fund\n5G acceleration roadmap"),
        ("3", "STRATEGIC RESERVE", "Maintain diversification option\nfor future procurement cycles"),
    ],
)

# 8. Closing
deck.add_closing("Thank You", "TCO Analysis  |  Confidential")

# ── Save ──
output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'tco_example.pptx')
n = deck.save(output_path)
print(f"Generated {n} slides -> {output_path}")

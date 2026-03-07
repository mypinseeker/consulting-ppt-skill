# McKinsey Design Specifications

## Page Layout (16:9 Widescreen)

```
Slide: 13.333 x 7.5 inches

Top bar:     0.08" dark primary
Accent line: 0.03" accent color
Title area:  x=0.8", y=0.25", w=11.5", h=0.7"
Content:     x=0.8", y=1.3", w=11.5", h=5.2"
Footer bar:  y=7.1", h=0.4" dark primary
```

## Typography Hierarchy

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Cover title | 36pt | Bold | White |
| Cover subtitle | 16pt | Regular | Secondary |
| Section number | 48pt | Bold | Accent |
| Section title | 28pt | Bold | White |
| Action title | 20pt | Bold | Primary |
| Subtitle | 12pt | Regular | Dark gray |
| KPI value | 36pt | Bold | White (on dark bg) |
| KPI label | 10pt | Regular | White (on dark bg) |
| Body text | 11pt | Regular | Charcoal |
| Bullet points | 11pt | Regular | Charcoal |
| Chart axis labels | 8pt | Regular | Default |
| Chart data labels | 8pt | Regular | Default |
| Table header | 9pt | Bold | White on primary |
| Table body | 9pt | Regular | Charcoal |
| Source/footnote | 7pt | Regular | Mid gray |
| Closing title | 42pt | Bold | White |

## Mandatory Rules

### Rule 1: Deep Background = White Text
All text on primary, secondary, accent, or shade backgrounds must be WHITE.
The `BrandPalette.text_on()` method enforces this automatically.

### Rule 2: Large Boxes = Sharp Corners
Boxes wider than 3 inches use MSO_SHAPE.RECTANGLE (sharp corners).
Small labels under 1.5 inches may use rounded corners.

### Rule 3: No Borders by Default
Shapes have no border (`line.fill.background()`) unless they are:
- Tables (cell separators)
- Insight callout boxes (thin brand color border)
- Emphasis containers

### Rule 4: Action Titles = Complete Sentences
Every slide title states a conclusion or finding, not a topic.

### Rule 5: High Information Density
Target: 50-70 characters per square inch on content slides.
Exception: Cover, divider, and closing slides are intentionally sparse.

## Insight Box Specification

```
Background: tint_05 (near-white brand)
Border:     1.5pt secondary
Label bar:  0.28" height, primary fill
Label text: "KEY INSIGHT", 8pt bold accent color
Content:    10pt charcoal, 0.15" padding
```

## KPI Box Specification

```
Shape:      Rectangle, no border
Background: Brand color (primary/secondary/shade)
Value:      36pt bold, centered, white
Label:      10pt regular, centered, white
Padding:    Auto via vertical_anchor MIDDLE
```

## Chart Specification

```
Type:       Clustered bar (default), stacked bar, area
Size:       Min 60% of content area (3.5" height minimum)
Data labels: Always visible, $#,##0.0"M" format
Gridlines:  Light gray (#E0E0E0), major only
Legend:     Bottom, 8pt, outside layout
Axis labels: 8pt brand font
```

## Table Specification

```
Header row: Primary fill, white bold text, 9pt, centered
Data rows:  Alternating white / light_gray
Text:       9pt charcoal, first column left-aligned, rest centered
Row height: 0.35" standard
```

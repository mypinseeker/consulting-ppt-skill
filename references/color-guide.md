# Color Guide: 3-Hue Brand Palette Derivation

## Principle

A professional presentation uses **exactly 3 brand hues** plus neutral grays.
All visual differentiation comes from **shade/tint** (lightness), never from
adding new hues (red, green, orange, purple).

## How BrandPalette Works

Given 3 input colors, the system generates a complete palette:

```
Input:
  primary   = "#00377B"  (dark blue)
  secondary = "#009FDB"  (bright blue)
  accent    = "#FFD100"  (yellow)

Generated:
  shade_90  = darken primary 25%     -> #002A5C  (darkest, for "negative")
  shade_70  = darken primary 15%     -> #004D99  (dark-mid)
  shade_50  = lighten primary 25%    -> #0073BB  (mid tone)
  tint_30   = lighten secondary 40%  -> #4DBBE8  (light)
  tint_15   = lighten secondary 65%  -> #99D6F1  (very light)
  tint_05   = lighten secondary 88%  -> #E0F2FA  (near-white, backgrounds)

  accent_dark = darken accent 20%    -> #CCA700  (muted gold)

  Neutrals: white, #F5F5F5, #95A5A6, #7F8C8D, #2C3E50, black
```

## Semantic Color Mapping

| Semantic | Color | Use |
|----------|-------|-----|
| Positive / Stay / Current | `secondary` | Bar charts, KPI boxes |
| Negative / Switch / Risk | `shade_90` | Contrasting bars, warnings |
| Highlight / Warning | `accent` | Callouts, emphasis |
| Primary data | `primary` | Headers, main chart series |
| Background fill | `tint_05` | Insight boxes, light areas |

## 7-Dimension Charts

For stacked/grouped charts with up to 7 series, use this sequence:

```
1. secondary    (#009FDB)  - brightest, most prominent
2. primary      (#00377B)  - dark anchor
3. shade_50     (#0073BB)  - mid blue
4. accent       (#FFD100)  - yellow pop
5. shade_70     (#004D99)  - dark-mid
6. tint_30      (#4DBBE8)  - light blue
7. accent_dark  (#CCA700)  - muted gold
```

## Contrast Rules

| Background | Text Color | Min Ratio |
|------------|------------|-----------|
| primary / shade_90 / shade_70 | WHITE | 4.5:1+ |
| secondary / shade_50 | WHITE | 3.0:1+ |
| accent | CHARCOAL | 3.0:1+ |
| tint_05 / light_gray / white | CHARCOAL | 7.0:1+ |

The `BrandPalette.text_on(bg)` method handles this automatically.

## Anti-Patterns (Never Do)

- Adding red/green for "good/bad" — use shade_90 vs secondary instead
- Using orange for warnings — use accent (yellow) instead
- Rainbow charts — use the 7-dimension sequence above
- Random hex codes not in the palette
- More than 3 distinct hues anywhere in the deck

---
name: consulting-ppt
description: >
  McKinsey-quality PPT generator with automated pipeline.
  One-sentence input → 7-stage state machine → professional PPTX output.
  Enforces Pyramid Principle, Action Titles, strict 3-color brand system,
  and automated QA with Gate checks at every stage.
license: MIT
metadata:
  author: mypinseeker
  version: "3.0.0"
  last_updated: "2026-04-18"
  architecture: "State Machine + Planning JSON Contract + Renderer + QA Gate"
---

# Consulting PPT Skill v3.0

One prompt → McKinsey-quality PPTX. Fully automated 7-stage pipeline with
Pyramid Principle enforcement, Action Title validation, and QA gates.

---

## HOW TO USE (Claude reads this)

### Mode 1: Full Pipeline (一句话生成)

When user says something like:
- "帮我做一份关于 XX 的 PPT"
- "Generate a deck about..."
- "做一份分析报告 PPT"

**Execute this:**

```python
import sys
sys.path.insert(0, "/home/Administrator/Workspace/consulting-ppt-skill")
from engine.orchestrator import Orchestrator

# Step 1: 采访用户（麦肯锡 10 问）
# 读取 references/playbooks/P0_interview.md 获取问题清单
# 向用户提问前 5 个必答问题，收集回答

interview = {
    "audience": "...",           # Q1: 谁是受众
    "core_question": "...",      # Q2: 核心问题（一句话）
    "hypothesis": "...",         # Q3: 结论/假设
    "key_arguments": [...],      # Q4: 2-5 个支撑论点
    "data_sources": [...],       # Q5: 数据来源
    "actions": [...],            # Q7: 行动建议（可选）
    "brand": {                   # Q8: 品牌色（可选，有默认值）
        "primary": "#00377B",
        "secondary": "#009FDB",
        "accent": "#FFD100"
    },
}

# Step 2: 自动执行全流程
orc = Orchestrator()
pptx_path = orc.run_from_interview(interview)
# 输出: artifacts/runs/<run_id>/deck.pptx
```

### Mode 2: From Data (用户已有数据)

When user provides structured data (CSV/Excel/JSON) and asks for PPT:

```python
# 直接从大纲开始，跳过采访
orc = Orchestrator()
pptx_path = orc.run_from_outline({
    "top_conclusion": "用户的核心结论",
    "arguments": [
        {"title": "论点1...", "slides": [{"template": "data_story"}]},
        {"title": "论点2...", "slides": [{"template": "comparison"}]},
    ]
})
```

### Mode 3: From Plan JSON (精确控制每一页)

When user provides or you generate a plan.json:

```python
orc = Orchestrator()
pptx_path = orc.run_from_plan("path/to/plan.json")
```

---

## CRITICAL RULES (Claude MUST follow — 违反任何一条 = 不合格)

### Rule 1: Max 3 Brand Hues + Neutrals
- User defines **exactly 3 brand colors** (primary, secondary, accent)
- ALL colors derive from these 3 via shade/tint — **never add new hues**
- Neutrals (white, grays, charcoal, black) always allowed
- **Violation**: Using red, green, orange, purple outside brand palette

### Rule 2: Action Titles (Conclusions, Not Topics)
- Every content slide title is a **complete sentence stating the conclusion**
- BAD: "Market Analysis", "Cost Comparison", "Timeline"
- GOOD: "Switching vendors costs 22-57% more than staying"
- GOOD: "Migration creates a 16-month competitive gap"
- **Exempt**: cover, section_divider, closing, appendix

### Rule 3: Every Number Has a Unit
- KPI: "+$54.0M" not "+54.0"
- Charts: `$#,##0.0"M"` or `#,##0"%"` — never bare numbers
- Tables: column headers include unit `($M)`, `(%)`, `(months)`

### Rule 4: Contrast Ratio >= 3:1 + Color-Adaptive Layout
- Dark background → WHITE text
- Light background → CHARCOAL text
- **Never**: yellow on blue, gray on red, red on red
- **Cover/Closing 自适应**: primary 是亮色（红/橙/黄）→ 白底+品牌色做强调条
  primary 是深色（深蓝/深灰/黑）→ 全屏深色背景+白色文字
- **KPI 卡片**: 白底+顶部彩色条+品牌色数字（不再用品牌色做满底）
- **Insight 面板**: 白底/浅灰底+左侧彩色边+多行内容（不是小色块+一句话）

### Rule 5: Charts Occupy 50-60% + Insight Panel 40%
- Data labels on every bar/point
- One chart per slide (two max for comparison)

### Rule 6: Chart Data Type Binding
- Every chart in Plan JSON MUST have a `data_type` field
- Valid types: `percentage` | `currency_usd` | `currency_eur` | `score` | `count` | `plain`
- Gate will **CRITICAL** block if `data_type` contradicts `y_axis_title`
  - BAD: `data_type: "currency_usd"` + `y_axis_title: "增长率(%)"`
  - GOOD: `data_type: "percentage"` + `y_axis_title: "YoY增长率(%)"`
- Format is auto-bound: `percentage` → `#,##0"%"`, `currency_usd` → `$#,##0`, etc.

### Rule 7: Text Length Limits (CJK-Aware)
- Cover title + subtitle: **≤35 中文字** (or ≤70 English chars)
- Action Title: **≤45 中文字** (or ≤85 English chars)
- KPI label + detail: **≤12 中文字** (or ≤25 English chars)
- Gate will WARNING if exceeded
- **Why**: 36pt 中文字符宽度 ≈ 36pt，比英文宽 80%。不限长度必溢出

### Rule 8: Pyramid Principle
- Top-level conclusion first (top_conclusion)
- 2-5 supporting arguments, MECE
- Each argument title answers "So What?"
- Gate: `engine/gates.py check_pyramid_principle()` must pass

### Rule 9: Density Contract
- Every content page MUST have `density_label` (low/medium/high)
- density_bias collected at interview, frozen in outline, enforced in Gate
- high-density pages: max 4 chart series, charts ≤70% area
- low-density pages: max 3 content items
- Density is CONTRACT, not suggestion — Gate blocks violations

### Rule 10: Information Density Per Slide
- Data Story 页必须有图表(50-60%) + Insight面板(40%)，不能只放一个图+一句话
- Insight 面板用要点列表（3-5 个 bullet），不是一句话总结
- KPI 页每个卡片包含：大数字 + 标签 + 简述（三层信息）
- Recommendation 卡片包含：编号 + 标题 + 2-3 句详细描述（不是一句话）
- 封面不能信息过密，但内容页不能信息过稀

### Rule 11: Failure Handling
- Gate failure → retry (max 2) → blocked (return None, no crash)
- Never `raise ValueError` on Gate failure
- Blocked stages save state for `RunManager.resume()` recovery
- Per-page markers enable partial recovery after crash

---

## 7-STAGE PIPELINE

```
Stage 0: INTERVIEW    → interview.json     (麦肯锡 10 问)
Stage 1: CONFIRM      → requirements.json  (用户确认)
Stage 2: RESEARCH     → research.json      (可跳过，用户自带数据)
Stage 3: OUTLINE      → outline.json       (Pyramid Principle 大纲)
Stage 4: STYLE_LOCK   → style.json         (3 色品牌锁定)
Stage 5: GENERATE     → plan.json          (Planning JSON 合同)
Stage 6: QA           → qa_report.json     (0 CRITICAL 才通过)
Stage 7: EXPORT       → delivery_manifest  (最终 PPTX)
```

**Gate 规则**: 每阶段产物落盘后经 Gate 校验。0 CRITICAL = 通过。失败只回退当前步。

**断点恢复**: 产物文件即 checkpoint。中断后用 `RunManager.resume(run_id)` 自动推断继续。

---

## SLIDE TEMPLATES (10 种)

| Template | JSON `template` 值 | 用途 |
|----------|-------------------|------|
| Cover | `cover` | 封面：全深色背景 + 标题 + 日期 |
| Section Divider | `section_divider` | 章节分隔 |
| Executive Summary | `executive_summary` | KPI 卡片行 (3-4 个) |
| Data Story | `data_story` | Action Title + 大图表 + Insight Box |
| Comparison | `comparison` | 左右分栏对比 |
| Framework | `framework` | 2x2 矩阵 / Issue Tree |
| Table | `table` | 数据表格 |
| Recommendation | `recommendation` | 3 个编号行动卡 |
| Appendix | `appendix` | 附录数据 + 来源 |
| Closing | `closing` | 致谢页 |

---

## PLANNING JSON FORMAT

每页的数据合同（AI 先生成这个 JSON，校验通过后再渲染）：

```json
{
  "metadata": {
    "title": "Deck title",
    "brand": {"primary": "#hex", "secondary": "#hex", "accent": "#hex"},
    "total_slides": 8
  },
  "slides": [
    {
      "slide_number": 1,
      "template": "cover",
      "title": "...",
      "subtitle": "...",
      "date": "April 2026"
    },
    {
      "slide_number": 2,
      "template": "executive_summary",
      "action_title": "Core conclusion sentence with numbers",
      "kpis": [
        {"value": "+57%", "label": "Scenario 1", "detail": "$54M delta"}
      ],
      "source": "Data source, Year"
    },
    {
      "slide_number": 3,
      "template": "data_story",
      "action_title": "Conclusion sentence about what the chart shows",
      "chart": {
        "type": "stacked_bar",
        "data_type": "currency_usd",
        "categories": ["A", "B", "C"],
        "series": [{"name": "Series 1", "values": [10, 20, 30]}],
        "y_axis_title": "Cost ($M)"
      },
      "insight": "Key takeaway from the data",
      "source": "Data source"
    }
  ]
}
```

**Validate before render**: `python -c "from engine.planning_schema import validate_and_report; validate_and_report('plan.json')"`

---

## FILE STRUCTURE

```
consulting-ppt-skill/
├── SKILL.md                    # This file (v3.0)
├── engine/
│   ├── orchestrator.py         # Dispatcher only (no content generation)
│   ├── outline_agent.py        # Pyramid Principle outline generator
│   ├── plan_agent.py           # Planning JSON generator
│   ├── step_registry.py        # 25-step canonical plan
│   ├── state_machine.py        # 7-stage state machine + RunManager
│   ├── gates.py                # Pyramid Principle + Gate checks
│   ├── planning_schema.py      # Planning JSON validation
│   ├── renderer.py             # JSON → PPTX rendering
│   ├── design_system.py        # 3-color brand palette + typography
│   ├── slide_builders.py       # 10 slide templates
│   └── chart_helpers.py        # Waterfall, line, pie charts
├── references/
│   ├── playbooks/
│   │   ├── P0_interview.md     # 麦肯锡 10 问清单
│   │   └── P3_outline.md       # Pyramid Principle 规则
│   ├── design-specs.md
│   ├── layouts.md
│   └── color-guide.md
├── scripts/
│   └── qa_ppt_audit.py         # QA 审计
├── examples/
│   ├── sample_plan.json        # 6 页示例 Plan JSON
│   └── tco_example.py          # Python API 示例
├── artifacts/
│   └── runs/<RUN_ID>/          # 每次运行的产物目录
└── output/                     # 输出目录
```

---

## DESIGN SYSTEM

### Color: 3 Brand Hues → Auto-derived Palette

```
Primary → shade_90 / shade_70 / shade_50 / tint_30 / tint_15 / tint_05
Accent  → accent_dark
Neutrals: white / light_gray / mid_gray / dark_gray / charcoal / black
```

### Typography

```
Cover title:     36pt Bold White
Slide title:     20pt Bold Primary
Subtitle:        12pt Regular Dark gray
KPI value:       36pt Bold White (on dark bg)
Body:            11pt Regular Charcoal
Chart labels:    8pt Regular
Table header:    9pt Bold White on Primary
Source/footer:   7pt Regular Mid gray
```

### Chart Types

`bar` | `stacked_bar` | `grouped_bar` | `line` | `area` | `pie` | `donut` | `waterfall` | `bubble` | `scatter`

---

## REQUIREMENTS

```bash
pip install python-pptx
```

---

## WORKFLOW INTEGRATION

- **mckinsey-consultant skill**: This skill handles STEP 7-8 (generation + QA)
- **frontend-slides skill**: Use for HTML preview before PPTX delivery
- **Standalone**: Full pipeline from one prompt to PPTX

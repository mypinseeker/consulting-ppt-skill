# P3 大纲生成 — Pyramid Principle

> 大纲是整份 PPT 的骨架。必须遵循 Pyramid Principle（金字塔原理）。

---

## 金字塔结构规则

```
                   ┌──────────────────┐
                   │   顶层结论        │  ← 一句话回答 core_question
                   │   (top_conclusion)│
                   └────────┬─────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        ┌─────▼─────┐ ┌────▼─────┐ ┌─────▼─────┐
        │  论点 1    │ │  论点 2   │ │  论点 3    │  ← 2-5 个，MECE
        │ (argument) │ │(argument)│ │ (argument) │
        └─────┬─────┘ └────┬─────┘ └─────┬─────┘
              │            │              │
         ┌────┴────┐  ┌───┴────┐    ┌────┴────┐
         │ 证据/页面│  │证据/页面│    │ 证据/页面│  ← 数据、图表、案例
         └─────────┘  └────────┘    └─────────┘
```

## 校验清单

| 检查项 | 规则 | 严重度 |
|:------|:-----|:------|
| 结论先行 | `top_conclusion` 必须是完整判断句，包含量化结论 | CRITICAL |
| 论点数量 | 2-5 个（受众短期记忆限制） | CRITICAL |
| MECE | 论点之间不重叠、不遗漏 | WARNING |
| So What | 每个论点标题必须是结论，不是主题词 | WARNING |
| 支撑充分 | 每个论点至少有 1 个 slide 或 evidence | WARNING |
| 叙事流 | 论点间有逻辑递进（现状→问题→方案 或 结论→证据→行动） | INFO |

## 大纲输出格式

```json
{
  "top_conclusion": "Switching vendors costs 22-57% more than staying across all scenarios",
  "narrative_flow": "conclusion_first",
  "arguments": [
    {
      "title": "Migration and multi-vendor costs dominate the switching premium",
      "slides": [
        {"template": "data_story", "focus": "stacked cost breakdown"},
        {"template": "comparison", "focus": "stay vs switch timeline"}
      ],
      "evidence": ["TCO Model Q1 2026", "Vendor deployment commitments"]
    },
    {
      "title": "Stay scenario delivers 16 months faster 5G rollout",
      "slides": [
        {"template": "comparison", "focus": "deployment timeline"}
      ],
      "evidence": ["Vendor roadmap presentations"]
    },
    {
      "title": "Three actions capture value without switching risk",
      "slides": [
        {"template": "recommendation", "focus": "negotiate + modernize + reserve"}
      ],
      "evidence": ["Negotiation playbook", "Industry benchmarks"]
    }
  ]
}
```

## 页面序列生成规则

从大纲自动生成页面序列：

```
1. Cover（封面）
2. Executive Summary（顶层结论 + KPI）
3-N. 每个 argument 的支撑页面
N+1. Recommendation（如果有 actions）
N+2. Closing
```

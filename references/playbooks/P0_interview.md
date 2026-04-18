# P0 麦肯锡 10 问采访

> 在生成任何内容之前，必须完成以下 10 个问题的采访。
> 用户可以跳过标记为 (可选) 的问题，但前 5 个为必答。

---

## 必答问题（CRITICAL — 缺失则无法进入 OUTLINE 阶段）

### Q1. 谁是受众？
- CEO / Board / 运营层 / 技术层 / 投资人 / 外部客户？
- 受众的知识水平？（行业专家 vs 需要基础铺垫）
- 示例回答："CTO + 技术委员会，熟悉 RAN 架构"

### Q2. 核心问题是什么？（一句话）
- 这份 PPT 要回答的唯一问题
- 示例："Should we switch RAN vendors or stay with the current one?"

### Q3. 你的结论/假设是什么？
- 结论先行：你已经知道答案是什么了吗？
- 如果不确定，写下最强假设
- 示例："Staying is 22-57% cheaper than switching"

### Q4. 支撑结论的关键论点（2-5 个）
- 每个论点对应 PPT 的一个 section
- 遵循 MECE：不重叠、不遗漏
- 示例：
  1. "Migration costs dominate the switching premium"
  2. "Stay delivers faster 5G rollout"
  3. "Three actions capture value without switching risk"

### Q5. 有哪些数据支撑？
- 列出已有的数据来源（Excel / CSV / 报告 / 模型）
- 标注哪些数据是确定的（A 级），哪些是估算的（B 级）
- 示例："TCO Model Q1 2026 (A 级), Vendor quotes (A 级), Deployment timeline (B 级)"

---

## 可选问题（建议回答，提高 PPT 质量）

### Q6. 反对意见是什么？如何回应？ (可选)
- 受众可能的质疑点
- 你的预备回应
- 示例："Board 可能认为 switching 能获得更好的 5G 技术 → 回应：新旧厂商 5G spec 差异 <5%"

### Q7. 行动建议是什么？ (可选)
- 你希望受众看完 PPT 后做什么？
- 1-3 个具体行动
- 示例："1. 用 RFP 压力谈判 10-15% 降价；2. 加速 5G 部署；3. 保留备选厂商资格"

### Q8. 品牌色（3 色）？ (可选)
- Primary / Secondary / Accent 的 hex 值
- 如果不提供，使用默认麦肯锡配色 (#00377B / #009FDB / #FFD100)

### Q9. 页数范围？ (可选)
- 建议范围：8-15 页（麦肯锡标准 deck）
- 超过 20 页需要特别理由
- 默认：10 页

### Q10. 交付格式？ (可选)
- PPTX（默认，可编辑）
- HTML（预览 + 团队对齐）
- 两者都要

---

## 采访输出格式

采访结果保存为 `interview.json`：

```json
{
  "audience": "CTO + Board",
  "audience_expertise": "high",
  "core_question": "Should we switch RAN vendors or stay?",
  "hypothesis": "Staying is 22-57% cheaper than switching",
  "key_arguments": [
    "Migration costs dominate",
    "Stay delivers faster 5G",
    "Three actions capture value"
  ],
  "data_sources": [
    {"name": "TCO Model", "confidence": "A"},
    {"name": "Vendor quotes", "confidence": "A"}
  ],
  "counterarguments": "Board may prefer newer 5G tech",
  "actions": ["Negotiate 10-15%", "Accelerate 5G", "Keep backup qualified"],
  "brand": {"primary": "#00377B", "secondary": "#009FDB", "accent": "#FFD100"},
  "page_count": "8-12",
  "format": "PPTX"
}
```

## Gate 规则

`interview.json` 必须包含 `audience`、`core_question`、`hypothesis` 才能通过 Gate 进入下一阶段。

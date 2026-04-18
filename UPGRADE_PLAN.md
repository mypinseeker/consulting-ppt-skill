# Consulting PPT Skill 升级计划 — v1.0 → v2.0

> 基于 sunbigfly/ppt-agent-skills (v4.1, 615⭐) 的架构思路
> 结合你的麦肯锡咨询定位，取其精华，适配你的场景

---

## 一、你的 v1.0 vs ppt-agent-skills v4.1 对比

| 维度 | 你的 v1.0 | ppt-agent-skills v4.1 | 差距 |
|:-----|:---------|:---------------------|:-----|
| **工作流** | 手动调用 Python API 拼装幻灯片 | 7 阶段状态机自动化（采访→大纲→风格→规划→生成→QA→导出） | 🔴 大 |
| **输入方式** | 代码调用 `deck.add_kpi_slide(...)` | 一句话需求："帮我做一份 15 页路演 deck" | 🔴 大 |
| **QA 机制** | 静态审计（对比度/单位/字体） | 像素级 Visual QA（截图→AI 审视→DOM 重写） | 🟡 中 |
| **断点恢复** | 无 | 扫描磁盘产物自动恢复 | 🟡 中 |
| **数据/渲染隔离** | 无（直接 python-pptx 操作） | JSON 合同先验证 → 再驱动 HTML → 再导出 PPTX | 🔴 大 |
| **多阶段隔离** | 无（单脚本） | 每阶段独立 subagent，防止上下文污染 | 🔴 大 |
| **设计系统** | ✅ 3 色 + shade/tint + 语义色 | 8 套主题风格可选 | 你更严格（麦肯锡标准） |
| **图表** | python-pptx 原生图表 | 13 种 HTML 图表模板 | 🟡 中 |
| **方法论** | ✅ Action Title + 密度规则 | 通用型，无咨询方法论 | 你更专业 |
| **输出格式** | PPTX only | HTML 预览 + PNG PPTX + SVG PPTX 双引擎 | 🟡 中 |

### 结论：你有方法论优势（麦肯锡），他有工程化优势（状态机+QA+隔离）

---

## 二、升级策略：借鉴 5 个核心架构，保留你的麦肯锡 DNA

### 升级 1: 状态机驱动工作流（最重要）

**现状**：用户要写 Python 代码调用 API
**目标**：用户说一句话 → 全自动生成

```
新工作流（7 阶段 State Machine）：

P0 需求采访 ──→ P1 确认 ──→ P2 数据收集 ──→ P3 大纲生成
                                                    ↓
P6 交付 ←── P5 QA审计 ←── P4 逐页生成 ←── P3.5 风格锁定

每阶段：
  产物落盘 → Gate 校验 → 通过才进入下一阶段
  失败 → 只回退当前步骤，不影响前面的产出
```

**新增文件**：
```
consulting-ppt-skill/
├── SKILL.md                      # 升级：加入状态机定义
├── engine/
│   ├── state_machine.py          # 新增：7 阶段状态机
│   ├── gates.py                  # 新增：阶段间 Gate 校验
│   ├── design_system.py          # 保留
│   ├── slide_builders.py         # 保留 + 增强
│   └── chart_helpers.py          # 新增：更多图表类型
├── scripts/
│   ├── qa_ppt_audit.py           # 保留 + 增强（加 Visual QA）
│   ├── visual_qa.py              # 新增：截图 → AI 审视
│   └── exporter.py               # 新增：双格式导出
├── references/
│   ├── playbooks/                # 新增：每阶段的 subagent 执行手册
│   │   ├── P0_interview.md       # 需求采访问题清单
│   │   ├── P2_research.md        # 数据收集规则
│   │   ├── P3_outline.md         # 大纲生成规则（Pyramid Principle）
│   │   ├── P3.5_style.md         # 风格锁定规则
│   │   └── P4_page_gen.md        # 逐页生成规则
│   ├── design-specs.md           # 保留
│   ├── layouts.md                # 保留 + 扩展
│   └── color-guide.md            # 保留
└── artifacts/                    # 新增：产物目录
    └── runs/<RUN_ID>/            # 每次运行的产物
```

---

### 升级 2: 数据层/渲染层隔离（Planning JSON）

**现状**：直接用 python-pptx API 生成，数据和渲染混在一起
**目标**：先生成 Planning JSON（数据合同），验证后再渲染 PPTX

```python
# 现在（v1.0）：数据和渲染混合
deck.add_kpi_slide(
    title="Switching costs 22-57% more",
    kpis=[
        ("+57%", "S1: Bogota", "$54.0M delta"),
    ]
)

# 目标（v2.0）：先生成 JSON 合同
# planning_03.json
{
  "slide_number": 3,
  "template": "kpi_row",
  "action_title": "Switching costs 22-57% more than staying across all scenarios",
  "subtitle": "5-Year TCO comparison",
  "kpis": [
    {"value": "+57%", "label": "S1: Bogota", "detail": "$54.0M delta"},
    {"value": "+47%", "label": "S2: 3-Region", "detail": "$62.1M delta"},
    {"value": "+22%", "label": "S3: Full Network", "detail": "$106.0M delta"}
  ],
  "density_label": "medium",
  "source": "Internal TCO Model, 2026"
}
```

**好处**：
1. JSON 可以被 Gate 校验（必须有 action_title、unit、source）
2. 用户可以在 JSON 层修改内容，不需要改代码
3. 同一份 JSON 可以渲染成 PPTX / HTML / PDF

---

### 升级 3: Visual QA 闭环（像素级审计）

**现状**：`qa_ppt_audit.py` 只检查对比度/字体/单位（静态规则）
**目标**：生成后截图 → AI 审视 → 发现问题自动修复

```
新 QA 流程：

  PPTX 生成
    ↓
  Puppeteer/Playwright 截图每页 → slide-N.png
    ↓
  AI 审视（Claude Vision）：
    ✅ 文字是否溢出容器？
    ✅ 图表标签是否被裁切？
    ✅ 留白是否均匀？
    ✅ 色彩对比是否足够？
    ✅ 信息密度是否 50-70 chars/sq-inch？
    ↓
  如有问题 → 回到 Planning JSON 修改 → 重新渲染
    ↓
  通过 → 标记 QA_PASSED → 进入导出
```

---

### 升级 4: 麦肯锡方法论增强（你的差异化）

ppt-agent-skills 是通用型，你的定位是**咨询级**。增加：

**P0 需求采访 — 麦肯锡 10 问**
```markdown
1. 谁是受众？（CEO/Board/运营层/技术层）
2. 核心问题是什么？（一句话）
3. 你的假设/结论是什么？
4. 支撑结论的 3 个关键论点？
5. 每个论点的数据支撑？
6. 反对意见是什么？如何回应？
7. 行动建议是什么？
8. 品牌色（3 色）？
9. 页数范围？
10. 交付格式（PPTX/HTML/PDF）？
```

**P3 大纲生成 — Pyramid Principle 强制**
```
金字塔结构检查：
  ✅ 开篇 = 结论先行（不是问题先行）
  ✅ 每个 section = 一个支撑论点
  ✅ 每页 = 一个 Action Title（结论，不是主题）
  ✅ MECE 检查：论点之间不重叠、不遗漏
  ✅ So What 检查：每页数据都回答 "所以呢？"
```

**P4 页面模板 — 麦肯锡 7 大版式**
```
1. Cover（全深色背景 + 标题 + 副标题 + 日期）
2. Executive Summary（3-4 个 KPI 卡 + 迷你图表）
3. Data Story（Action Title + 大图表 60-70% + Insight Box）
4. Comparison（左右分栏 / 前后对比）
5. Framework（2x2 矩阵 / Issue Tree / 漏斗）
6. Recommendation（3 个编号行动卡 + 时间线）
7. Appendix（详细数据表格 + 来源说明）
```

---

### 升级 5: 双格式输出（HTML 预览 + PPTX 交付）

**现状**：只输出 PPTX
**目标**：先 HTML 预览对齐 → 确认后输出 PPTX

这与你之前确定的 **PPT 三步法**（4/18 Daily Thinking）完全吻合：
```
Step 1: HTML 先行（frontend-slides → 浏览器预览 → 团队对齐）
Step 2: Excel 图表（数据管理 + 图表编辑）
Step 3: PPTX 交付（consulting-ppt-skill → 最终输出）
```

---

## 三、实施优先级

| 优先级 | 升级项 | 预估工作量 | 价值 |
|:-------|:------|:----------|:-----|
| **P0** | 状态机 + 7 阶段工作流 | 2-3 天 | ⭐⭐⭐⭐⭐ 从"写代码"变成"说一句话" |
| **P0** | Planning JSON 数据合同 | 1 天 | ⭐⭐⭐⭐⭐ 数据/渲染解耦 |
| **P1** | 麦肯锡 10 问采访 + Pyramid Principle | 1 天 | ⭐⭐⭐⭐ 你的差异化 |
| **P1** | 断点恢复（扫描产物推断阶段） | 半天 | ⭐⭐⭐ 长文档不怕中断 |
| **P2** | Visual QA（截图 + AI 审视） | 1-2 天 | ⭐⭐⭐⭐ 像素级质量保证 |
| **P2** | HTML 预览输出 | 1 天 | ⭐⭐⭐ 与 frontend-slides 打通 |
| **P3** | 更多图表模板（瀑布图/桑基图/矩阵） | 1 天 | ⭐⭐⭐ 丰富表达能力 |
| **P3** | 双引擎 PPTX 导出（PNG + SVG） | 1 天 | ⭐⭐ 高保真还原 |

---

## 四、v2.0 目标定位

```
v1.0: "一个 Python 库，帮你生成麦肯锡风格 PPTX"
  ↓
v2.0: "一个 AI Agent Skill，一句话需求 → 自动采访 → 自动大纲 →
       自动生成 → 自动 QA → 交付麦肯锡级 PPTX"
```

**核心差异化 vs ppt-agent-skills**：
- 他是通用型（什么 PPT 都能做）
- 你是咨询型（麦肯锡方法论 + BLM + Pyramid Principle + Action Title）
- 你的受众是需要**咨询级质量**的专业人士

---

## Sources

- [ppt-agent-skills (GitHub)](https://github.com/sunbigfly/ppt-agent-skills)
- [PPTAgent 中科院开源](https://github.com/icip-cas/PPTAgent)
- [开源PPT生成Agent全景](https://blog.csdn.net/hadoopdevelop/article/details/151006914)

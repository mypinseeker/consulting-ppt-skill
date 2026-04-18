# 深度对比：consulting-ppt-skill v2.0 vs ppt-agent-skills v4.1

> 目的：逐维度对比两个项目，找出可学习的具体改进点
> 日期：2026-04-18

---

## 一、架构级对比

| 维度 | 我们 (consulting-ppt v2.0) | 他们 (ppt-agent v4.1) | 差距 | 可学习？ |
|:-----|:-------------------------|:---------------------|:-----|:--------|
| **流水线步数** | 7 阶段（粗粒度） | 54 步（细粒度，每步有 WAIT/RETRY 标记） | 🔴 大 | ✅ 拆细 |
| **主 Agent 角色** | 全干（采访+大纲+渲染+QA） | 只做调度，**绝不写正式产物** | 🔴 大 | ✅ 核心 |
| **Subagent** | 无（单进程） | 每阶段独立 subagent，上下文隔离 | 🔴 大 | ✅ |
| **Gate 机制** | 有（JSON 校验 + Pyramid） | 有 + 双重校验（subagent 自审 + 主 agent 再审） | 🟡 中 | ✅ |
| **失败处理** | 抛异常中止 | RETRY_CURRENT / ROLLBACK→StepID / BLOCKED_PAGE | 🔴 大 | ✅ |
| **人工审核** | 无（全自动） | 可选 Manual Audit：review 阶段 WAIT_USER | 🟡 中 | ✅ |
| **密度管理** | Rule 6 信息密度（粗略） | density_bias + density_curve + 逐页密度窗口（合同级） | 🔴 大 | ✅ |
| **渲染路径** | Planning JSON → python-pptx 直出 | Planning JSON → HTML → 截图审计 → PPTX 导出 | 🟡 中 | 部分 |

---

## 二、他们有但我们没有的 12 个关键设计

### 🔴 P0 — 主 Agent "不写正式产物"原则

**他们**：
> "Only does: 维护计划、调用 harness、管理 subagent 生命周期、校验 Gate、与用户交互"
> "Never does: 写正式交付物、手写 subagent prompt、执行内容生产"
> **红线：所有正式产物必须由对应的 subagent 生成**

**我们**：orchestrator.py 里 `_generate_outline()` 和 `_generate_plan()` 都是主 agent 直接生成的。

**学习点**：主 agent 应该只做调度，内容生成交给专门的 subagent（或至少是独立函数+独立 context）。这防止主 agent 的上下文污染内容质量。

---

### 🔴 P1 — 54 步 Canonical Plan（每步有状态标记）

**他们**：每一步标记了 `WAIT_USER` / `WAIT_AGENT` / `RETRY` / `ROLLBACK`，不是模糊的"7 个阶段"。

**我们**：7 个粗粒度阶段，阶段内逻辑全在 Python 代码里，Claude 看 SKILL.md 只知道"有 7 步"。

**学习点**：把流水线细化到 20-30 步，每步在 SKILL.md 里明确标注：
- 这步需要等用户输入吗？(WAIT_USER)
- 失败了怎么办？(RETRY / ROLLBACK 到哪步)
- 产物是什么？(文件路径)

---

### 🔴 P2 — Subagent 上下文隔离

**他们**：
> "create → RUN → STATUS → FINALIZE → close; 完全隔离模式"
> "强制携带 SUBAGENT_MODEL 参数"
> "Subagent 看不到主 agent 的完整上下文"

**我们**：单进程，所有步骤共享同一个 Python 上下文。

**学习点**：用 Claude Code 的 Agent tool 为每个阶段启动独立 subagent。好处：
1. 大纲 subagent 不会被采访内容的噪音干扰
2. 渲染 subagent 只看到 Plan JSON，不看大纲和采访
3. 每个 subagent 可以用不同的 model（大纲用 Opus，渲染用 Haiku）

---

### 🔴 P3 — 密度合同系统 (Density Contract)

**他们**：
> Step 0 采访时收集 `density_bias`（relaxed / balanced / ultra_dense）
> Step 3 大纲冻结 `density_curve`——每页一个密度窗口
> Step 4 HTML 执行**不能违反密度合同**
> "高密度页不能加 hero image 或复杂装饰"

**我们**：`density_label` 字段存在但没有强制约束，没有逐页密度窗口。

**学习点**：
1. 采访时收集用户偏好（密/松/适中）
2. 大纲阶段给每页标注密度级别
3. Gate 校验：高密度页禁止大图、低密度页禁止超过 3 个要点
4. 密度是**合同**，不是建议

---

### 🔴 P4 — 失败处理三级机制

**他们**：
```
失败类型 → 处理方式
Review 拒绝 → PagePatchAgent 从 review 阶段修补
结构性问题 → Rollback 到 HTML 或 Planning 重做
连续 3 次失败 → BLOCKED_PAGE_N → 暂停，问用户
```

**我们**：Gate 失败 → raise ValueError → 中止全流程。

**学习点**：加 retry 和 rollback 逻辑：
- 单页失败不应中止整个 deck
- 给用户选择：修复 / 简化 / 跳过

---

### 🟡 P5 — 环境感知（Step 0 前置检查）

**他们**：
> "环境嗅探（Step 0 前强制）"：
> - 检测可用 model
> - 检测是否有搜索工具
> - 检测是否有 Python/文件 IO
> - 检测是否支持图片生成
> - 降级方案：搜索不可用→跳过 Research；图片不可用→降级为文字

**我们**：无环境检测，假设一切可用。

**学习点**：在 SKILL.md 顶部加环境检查清单，Claude 先检测能力再决定流程。

---

### 🟡 P6 — Prompt Harness（统一 Prompt 生成器）

**他们**：
> "所有 subagent prompt 通过 `prompt_harness.py` 生成"
> "不允许手动变量替换"
> "模板含 `{{SUBAGENT_NAME}}`, `{{PROMPT_PATH}}`, `{{MODEL}}` 槽位"

**我们**：没有 prompt 模板系统，SKILL.md 里直接写 Python 代码。

**学习点**：对我们的场景（python-pptx 直出），prompt harness 不是最优先的。但如果未来要多 subagent，需要。

---

### 🟡 P7 — 跨会话恢复（Cross-dialogue Recovery）

**他们**：
> "绑定旧 RUN_ID；从 P5→P0 级联检测 Gate"
> "Step 4 重新扫描所有页面 + 重校验"
> "如果 Manual Audit 开启：恢复最新 PNG/review 存档"

**我们**：有 RunManager.resume()，但只推断到阶段级，不做逐页扫描。

**学习点**：Step 4 恢复时应扫描每页的 planningN.json + slide-N 是否完整。

---

### 🟡 P8 — 双重校验（Subagent 自审 + 主 Agent 再审）

**他们**：
> "Subagent FINALIZE 前自审"
> "主 Agent 收到 FINALIZE 后再次校验 Gate"

**我们**：只有主 Agent 校验。

**学习点**：在渲染前让"生成者"先自查一遍（相当于 developer 写完代码先 self-review）。

---

### 🟡 P9 — 搜索分支 + 质量评估

**他们**：
> Step 2A Research 有搜索质量评估：
> "如果质量低 + 未到预算上限 → rollback 扩大范围重搜"
> "如果已到上限 → 标记 SEARCH_QUALITY_LOW → 让用户决定"

**我们**：无 Research 阶段（用户自带数据）。

**学习点**：如果未来要加搜索（比如 WebSearch），需要质量评估 + 用户决策点。

---

### 🟢 P10 — 多来源输入（.pptx 编辑模式）

**他们**：Step 2B 如果输入是 .pptx → 先确认是编辑模式还是新建模式。

**我们**：不支持已有 PPTX 输入。

**学习点**：未来考虑"基于已有 PPTX 优化"的模式。

---

### 🟢 P11 — Manual Audit 检查点

**他们**：用户可以选择在每页 review 阶段手动审批。

**我们**：全自动，无人工检查点。

**学习点**：加一个可选的 `manual_audit: true` 参数，启用后每页渲染后暂停让用户确认。

---

### 🟢 P12 — Delivery Manifest 详细清单

**他们**：`delivery-manifest.json` 包含所有产物路径 + 状态。

**我们**：有 delivery_manifest，但信息较简单。

**学习点**：扩展 manifest 包含：每页截图路径、QA 评分、density 合规状态。

---

## 三、我们有但他们没有的 5 个优势

| 优势 | 说明 |
|:-----|:-----|
| **Pyramid Principle Gate** | 自动检查结论先行、MECE、So What |
| **Action Title 自动验证** | 检测标题是否为判断句 |
| **3 色品牌系统 + 语义色** | 严格 shade/tint 派生，不允许随意加色 |
| **data_type 绑定** | 声明数据类型 → 自动绑定格式，Gate 拦截矛盾 |
| **CJK 溢出检测** | 中文字宽度感知的文本溢出检测 |

---

## 四、优先级排序：应该学哪些？

| 优先级 | 改进项 | 预计工作量 | 价值 |
|:-------|:------|:----------|:-----|
| **P0** | 密度合同系统（采访→大纲→Gate 全链路） | 3-4h | ⭐⭐⭐⭐⭐ |
| **P0** | 失败处理三级机制（retry/rollback/blocked） | 2-3h | ⭐⭐⭐⭐⭐ |
| **P1** | 细化 SKILL.md 到 20-30 步 + WAIT/RETRY 标记 | 2-3h | ⭐⭐⭐⭐ |
| **P1** | Manual Audit 可选检查点 | 1-2h | ⭐⭐⭐ |
| **P2** | 主 Agent 不写产物原则 + Subagent 隔离 | 4-5h | ⭐⭐⭐⭐ |
| **P2** | 环境感知前置检查 | 1h | ⭐⭐⭐ |
| **P3** | 跨会话逐页恢复 | 2h | ⭐⭐⭐ |
| **P3** | 双重校验（自审 + 再审） | 1h | ⭐⭐ |

---

## 五、总结

**他们的核心哲学**：把 AI 当"不可信的执行者"——所有产出必须经过校验，主 Agent 只做调度不做内容，每一步都有失败处理，密度是合同不是建议。

**我们的核心哲学**：把 AI 当"有方法论的咨询师"——Pyramid Principle、Action Title、3 色系统，关注的是"内容质量"而不是"流程可靠性"。

**最大差距**：我们在"内容质量规则"上更强，但在"流程鲁棒性"上差很多。ppt-agent 的 54 步流水线 + 三级失败处理 + 密度合同，让它在生产环境中更可靠。

**行动建议**：保留我们的方法论优势，补上他们的流程鲁棒性——特别是密度合同和失败处理。

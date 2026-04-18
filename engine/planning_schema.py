"""
Planning Schema — JSON 合同层
==============================
数据和渲染之间的合同。AI 先生成 Planning JSON，校验通过后再渲染 PPTX。

设计原则（约束式自由）：
  - 硬约束（enum/required）：模板类型、Action Title 必须是判断句、数据必须带单位
  - 软自由（oneOf/optional）：图表类型选择、叙事顺序、布局提示
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


# ====================================================================
# 校验错误
# ====================================================================

@dataclass
class ValidationError:
    slide: int
    field: str
    severity: str   # CRITICAL / WARNING / INFO
    message: str

    def __str__(self):
        return f"[{self.severity}] Slide {self.slide} → {self.field}: {self.message}"


# ====================================================================
# 模板类型枚举
# ====================================================================

VALID_TEMPLATES = {
    "cover",               # 封面：全深色背景 + 标题 + 副标题 + 日期
    "section_divider",     # 章节分隔页
    "executive_summary",   # KPI 卡片行 + 迷你图表
    "data_story",          # Action Title + 大图表(60-70%) + Insight Box
    "comparison",          # 左右分栏 / 前后对比
    "framework",           # 2x2 矩阵 / Issue Tree / 漏斗
    "table",               # 数据表格
    "recommendation",      # 3 个编号行动卡
    "appendix",            # 附录数据表 + 来源说明
    "closing",             # 致谢页
}

VALID_CHART_TYPES = {
    "bar", "stacked_bar", "grouped_bar",
    "line", "area",
    "pie", "donut",
    "waterfall",
    "bubble", "scatter",
}

# ====================================================================
# 数据类型 → 格式绑定（约束式自由的"约束"部分）
# ====================================================================

VALID_DATA_TYPES = {
    "percentage":  '#,##0"%"',       # 增长率、占比、渗透率
    "currency_usd": '$#,##0',        # 美元
    "currency_eur": '€#,##0',        # 欧元
    "currency_cny": '¥#,##0',        # 人民币
    "score":       '#,##0.0',        # 评分、指数
    "count":       '#,##0',          # 数量、人数、户数
    "ratio":       '#,##0.0',        # 比率（非百分比）
    "plain":       '#,##0',          # 纯数字
}

def _check_data_type_consistency(chart: dict, sn: int) -> list:
    """检查 chart 的 data_type 是否与 y_axis_title 一致"""
    errors = []
    data_type = chart.get("data_type")
    y_title = (chart.get("y_axis_title") or "").lower()

    if not data_type:
        # 没有声明 data_type → WARNING，建议添加
        if y_title:
            errors.append(ValidationError(sn, "chart.data_type", "WARNING",
                f"图表缺少 data_type 字段。y_axis='{chart.get('y_axis_title')}' "
                f"建议添加 data_type (可选: {sorted(VALID_DATA_TYPES.keys())})"))
        return errors

    if data_type not in VALID_DATA_TYPES:
        errors.append(ValidationError(sn, "chart.data_type", "WARNING",
            f"未知 data_type '{data_type}'，可选: {sorted(VALID_DATA_TYPES.keys())}"))
        return errors

    # 交叉验证：data_type 和 y_axis_title 是否矛盾
    contradictions = {
        "percentage": ["$", "€", "¥", "usd", "eur", "cost", "price", "月费"],
        "currency_usd": ["%", "率", "评分", "score", "ratio"],
        "currency_eur": ["%", "率", "评分", "score", "$", "usd"],
        "score": ["$", "€", "%", "率"],
    }

    if data_type in contradictions:
        for bad_keyword in contradictions[data_type]:
            if bad_keyword in y_title:
                errors.append(ValidationError(sn, "chart.data_type", "CRITICAL",
                    f"data_type='{data_type}' 与 y_axis_title='{chart.get('y_axis_title')}' 矛盾！"
                    f"（'{bad_keyword}' 不应出现在 {data_type} 类型的图表中）"))
                break

    return errors

VALID_DENSITY_LABELS = {"low", "medium", "high"}

# ====================================================================
# 占位数据检测
# ====================================================================

PLACEHOLDER_PATTERNS = [
    r"^Category [A-Z]$",
    r"^Option [A-Z]$",
    r"^Point \d+$",
    r"^Series \d+$",
    r"^Data source to be confirmed$",
    r"^Key insight from:",
    r"^#\d+$",           # KPI 值 = "#1", "#2"
    r"^To be confirmed$",
    r"^(?:100|150|120|200|250|300)$",  # 常见占位值（精确匹配）
]

import re as _re
_PLACEHOLDER_RES = [_re.compile(p, _re.IGNORECASE) for p in PLACEHOLDER_PATTERNS]


def _is_placeholder(text: str) -> bool:
    """检测文本是否为占位内容"""
    text = text.strip()
    for pattern in _PLACEHOLDER_RES:
        if pattern.match(text):
            return True
    return False

# ====================================================================
# Action Title 校验规则
# ====================================================================

# 不合格的 Action Title 模式（主题式标题）
BAD_TITLE_PATTERNS = [
    r"^(Overview|Summary|Analysis|Comparison|Timeline|Background|Introduction|Appendix|Agenda)$",
    r"^(市场分析|概述|总结|背景|议程|对比|时间线)$",
]

# 合格的 Action Title 特征：包含动词或量化结论
GOOD_TITLE_SIGNALS = [
    r"\d",                        # 包含数字
    r"(cost|save|increase|decrease|grow|decline|reduce|exceed|outperform)",
    r"(导致|超过|节省|增长|下降|占比|达到|降低|提升)",
    r"(more than|less than|compared to|versus|vs\.?)",
]

# 免检模板（封面、分隔、致谢不需要 Action Title）
ACTION_TITLE_EXEMPT = {"cover", "section_divider", "closing", "appendix"}


def _is_action_title(title: str) -> bool:
    """检查标题是否为 Action Title（结论句，不是主题词）"""
    if not title or len(title) < 10:
        return False

    # 如果匹配坏模式 → 不合格
    for pattern in BAD_TITLE_PATTERNS:
        if re.match(pattern, title.strip(), re.IGNORECASE):
            return False

    # 如果包含好信号 → 合格
    for pattern in GOOD_TITLE_SIGNALS:
        if re.search(pattern, title, re.IGNORECASE):
            return True

    # 如果标题足够长（>30 字符），大概率是判断句
    if len(title) > 30:
        return True

    return False


# ====================================================================
# 单位校验
# ====================================================================

UNIT_PATTERN = re.compile(r"[\$€¥%]|\b(M|B|K|bn|mn|months?|years?|days?|bps|pp|万|亿)\b", re.IGNORECASE)


def _has_unit(value: str) -> bool:
    """检查数值是否带单位"""
    return bool(UNIT_PATTERN.search(str(value)))


# ====================================================================
# 核心校验函数
# ====================================================================

def validate_plan(plan_path: str) -> List[ValidationError]:
    """
    校验 Planning JSON 合同。

    Args:
        plan_path: JSON 文件路径

    Returns:
        错误列表。空列表 = 通过 Gate。

    Gate 规则：0 CRITICAL = 通过，WARNING 记录但不阻塞。
    """
    errors: List[ValidationError] = []
    path = Path(plan_path)

    # 文件存在性
    if not path.exists():
        errors.append(ValidationError(0, "file", "CRITICAL", f"文件不存在: {plan_path}"))
        return errors

    # JSON 解析
    try:
        with open(path) as f:
            plan = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(ValidationError(0, "json", "CRITICAL", f"JSON 解析失败: {e}"))
        return errors

    # 顶层结构
    if "metadata" not in plan:
        errors.append(ValidationError(0, "metadata", "WARNING", "缺少 metadata 字段"))

    if "slides" not in plan or not isinstance(plan["slides"], list):
        errors.append(ValidationError(0, "slides", "CRITICAL", "缺少 slides 数组"))
        return errors

    if len(plan["slides"]) == 0:
        errors.append(ValidationError(0, "slides", "CRITICAL", "slides 数组为空"))
        return errors

    # 逐页校验
    for i, slide in enumerate(plan["slides"]):
        sn = slide.get("slide_number", i + 1)

        # 必填字段
        if "template" not in slide:
            errors.append(ValidationError(sn, "template", "CRITICAL", "缺少 template 字段"))
            continue

        template = slide["template"]
        if template not in VALID_TEMPLATES:
            errors.append(ValidationError(sn, "template", "CRITICAL",
                          f"无效模板 '{template}'，可选: {sorted(VALID_TEMPLATES)}"))
            continue

        # Action Title 校验（非免检模板）
        if template not in ACTION_TITLE_EXEMPT:
            title = slide.get("action_title", "")
            if not title:
                errors.append(ValidationError(sn, "action_title", "CRITICAL",
                              "内容页缺少 action_title"))
            else:
                if not _is_action_title(title):
                    errors.append(ValidationError(sn, "action_title", "WARNING",
                                  f"Action Title 可能不是判断句: '{title}'。"
                                  f"好的 Action Title 示例: 'Switching costs 22-57% more than staying'"))
                # 长度限制：20pt 字体在 11.5" 宽框内，中文约 40 字、英文约 80 字符
                cn_count = sum(1 for c in title if ord(c) > 127)
                if cn_count > len(title) * 0.3:
                    # 中文为主
                    if len(title) > 50:
                        errors.append(ValidationError(sn, "action_title", "WARNING",
                                      f"Action Title 过长 ({len(title)}字, {cn_count}中文)，"
                                      f"建议中文 ≤45 字以避免溢出"))
                else:
                    if len(title) > 90:
                        errors.append(ValidationError(sn, "action_title", "WARNING",
                                      f"Action Title 过长 ({len(title)}字)，建议英文 ≤85 字"))

        # KPI 值/标签长度限制（36pt 值 + 10pt 标签在 2.7"×1.4" 盒子里）
        if template == "executive_summary":
            for j, kpi in enumerate(slide.get("kpis", [])):
                label = kpi.get("label", "")
                detail = kpi.get("detail", "")
                combined = f"{label}{detail}"
                cn = sum(1 for c in combined if ord(c) > 127)
                if cn > 0 and len(combined) > 15:
                    errors.append(ValidationError(sn, f"kpis[{j}].label", "WARNING",
                                  f"KPI 标签+详情过长 ({len(combined)}字, {cn}中文)，"
                                  f"建议中文合计 ≤12 字以避免在 KPI 盒子中溢出"))

        # 封面标题+副标题总长限制（36pt+16pt 在 10"×1.5"）
        if template == "cover":
            title = slide.get("title", "")
            subtitle = slide.get("subtitle", "")
            combined = f"{title} {subtitle}"
            cn = sum(1 for c in combined if ord(c) > 127)
            if cn > 0 and len(combined) > 40:
                errors.append(ValidationError(sn, "cover.title+subtitle", "WARNING",
                              f"封面标题+副标题过长 ({len(combined)}字, {cn}中文)，"
                              f"建议合计 ≤35 中文字以避免溢出。可将副标题缩短。"))

        # 密度标签
        density = slide.get("density_label")
        if density and density not in VALID_DENSITY_LABELS:
            errors.append(ValidationError(sn, "density_label", "WARNING",
                          f"无效 density_label '{density}'，可选: {sorted(VALID_DENSITY_LABELS)}"))

        # Density contract enforcement
        if template not in ACTION_TITLE_EXEMPT:
            dl = slide.get("density_label")
            if not dl:
                errors.append(ValidationError(sn, "density_label", "WARNING",
                              "内容页缺少 density_label（建议标注 low/medium/high）"))
            elif dl == "high":
                # High density pages: warn if chart has too many series
                chart = slide.get("chart", {})
                n_series = len(chart.get("series", []))
                if n_series > 4:
                    errors.append(ValidationError(sn, "density", "WARNING",
                                  f"高密度页有 {n_series} 个数据系列，可能过于拥挤（建议 ≤4）"))
            elif dl == "low":
                # Low density pages: warn if too many data points
                kpis = slide.get("kpis", [])
                recs = slide.get("recommendations", [])
                points = slide.get("left", {}).get("points", []) + slide.get("right", {}).get("points", [])
                total = len(kpis) + len(recs) + len(points)
                if total > 3:
                    errors.append(ValidationError(sn, "density", "WARNING",
                                  f"低密度页有 {total} 个内容项，建议 ≤3"))

        # 来源/脚注
        if template in ("data_story", "table", "comparison", "framework"):
            if not slide.get("source"):
                errors.append(ValidationError(sn, "source", "INFO",
                              "数据页缺少 source 字段（建议添加数据来源）"))

        # KPI / 数据点单位校验
        if template == "executive_summary":
            for j, kpi in enumerate(slide.get("kpis", [])):
                value = kpi.get("value", "")
                if value and not _has_unit(value):
                    errors.append(ValidationError(sn, f"kpis[{j}].value", "WARNING",
                                  f"KPI 值 '{value}' 缺少单位（$M, %, months 等）"))

        # 图表类型校验 + 占位数据检测
        if template == "data_story":
            chart = slide.get("chart", {})
            chart_type = chart.get("type")
            if chart_type and chart_type not in VALID_CHART_TYPES:
                errors.append(ValidationError(sn, "chart.type", "WARNING",
                              f"未知图表类型 '{chart_type}'，可选: {sorted(VALID_CHART_TYPES)}"))

            # 数据类型一致性检查
            errors.extend(_check_data_type_consistency(chart, sn))

            # 检测图表占位数据
            for cat in chart.get("categories", []):
                if _is_placeholder(str(cat)):
                    errors.append(ValidationError(sn, "chart.categories", "CRITICAL",
                                  f"图表包含占位数据: '{cat}'。必须替换为真实数据"))
                    break

            # 检测 insight 占位
            insight = slide.get("insight", "")
            if insight and _is_placeholder(insight):
                errors.append(ValidationError(sn, "insight", "WARNING",
                              f"Insight 是占位文本: '{insight}'。应替换为真正的数据洞察"))

            # 检测 source 占位
            source = slide.get("source", "")
            if source and _is_placeholder(source):
                errors.append(ValidationError(sn, "source", "WARNING",
                              f"Source 是占位文本: '{source}'。应替换为真实数据来源"))

        # KPI 占位值检测
        if template == "executive_summary":
            for j, kpi in enumerate(slide.get("kpis", [])):
                value = kpi.get("value", "")
                if _is_placeholder(str(value)):
                    errors.append(ValidationError(sn, f"kpis[{j}].value", "CRITICAL",
                                  f"KPI 值是占位数据: '{value}'。必须替换为真实数据（如 '+57%', '$194亿'）"))

    # 结构完整性
    templates_used = [s.get("template") for s in plan["slides"]]
    if "cover" not in templates_used:
        errors.append(ValidationError(0, "structure", "WARNING", "缺少 cover 页"))
    if templates_used[0] != "cover":
        errors.append(ValidationError(0, "structure", "INFO", "第一页建议为 cover"))

    return errors


def validate_and_report(plan_path: str) -> bool:
    """校验并打印报告。返回 True = 通过 Gate。"""
    errors = validate_plan(plan_path)

    if not errors:
        print("✅ Planning JSON 校验通过 — 0 errors")
        return True

    criticals = [e for e in errors if e.severity == "CRITICAL"]
    warnings = [e for e in errors if e.severity == "WARNING"]
    infos = [e for e in errors if e.severity == "INFO"]

    print(f"📋 校验结果: {len(criticals)} CRITICAL / {len(warnings)} WARNING / {len(infos)} INFO")
    print("-" * 60)
    for e in errors:
        icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}[e.severity]
        print(f"  {icon} {e}")

    passed = len(criticals) == 0
    print("-" * 60)
    print(f"{'✅ GATE PASSED' if passed else '❌ GATE FAILED'} — 0 CRITICAL required")
    return passed


def self_review_plan(plan_path: str) -> List[ValidationError]:
    """
    Self-review: 渲染前的二次校验（生成者视角）。
    检查 validate_plan 不覆盖的语义问题。
    """
    errors = []
    path = Path(plan_path)
    if not path.exists():
        return errors

    plan = json.loads(path.read_text())
    slides = plan.get("slides", [])

    # 1. 叙事连贯性：相邻页标题不应重复关键词超过 50%
    prev_title = ""
    for slide in slides:
        title = slide.get("action_title", "")
        if title and prev_title:
            words_curr = set(title.lower().split())
            words_prev = set(prev_title.lower().split())
            stopwords = {"the", "a", "an", "is", "are", "and", "or", "of", "in", "to",
                         "的", "是", "在", "和", "与"}
            words_curr -= stopwords
            words_prev -= stopwords
            if words_curr and words_prev:
                overlap = len(words_curr & words_prev) / min(len(words_curr), len(words_prev))
                if overlap > 0.6:
                    errors.append(ValidationError(
                        slide.get("slide_number", 0), "narrative",
                        "WARNING",
                        f"相邻页标题重复度 {overlap:.0%}：可能叙事不够递进"))
        if title:
            prev_title = title

    # 2. 图表类型多样性：连续 3+ 页用同一图表类型
    chart_types = []
    for slide in slides:
        ct = slide.get("chart", {}).get("type", "")
        chart_types.append(ct if ct else None)
    for i in range(len(chart_types) - 2):
        if chart_types[i] and chart_types[i] == chart_types[i+1] == chart_types[i+2]:
            errors.append(ValidationError(
                i+1, "chart_variety", "INFO",
                f"连续 3 页使用 '{chart_types[i]}' 图表，建议变换图表类型增加视觉多样性"))
            break

    # 3. 总页数合理性
    n = len(slides)
    if n > 15:
        errors.append(ValidationError(0, "page_count", "WARNING",
                      f"共 {n} 页，超过建议的 15 页上限。受众注意力有限。"))
    elif n < 4:
        errors.append(ValidationError(0, "page_count", "WARNING",
                      f"共 {n} 页，内容可能不足。建议至少 5 页。"))

    return errors


# ====================================================================
# CLI 入口
# ====================================================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python planning_schema.py <plan.json>")
        sys.exit(1)
    passed = validate_and_report(sys.argv[1])
    sys.exit(0 if passed else 1)

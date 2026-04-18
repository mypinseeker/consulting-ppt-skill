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

VALID_DENSITY_LABELS = {"low", "medium", "high"}

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
            elif not _is_action_title(title):
                errors.append(ValidationError(sn, "action_title", "WARNING",
                              f"Action Title 可能不是判断句: '{title}'。"
                              f"好的 Action Title 示例: 'Switching costs 22-57% more than staying'"))

        # 密度标签
        density = slide.get("density_label")
        if density and density not in VALID_DENSITY_LABELS:
            errors.append(ValidationError(sn, "density_label", "WARNING",
                          f"无效 density_label '{density}'，可选: {sorted(VALID_DENSITY_LABELS)}"))

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

        # 图表类型校验
        if template == "data_story":
            chart = slide.get("chart", {})
            chart_type = chart.get("type")
            if chart_type and chart_type not in VALID_CHART_TYPES:
                errors.append(ValidationError(sn, "chart.type", "WARNING",
                              f"未知图表类型 '{chart_type}'，可选: {sorted(VALID_CHART_TYPES)}"))

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

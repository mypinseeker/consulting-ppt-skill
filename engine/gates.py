"""
Gates — 阶段间校验规则
======================
所有 Gate 函数已集成在 state_machine.py 中。
本文件提供额外的 Pyramid Principle 深度校验工具。
"""

import json
import re
from pathlib import Path
from typing import List, Tuple


def check_pyramid_principle(outline: dict) -> List[Tuple[str, str]]:
    """
    Pyramid Principle 深度校验。

    检查项：
      1. 结论先行：top_conclusion 必须是完整判断句
      2. MECE：论点之间不重叠、不遗漏
      3. So What：每个论点必须回答"所以呢？"
      4. 层级一致：同级论点的粒度应相似

    Returns:
        [(severity, message), ...]
    """
    issues = []

    # 1. 结论先行
    conclusion = outline.get("top_conclusion", "")
    if not conclusion:
        issues.append(("CRITICAL", "缺少顶层结论（top_conclusion）"))
    elif len(conclusion) < 15:
        issues.append(("WARNING", f"顶层结论太短 ({len(conclusion)} 字符)，应为完整判断句"))
    elif not any(c.isdigit() for c in conclusion):
        issues.append(("INFO", "顶层结论没有量化数据，建议加入关键数字"))

    # 2. 论点结构
    arguments = outline.get("arguments", [])
    if len(arguments) < 2:
        issues.append(("CRITICAL", f"论点数量不足 ({len(arguments)})，Pyramid 至少需要 2 个支撑论点"))
    elif len(arguments) > 5:
        issues.append(("WARNING", f"论点过多 ({len(arguments)})，建议 3-5 个（受众记忆力有限）"))

    # 3. 每个论点检查
    titles = []
    for i, arg in enumerate(arguments):
        title = arg.get("title", "")
        if not title:
            issues.append(("CRITICAL", f"论点 {i+1} 缺少标题"))
            continue

        titles.append(title)

        # So What 检查：标题应该是结论，不是主题
        topic_patterns = [
            r"^(Background|Overview|Data|Analysis|Results|Discussion)$",
            r"^(背景|概述|数据|分析|结果|讨论)$",
        ]
        for p in topic_patterns:
            if re.match(p, title.strip(), re.IGNORECASE):
                issues.append(("WARNING",
                    f"论点 {i+1} 标题 '{title}' 是主题词不是结论。"
                    f"应改为回答 'So What?' 的判断句"))

        # 支撑材料
        slides = arg.get("slides", [])
        evidence = arg.get("evidence", [])
        if not slides and not evidence:
            issues.append(("WARNING", f"论点 {i+1} '{title}' 缺少支撑（slides 或 evidence）"))

    # 4. MECE 粗检（基于标题关键词重叠度）
    if len(titles) >= 2:
        for i in range(len(titles)):
            for j in range(i + 1, len(titles)):
                words_i = set(titles[i].lower().split())
                words_j = set(titles[j].lower().split())
                # 去掉常见虚词
                stopwords = {"the", "a", "an", "is", "are", "and", "or", "of", "in", "to", "for",
                             "的", "是", "在", "和", "与", "了", "不", "有"}
                words_i -= stopwords
                words_j -= stopwords
                if words_i and words_j:
                    overlap = words_i & words_j
                    overlap_ratio = len(overlap) / min(len(words_i), len(words_j))
                    if overlap_ratio > 0.5:
                        issues.append(("WARNING",
                            f"论点 {i+1} 和论点 {j+1} 可能重叠 "
                            f"(共同词: {overlap})，检查是否 MECE"))

    return issues


def validate_outline_file(path: str) -> bool:
    """校验 outline.json 并打印报告"""
    data = json.loads(Path(path).read_text())
    issues = check_pyramid_principle(data)

    if not issues:
        print("✅ Pyramid Principle 校验通过")
        return True

    criticals = [i for i in issues if i[0] == "CRITICAL"]
    warnings = [i for i in issues if i[0] == "WARNING"]
    infos = [i for i in issues if i[0] == "INFO"]

    print(f"📋 Pyramid Principle: {len(criticals)} CRITICAL / {len(warnings)} WARNING / {len(infos)} INFO")
    for severity, msg in issues:
        icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}[severity]
        print(f"  {icon} {msg}")

    return len(criticals) == 0


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python gates.py <outline.json>")
        sys.exit(1)
    passed = validate_outline_file(sys.argv[1])
    sys.exit(0 if passed else 1)

"""
Step Registry — 25-step canonical plan with WAIT/RETRY/ROLLBACK markers
========================================================================
Maps the 7 Stage enum to 25 fine-grained steps for SKILL.md documentation.
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional

class StepAction(IntEnum):
    AUTO = 0          # Fully automatic
    WAIT_USER = 1     # Pause for user input
    WAIT_AGENT = 2    # Wait for subagent completion
    RETRY = 3         # Can retry on failure
    ROLLBACK = 4      # Can rollback to previous step

@dataclass
class Step:
    id: str
    name: str
    stage: str           # Maps to Stage enum
    action: StepAction
    artifact: str        # Output file
    rollback_to: Optional[str] = None
    description: str = ""

# 25-step canonical plan
CANONICAL_PLAN = [
    # P0: Interview
    Step("P0.01", "环境检查", "INTERVIEW", StepAction.AUTO, "", description="检测 python-pptx/磁盘/权限"),
    Step("P0.02", "采访用户", "INTERVIEW", StepAction.WAIT_USER, "interview.json", description="麦肯锡 11 问"),
    Step("P0.03", "采访 Gate", "INTERVIEW", StepAction.RETRY, "", rollback_to="P0.02", description="校验必填字段+density_bias"),

    # P1: Confirm
    Step("P1.01", "需求摘要", "CONFIRM", StepAction.AUTO, "requirements.json", description="生成需求确认文档"),
    Step("P1.02", "用户确认", "CONFIRM", StepAction.WAIT_USER, "", description="用户审阅并确认需求"),

    # P2: Research (optional)
    Step("P2.01", "判断是否需要搜索", "RESEARCH", StepAction.AUTO, "", description="用户自带数据→跳过"),
    Step("P2.02", "数据收集", "RESEARCH", StepAction.WAIT_AGENT, "research.json", description="WebSearch 或本地资料压缩"),
    Step("P2.03", "质量评估", "RESEARCH", StepAction.RETRY, "", rollback_to="P2.02", description="搜索质量低→扩大范围重搜"),

    # P3: Outline
    Step("P3.01", "生成大纲", "OUTLINE", StepAction.AUTO, "outline.json", description="Pyramid Principle 大纲"),
    Step("P3.02", "密度窗口标注", "OUTLINE", StepAction.AUTO, "", description="逐页标注 density_target"),
    Step("P3.03", "大纲 Gate", "OUTLINE", StepAction.RETRY, "", rollback_to="P3.01", description="Pyramid+MECE+density 校验"),
    Step("P3.04", "用户确认大纲", "OUTLINE", StepAction.WAIT_USER, "", description="可选：用户审阅大纲结构"),

    # P3.5: Style Lock
    Step("P3.5.01", "品牌色锁定", "STYLE_LOCK", StepAction.AUTO, "style.json", description="3色+字体+extreme检测"),
    Step("P3.5.02", "风格 Gate", "STYLE_LOCK", StepAction.RETRY, "", rollback_to="P3.5.01", description="校验 3 色完整性"),

    # P4: Generate
    Step("P4.01", "生成 Plan JSON", "GENERATE", StepAction.AUTO, "plan.json", description="逐页 Planning 合同"),
    Step("P4.02", "占位数据检测", "GENERATE", StepAction.AUTO, "", description="拦截 Category A/#1 等占位"),
    Step("P4.03", "data_type 一致性", "GENERATE", StepAction.AUTO, "", description="data_type vs y_axis 矛盾检测"),
    Step("P4.04", "CJK 长度校验", "GENERATE", StepAction.AUTO, "", description="标题/KPI 中文字数限制"),
    Step("P4.05", "Plan Gate", "GENERATE", StepAction.RETRY, "", rollback_to="P4.01", description="0 CRITICAL 才通过"),

    # P5: QA
    Step("P5.01", "渲染 PPTX", "QA", StepAction.AUTO, "deck.pptx", description="Plan JSON → python-pptx"),
    Step("P5.02", "Visual QA 扫描", "QA", StepAction.AUTO, "qa_report.json", description="7 检查项（溢出/对比度/密度等）"),
    Step("P5.03", "QA Gate", "QA", StepAction.RETRY, "", rollback_to="P4.01", description="0 CRITICAL 才通过"),
    Step("P5.04", "人工审核", "QA", StepAction.WAIT_USER, "", description="可选：Manual Audit 逐页审批"),

    # P6: Export
    Step("P6.01", "生成交付清单", "EXPORT", StepAction.AUTO, "delivery_manifest.json", description="产物路径+QA评分"),
    Step("P6.02", "完成", "EXPORT", StepAction.AUTO, "", description="输出最终 PPTX 路径"),
]

def get_step(step_id: str) -> Optional[Step]:
    for s in CANONICAL_PLAN:
        if s.id == step_id:
            return s
    return None

def print_plan():
    """打印完整 25 步计划"""
    current_stage = ""
    for s in CANONICAL_PLAN:
        if s.stage != current_stage:
            current_stage = s.stage
            print(f"\n{'─'*50}")
            print(f"  Stage: {current_stage}")
            print(f"{'─'*50}")
        action_icon = {0: "⚡", 1: "⏸️", 2: "🤖", 3: "🔄", 4: "⏪"}[s.action.value]
        rollback = f" → rollback:{s.rollback_to}" if s.rollback_to else ""
        print(f"  {action_icon} {s.id:8s} {s.name:16s} {s.description}{rollback}")

if __name__ == "__main__":
    print_plan()

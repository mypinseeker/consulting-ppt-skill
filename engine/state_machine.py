"""
State Machine — 7 阶段 PPT 生成工作流
=====================================
文件即状态机：每阶段产物落盘后即为 checkpoint，崩溃后扫描目录自动恢复。

工作流：
  INTERVIEW → CONFIRM → RESEARCH → OUTLINE → STYLE_LOCK → GENERATE → QA → EXPORT

设计原则：
  - 每阶段独立，上下文不跨阶段污染
  - Gate 校验通过才进入下一阶段
  - 失败只回退当前步骤
"""

import json
import os
import shutil
from enum import IntEnum
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from .planning_schema import validate_plan, ValidationError


# ====================================================================
# 阶段定义
# ====================================================================

class Stage(IntEnum):
    INTERVIEW   = 0   # P0: 采访用户，收集需求
    CONFIRM     = 1   # P1: 用户确认需求摘要
    RESEARCH    = 2   # P2: 数据收集（可选，咨询场景用户自带数据）
    OUTLINE     = 3   # P3: 生成叙事大纲（Pyramid Principle）
    STYLE_LOCK  = 4   # P3.5: 锁定品牌色 + 风格
    GENERATE    = 5   # P4: 逐页生成 Planning JSON → PPTX
    QA          = 6   # P5: QA 审计（静态规则 + 可选 Visual QA）
    EXPORT      = 7   # P6: 最终导出 + 交付清单


# 每阶段的产物文件（文件存在 = 该阶段完成）
STAGE_ARTIFACTS = {
    Stage.INTERVIEW:  "interview.json",
    Stage.CONFIRM:    "requirements.json",
    Stage.RESEARCH:   "research.json",
    Stage.OUTLINE:    "outline.json",
    Stage.STYLE_LOCK: "style.json",
    Stage.GENERATE:   "plan.json",
    Stage.QA:         "qa_report.json",
    Stage.EXPORT:     "delivery_manifest.json",
}

# 可跳过的阶段（咨询场景用户通常自带数据）
SKIPPABLE_STAGES = {Stage.RESEARCH}


# ====================================================================
# Gate 定义
# ====================================================================

class GateResult:
    """Gate 校验结果"""
    def __init__(self, passed: bool, errors: List[str] = None):
        self.passed = passed
        self.errors = errors or []

    def __bool__(self):
        return self.passed

    def __repr__(self):
        if self.passed:
            return "GateResult(PASSED)"
        return f"GateResult(FAILED: {self.errors})"


def gate_interview(run_dir: Path) -> GateResult:
    """Gate 0→1: 采访结果必须包含核心问题"""
    path = run_dir / STAGE_ARTIFACTS[Stage.INTERVIEW]
    if not path.exists():
        return GateResult(False, ["interview.json 不存在"])
    data = json.loads(path.read_text())
    required = ["audience", "core_question", "hypothesis"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return GateResult(False, [f"缺少必填字段: {missing}"])

    # Validate density_bias if present
    if "density_bias" in data:
        density_bias = data.get("density_bias")
        valid_values = {"relaxed", "balanced", "ultra_dense"}
        if density_bias not in valid_values:
            return GateResult(False, [f"density_bias 值无效: '{density_bias}'，可选: relaxed/balanced/ultra_dense"])

    return GateResult(True)


def gate_confirm(run_dir: Path) -> GateResult:
    """Gate 1→2: 需求确认文件存在且 confirmed=true"""
    path = run_dir / STAGE_ARTIFACTS[Stage.CONFIRM]
    if not path.exists():
        return GateResult(False, ["requirements.json 不存在"])
    data = json.loads(path.read_text())
    if not data.get("confirmed"):
        return GateResult(False, ["用户尚未确认需求"])
    return GateResult(True)


def gate_outline(run_dir: Path) -> GateResult:
    """Gate 3→4: 大纲必须符合 Pyramid Principle"""
    path = run_dir / STAGE_ARTIFACTS[Stage.OUTLINE]
    if not path.exists():
        return GateResult(False, ["outline.json 不存在"])

    data = json.loads(path.read_text())
    errors = []

    # 检查顶层结论
    if not data.get("top_conclusion"):
        errors.append("缺少 top_conclusion（金字塔顶端结论）")

    # 检查支撑论点
    arguments = data.get("arguments", [])
    if len(arguments) < 2:
        errors.append(f"支撑论点不足（{len(arguments)} 个，至少需要 2 个）")

    # MECE 检查：每个论点必须有标题
    for i, arg in enumerate(arguments):
        if not arg.get("title"):
            errors.append(f"论点 {i+1} 缺少标题")
        if not arg.get("slides") and not arg.get("evidence"):
            errors.append(f"论点 {i+1} 缺少支撑页面或证据")

    # Check for density_targets
    if not data.get("density_targets"):
        print("  ⚠️ WARNING: 大纲缺少 density_targets（建议标注密度目标）")

    return GateResult(len(errors) == 0, errors)


def gate_style(run_dir: Path) -> GateResult:
    """Gate 4→5: 风格文件必须包含 3 色"""
    path = run_dir / STAGE_ARTIFACTS[Stage.STYLE_LOCK]
    if not path.exists():
        return GateResult(False, ["style.json 不存在"])
    data = json.loads(path.read_text())
    brand = data.get("brand", {})
    missing = [k for k in ["primary", "secondary", "accent"] if not brand.get(k)]
    if missing:
        return GateResult(False, [f"缺少品牌色: {missing}"])
    return GateResult(True)


def gate_generate(run_dir: Path) -> GateResult:
    """Gate 5→6: Planning JSON 必须通过 schema 校验"""
    path = run_dir / STAGE_ARTIFACTS[Stage.GENERATE]
    if not path.exists():
        return GateResult(False, ["plan.json 不存在"])
    errors = validate_plan(str(path))
    criticals = [e for e in errors if e.severity == "CRITICAL"]
    if criticals:
        return GateResult(False, [str(e) for e in criticals])
    return GateResult(True)


def gate_qa(run_dir: Path) -> GateResult:
    """Gate 6→7: QA 报告 0 CRITICAL"""
    path = run_dir / STAGE_ARTIFACTS[Stage.QA]
    if not path.exists():
        return GateResult(False, ["qa_report.json 不存在"])
    data = json.loads(path.read_text())
    if data.get("critical_count", 0) > 0:
        return GateResult(False, [f"QA 有 {data['critical_count']} 个 CRITICAL 问题"])
    return GateResult(True)


# Gate 映射：从哪个阶段到下一个阶段的校验
GATES = {
    Stage.INTERVIEW:  gate_interview,
    Stage.CONFIRM:    gate_confirm,
    Stage.OUTLINE:    gate_outline,
    Stage.STYLE_LOCK: gate_style,
    Stage.GENERATE:   gate_generate,
    Stage.QA:         gate_qa,
}


# ====================================================================
# 运行管理器
# ====================================================================

class RunManager:
    """
    管理单次 PPT 生成的运行状态。

    用法：
        run = RunManager.create("RAN TCO Analysis")
        run.save_artifact(Stage.INTERVIEW, {...})
        run.check_gate(Stage.INTERVIEW)  # → GateResult

        # 崩溃恢复：
        run = RunManager.resume("run_20260418_143000")
        print(run.current_stage)  # 自动推断当前阶段
    """

    RUNS_DIR = Path(__file__).parent.parent / "artifacts" / "runs"

    def __init__(self, run_id: str, run_dir: Path):
        self.run_id = run_id
        self.run_dir = run_dir

    @classmethod
    def create(cls, title: str = "") -> "RunManager":
        """创建新运行"""
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        run_dir = cls.RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # 写入运行元数据
        meta = {
            "run_id": run_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }
        (run_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))

        print(f"📁 新运行创建: {run_id}")
        return cls(run_id, run_dir)

    @classmethod
    def resume(cls, run_id: str) -> "RunManager":
        """恢复已有运行（扫描产物推断状态）"""
        run_dir = cls.RUNS_DIR / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"运行不存在: {run_id}")
        run = cls(run_id, run_dir)
        stage = run.current_stage
        print(f"🔄 恢复运行: {run_id} → 当前阶段: {stage.name}")
        return run

    @classmethod
    def list_runs(cls) -> List[str]:
        """列出所有运行"""
        if not cls.RUNS_DIR.exists():
            return []
        return sorted([d.name for d in cls.RUNS_DIR.iterdir() if d.is_dir()])

    @property
    def current_stage(self) -> Stage:
        """扫描产物文件，推断当前应执行的阶段"""
        for stage in reversed(Stage):
            artifact = STAGE_ARTIFACTS[stage]
            if (self.run_dir / artifact).exists():
                # 该阶段产物存在，说明下一阶段待执行
                next_stage = stage + 1
                if next_stage <= Stage.EXPORT:
                    return Stage(next_stage)
                return Stage.EXPORT  # 全部完成
        return Stage.INTERVIEW  # 无产物，从头开始

    @property
    def completed_stages(self) -> List[Stage]:
        """已完成的阶段列表"""
        completed = []
        for stage in Stage:
            artifact = STAGE_ARTIFACTS[stage]
            if (self.run_dir / artifact).exists():
                completed.append(stage)
        return completed

    def save_artifact(self, stage: Stage, data: dict):
        """保存阶段产物（JSON）"""
        artifact = STAGE_ARTIFACTS[stage]
        path = self.run_dir / artifact
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"  💾 {artifact} saved")

    def load_artifact(self, stage: Stage) -> Optional[dict]:
        """读取阶段产物"""
        artifact = STAGE_ARTIFACTS[stage]
        path = self.run_dir / artifact
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def check_gate(self, stage: Stage) -> GateResult:
        """检查某阶段的 Gate"""
        gate_fn = GATES.get(stage)
        if not gate_fn:
            return GateResult(True)  # 无 Gate 的阶段直接通过
        result = gate_fn(self.run_dir)
        icon = "✅" if result else "❌"
        print(f"  {icon} Gate {stage.name}: {result}")
        return result

    def status(self) -> str:
        """打印运行状态"""
        lines = [f"📋 Run: {self.run_id}"]
        for stage in Stage:
            artifact = STAGE_ARTIFACTS[stage]
            exists = (self.run_dir / artifact).exists()
            icon = "✅" if exists else "⬜"
            marker = " ← 当前" if stage == self.current_stage and not exists else ""
            lines.append(f"  {icon} {stage.name:12s}  {artifact}{marker}")
        return "\n".join(lines)


# ====================================================================
# CLI 入口
# ====================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python state_machine.py create [title]     — 创建新运行")
        print("  python state_machine.py resume <run_id>    — 恢复运行")
        print("  python state_machine.py list               — 列出所有运行")
        print("  python state_machine.py status <run_id>    — 查看状态")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "create":
        title = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        run = RunManager.create(title)
        print(run.status())

    elif cmd == "list":
        runs = RunManager.list_runs()
        if runs:
            for r in runs:
                print(f"  📁 {r}")
        else:
            print("  (无运行记录)")

    elif cmd == "resume":
        run = RunManager.resume(sys.argv[2])
        print(run.status())

    elif cmd == "status":
        run = RunManager.resume(sys.argv[2])
        print(run.status())

    else:
        print(f"未知命令: {cmd}")

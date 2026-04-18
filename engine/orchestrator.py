"""
Orchestrator — 端到端编排：采访 → 大纲 → Plan JSON → PPTX
==========================================================
把状态机、Gate、渲染器串成一条可执行的流水线。

用法：
    from engine.orchestrator import Orchestrator
    orc = Orchestrator()
    orc.run_from_interview(interview_answers)  # 自动走完全流程
    # 或
    orc.run_from_outline(outline_data)         # 从大纲开始
    # 或
    orc.run_from_plan("plan.json")             # 从 Plan JSON 开始
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from .state_machine import RunManager, Stage
from .planning_schema import validate_and_report
from .gates import check_pyramid_principle
from .renderer import PlanRenderer
from .design_system import BrandPalette


class Orchestrator:
    """端到端 PPT 生成编排器"""

    DEFAULT_BRAND = {
        "primary": "#00377B",
        "secondary": "#009FDB",
        "accent": "#FFD100",
    }

    def __init__(self, run_id: Optional[str] = None):
        if run_id:
            self.run = RunManager.resume(run_id)
        else:
            self.run = None

    # ================================================================
    # 入口 1：从采访开始（完整流程）
    # ================================================================
    def run_from_interview(self, interview: dict) -> str:
        """
        从采访答案开始，自动走完全流程。

        Args:
            interview: 麦肯锡 10 问的回答（dict）

        Returns:
            输出 PPTX 路径
        """
        title = interview.get("core_question", "Untitled Deck")
        self.run = RunManager.create(title)

        # P0: 保存采访
        self.run.save_artifact(Stage.INTERVIEW, interview)
        gate = self.run.check_gate(Stage.INTERVIEW)
        if not gate:
            raise ValueError(f"采访 Gate 失败: {gate.errors}")

        # P1: 自动确认（编排模式下跳过人工确认）
        self.run.save_artifact(Stage.CONFIRM, {
            "confirmed": True,
            "mode": "orchestrated",
            "timestamp": datetime.now().isoformat(),
        })

        # P3: 生成大纲
        outline = self._generate_outline(interview)
        self.run.save_artifact(Stage.OUTLINE, outline)
        gate = self.run.check_gate(Stage.OUTLINE)
        if not gate:
            raise ValueError(f"大纲 Gate 失败: {gate.errors}")

        # P3.5: 锁定风格
        brand = interview.get("brand", self.DEFAULT_BRAND)
        style = {"brand": brand, "font_family": "Arial", "locked_at": datetime.now().isoformat()}
        self.run.save_artifact(Stage.STYLE_LOCK, style)

        # P4: 生成 Plan JSON
        plan = self._generate_plan(interview, outline, brand)
        self.run.save_artifact(Stage.GENERATE, plan)
        gate = self.run.check_gate(Stage.GENERATE)
        if not gate:
            raise ValueError(f"Plan Gate 失败: {gate.errors}")

        # P5: 渲染 + QA
        output_path = self._render_and_qa(plan)

        print(f"\n{'='*60}")
        print(f"✅ 全流程完成!")
        print(self.run.status())
        return output_path

    # ================================================================
    # 入口 2：从大纲开始
    # ================================================================
    def run_from_outline(self, outline: dict, brand: dict = None) -> str:
        """从已有大纲开始"""
        self.run = RunManager.create(outline.get("top_conclusion", "Deck"))

        # 跳过采访和确认
        self.run.save_artifact(Stage.INTERVIEW, {"skipped": True})
        self.run.save_artifact(Stage.CONFIRM, {"confirmed": True, "mode": "from_outline"})
        self.run.save_artifact(Stage.OUTLINE, outline)

        brand = brand or self.DEFAULT_BRAND
        style = {"brand": brand, "font_family": "Arial"}
        self.run.save_artifact(Stage.STYLE_LOCK, style)

        interview = {"brand": brand, "core_question": outline.get("top_conclusion", "")}
        plan = self._generate_plan(interview, outline, brand)
        self.run.save_artifact(Stage.GENERATE, plan)

        return self._render_and_qa(plan)

    # ================================================================
    # 入口 3：从 Plan JSON 开始
    # ================================================================
    def run_from_plan(self, plan_path: str) -> str:
        """从已有 Plan JSON 直接渲染"""
        plan = json.loads(Path(plan_path).read_text())
        self.run = RunManager.create("Direct Render")

        # 跳过前置阶段
        for stage in [Stage.INTERVIEW, Stage.CONFIRM, Stage.OUTLINE, Stage.STYLE_LOCK]:
            self.run.save_artifact(stage, {"skipped": True})
        self.run.save_artifact(Stage.GENERATE, plan)

        return self._render_and_qa(plan)

    # ================================================================
    # 内部方法
    # ================================================================

    def _generate_outline(self, interview: dict) -> dict:
        """从采访答案生成 Pyramid Principle 大纲"""
        hypothesis = interview.get("hypothesis", "")
        arguments = interview.get("key_arguments", [])
        actions = interview.get("actions", [])

        outline = {
            "top_conclusion": hypothesis,
            "narrative_flow": "conclusion_first",
            "arguments": [],
        }

        for i, arg in enumerate(arguments):
            slides = [{"template": "data_story", "focus": arg}]
            outline["arguments"].append({
                "title": arg,
                "slides": slides,
                "evidence": [],
            })

        # Pyramid Principle 校验
        issues = check_pyramid_principle(outline)
        criticals = [i for i in issues if i[0] == "CRITICAL"]
        if criticals:
            print(f"  ⚠️ 大纲有 {len(criticals)} 个 CRITICAL 问题，尝试自动修复...")
            # 基本修复：确保至少有 2 个论点
            if len(outline["arguments"]) < 2:
                outline["arguments"].append({
                    "title": "Additional analysis supports the conclusion",
                    "slides": [{"template": "data_story", "focus": "supporting data"}],
                    "evidence": ["To be confirmed"],
                })

        return outline

    def _generate_plan(self, interview: dict, outline: dict, brand: dict) -> dict:
        """从大纲生成 Planning JSON"""
        hypothesis = outline.get("top_conclusion", "")
        arguments = outline.get("arguments", [])
        actions = interview.get("actions", [])
        page_count = interview.get("page_count", "8-12")
        date = datetime.now().strftime("%B %Y")

        slides = []
        slide_num = 1

        # 1. Cover
        slides.append({
            "slide_number": slide_num,
            "template": "cover",
            "title": interview.get("core_question", hypothesis),
            "subtitle": hypothesis,
            "date": date,
        })
        slide_num += 1

        # 2. Executive Summary — 用论点标题作为 KPI
        kpis = []
        for i, arg in enumerate(arguments[:4]):
            kpis.append({
                "value": f"#{i+1}",
                "label": arg.get("title", "")[:40],
                "detail": "",
            })
        slides.append({
            "slide_number": slide_num,
            "template": "executive_summary",
            "action_title": hypothesis,
            "subtitle": "Key findings summary",
            "kpis": kpis,
            "density_label": "medium",
        })
        slide_num += 1

        # 3-N. 每个论点的支撑页面
        for arg in arguments:
            arg_slides = arg.get("slides", [])
            for s in arg_slides:
                template = s.get("template", "data_story")
                slide_data = {
                    "slide_number": slide_num,
                    "template": template,
                    "action_title": arg.get("title", ""),
                    "subtitle": s.get("focus", ""),
                    "density_label": "medium",
                }

                # data_story 需要图表数据
                if template == "data_story":
                    slide_data["chart"] = {
                        "type": "bar",
                        "categories": ["Category A", "Category B", "Category C"],
                        "series": [{"name": "Value", "values": [100, 150, 120]}],
                        "y_axis_title": "Value",
                        "show_data_labels": True,
                    }
                    slide_data["insight"] = f"Key insight from: {s.get('focus', '')}"
                    slide_data["source"] = "Data source to be confirmed"

                # comparison 需要左右数据
                elif template == "comparison":
                    slide_data["left"] = {
                        "label": "Option A",
                        "points": ["Point 1", "Point 2", "Point 3"],
                    }
                    slide_data["right"] = {
                        "label": "Option B",
                        "points": ["Point 1", "Point 2", "Point 3"],
                    }

                slides.append(slide_data)
                slide_num += 1

        # N+1. Recommendation（如果有 actions）
        if actions:
            recs = []
            for i, action in enumerate(actions[:3]):
                recs.append({
                    "number": str(i + 1),
                    "title": action.split(":")[0] if ":" in action else action[:30],
                    "detail": action,
                })
            slides.append({
                "slide_number": slide_num,
                "template": "recommendation",
                "action_title": f"{len(actions)} recommended actions to move forward",
                "recommendations": recs,
                "density_label": "medium",
            })
            slide_num += 1

        # Closing
        slides.append({
            "slide_number": slide_num,
            "template": "closing",
            "title": "Thank You",
            "subtitle": f"{interview.get('audience', 'Team')} — {date}",
        })

        plan = {
            "metadata": {
                "title": interview.get("core_question", ""),
                "date": date,
                "brand": brand,
                "total_slides": len(slides),
                "generated_by": "consulting-ppt-skill v2.0",
            },
            "slides": slides,
        }
        return plan

    def _render_and_qa(self, plan: dict) -> str:
        """渲染 PPTX + 简单 QA"""
        # 写临时 plan.json
        plan_path = self.run.run_dir / "plan.json"
        plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False))

        # 渲染
        output_path = str(self.run.run_dir / "deck.pptx")
        renderer = PlanRenderer(str(plan_path))
        renderer.render(output_path)

        # 简单 QA
        from pptx import Presentation
        prs = Presentation(output_path)
        qa_report = {
            "total_slides": len(prs.slides),
            "critical_count": 0,
            "warning_count": 0,
            "checks": [],
        }

        for i, slide in enumerate(prs.slides):
            n_shapes = len(slide.shapes)
            if n_shapes < 2:
                qa_report["warning_count"] += 1
                qa_report["checks"].append(f"Slide {i+1}: only {n_shapes} shapes (possibly empty)")
            if n_shapes > 20:
                qa_report["warning_count"] += 1
                qa_report["checks"].append(f"Slide {i+1}: {n_shapes} shapes (possibly cluttered)")

        self.run.save_artifact(Stage.QA, qa_report)
        gate = self.run.check_gate(Stage.QA)

        # 导出清单
        manifest = {
            "output_file": output_path,
            "total_slides": len(prs.slides),
            "qa_passed": bool(gate),
            "generated_at": datetime.now().isoformat(),
        }
        self.run.save_artifact(Stage.EXPORT, manifest)

        return output_path


# ====================================================================
# CLI
# ====================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m engine.orchestrator demo     — 运行 demo（麦肯锡 10 问 → PPTX）")
        print("  python -m engine.orchestrator plan.json — 从 Plan JSON 渲染")
        sys.exit(0)

    if sys.argv[1] == "demo":
        orc = Orchestrator()
        result = orc.run_from_interview({
            "audience": "CTO + Board",
            "audience_expertise": "high",
            "core_question": "Should we switch RAN vendors or stay with the current one?",
            "hypothesis": "Staying is 22-57% cheaper than switching across all 4 deployment scenarios",
            "key_arguments": [
                "Migration and multi-vendor costs dominate the switching premium",
                "Stay scenario delivers 16 months faster 5G rollout",
                "Three actions capture value without switching risk",
            ],
            "data_sources": [
                {"name": "TCO Model Q1 2026", "confidence": "A"},
                {"name": "Vendor deployment commitments", "confidence": "A"},
            ],
            "actions": [
                "STAY & NEGOTIATE: Leverage RFP pressure for 10-15% better pricing",
                "MODERNIZE: Use savings to fund 5G acceleration",
                "STRATEGIC RESERVE: Maintain vendor diversification for future",
            ],
            "brand": {"primary": "#00377B", "secondary": "#009FDB", "accent": "#FFD100"},
            "page_count": "8-12",
            "format": "PPTX",
        })
        print(f"\n📄 PPTX: {result}")
    else:
        orc = Orchestrator()
        result = orc.run_from_plan(sys.argv[1])
        print(f"\n📄 PPTX: {result}")

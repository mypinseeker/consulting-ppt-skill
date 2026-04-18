"""
Outline Agent — Generates Pyramid Principle outline from interview data.
Separated from orchestrator to enforce "main agent doesn't write artifacts" principle.
"""
import json
from typing import List, Dict, Any
from .gates import check_pyramid_principle


def generate_outline(interview: dict) -> dict:
    """
    Generate a Pyramid Principle outline from interview answers.

    Args:
        interview: McKinsey 10-Q answers (dict)

    Returns:
        Pyramid Principle outline with arguments and density targets
    """
    hypothesis = interview.get("hypothesis", "")
    arguments = interview.get("key_arguments", [])

    outline = {
        "top_conclusion": hypothesis,
        "narrative_flow": "conclusion_first",
        "arguments": [],
    }

    # Process arguments (support both string and dict formats)
    for arg in arguments:
        if isinstance(arg, dict):
            outline["arguments"].append(arg)
        else:
            slides = [{"template": "data_story", "focus": arg}]
            outline["arguments"].append({
                "title": arg,
                "slides": slides,
                "evidence": [],
            })

    # Pyramid Principle validation + auto-fix
    issues = check_pyramid_principle(outline)
    criticals = [i for i in issues if i[0] == "CRITICAL"]
    if criticals:
        print(f"  ⚠️ 大纲有 {len(criticals)} 个 CRITICAL 问题，尝试自动修复...")
        # Basic fix: ensure at least 2 arguments
        if len(outline["arguments"]) < 2:
            outline["arguments"].append({
                "title": "Additional analysis supports the conclusion",
                "slides": [{"template": "data_story", "focus": "supporting data"}],
                "evidence": ["To be confirmed"],
            })

    # Density targets based on interview preference
    density_bias = interview.get("density_bias", "balanced")
    density_map = {"relaxed": "medium", "balanced": "high", "ultra_dense": "high"}
    content_density = density_map.get(density_bias, "high")

    outline["density_bias"] = density_bias
    outline["density_targets"] = {
        "cover": "low",
        "section_divider": "low",
        "closing": "low",
        "executive_summary": "medium",
        "recommendation": "medium",
        "data_story": content_density,
        "comparison": content_density,
        "framework": content_density,
        "table": content_density,
        "appendix": content_density,
    }

    return outline

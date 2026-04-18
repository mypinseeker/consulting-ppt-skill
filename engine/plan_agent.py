"""
Plan Agent — Generates Planning JSON from outline + interview data.
Separated from orchestrator to enforce "main agent doesn't write artifacts" principle.
"""
import re
import json
from datetime import datetime
from typing import Dict, List, Any


def generate_plan(interview: dict, outline: dict, brand: dict) -> dict:
    """
    Generate Planning JSON from outline and interview data.

    Args:
        interview: McKinsey 10-Q answers
        outline: Pyramid Principle outline
        brand: Brand color palette (primary, secondary, accent)

    Returns:
        Planning JSON with slides array and metadata
    """
    hypothesis = outline.get("top_conclusion", "")
    arguments = outline.get("arguments", [])
    actions = interview.get("actions", [])
    page_count = interview.get("page_count", "8-12")
    date = datetime.now().strftime("%B %Y")

    slides = []
    slide_num = 1

    # 1. Cover — title+subtitle total ≤35 CJK chars
    cover_title = interview.get("core_question", hypothesis)
    cover_subtitle = hypothesis
    # If subtitle too long, truncate
    cn_total = sum(1 for c in (cover_title + cover_subtitle) if ord(c) > 127)
    if cn_total > 35:
        # Title takes priority, subtitle truncated
        max_sub = max(10, 35 - sum(1 for c in cover_title if ord(c) > 127))
        cover_subtitle = cover_subtitle[:max_sub] + "…"
    slides.append({
        "slide_number": slide_num,
        "template": "cover",
        "title": cover_title,
        "subtitle": cover_subtitle,
        "date": date,
    })
    slide_num += 1

    # 2. Executive Summary — use kpi_data from interview or extract from arguments
    kpis = []
    kpi_data = interview.get("kpi_data", [])
    if kpi_data:
        # User provided structured KPI data — enforce length limits
        for kpi in kpi_data[:4]:
            label = kpi.get("label", "")
            detail = kpi.get("detail", "")
            # KPI box 2.7"×1.4", 36pt value + 10pt label, CJK total ≤12 chars
            cn = sum(1 for c in (label + detail) if ord(c) > 127)
            if cn > 0 and len(label + detail) > 12:
                label = label[:8]
                detail = detail[:4] if detail else ""
            kpis.append({
                "value": kpi.get("value", ""),
                "label": label,
                "detail": detail,
            })
    else:
        # Auto-extract numbers from argument titles (best effort)
        for i, arg in enumerate(arguments[:4]):
            title = arg.get("title", "")
            # Try to extract first number+unit in title as KPI value
            num_match = re.search(r'(\d+[\.,]?\d*\s*[%$€¥M万亿]+|\$?\d+[\.,]?\d*[MBK]?\b)', title)
            if num_match:
                kpis.append({
                    "value": num_match.group(0),
                    "label": title[:40],
                    "detail": "",
                })
            else:
                kpis.append({
                    "value": f"Point {i+1}",
                    "label": title[:40],
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

    # 3-N. Supporting slides for each argument
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

            # data_story — prefer user-provided chart_data
            if template == "data_story":
                chart_data = s.get("chart_data")
                if chart_data:
                    slide_data["chart"] = chart_data
                else:
                    # No data: mark as placeholder (Gate will flag)
                    slide_data["chart"] = {
                        "type": "bar",
                        "categories": ["[需要填充真实数据]"],
                        "series": [{"name": "Data", "values": [0]}],
                        "y_axis_title": "[单位]",
                    }
                slide_data["insight"] = s.get("insight", f"[需要填充: {s.get('focus', '')} 的关键洞察]")
                # source from evidence
                evidence = arg.get("evidence", [])
                slide_data["source"] = ", ".join(evidence) if evidence else "[需要填充数据来源]"

            # comparison — prefer user-provided comparison_data
            elif template == "comparison":
                comp_data = s.get("comparison_data", {})
                slide_data["left"] = comp_data.get("left", {
                    "label": "[选项 A]",
                    "points": ["[需要填充对比点]"],
                })
                slide_data["right"] = comp_data.get("right", {
                    "label": "[选项 B]",
                    "points": ["[需要填充对比点]"],
                })

            slides.append(slide_data)
            slide_num += 1

    # N+1. Recommendation (if actions provided)
    if actions:
        recs = []
        for i, action in enumerate(actions[:5]):  # Support max 5 actions
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
            "generated_by": "consulting-ppt-skill v3.0",
        },
        "slides": slides,
    }
    return plan

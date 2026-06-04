"""Reviewer Agent 的 prompt 模板 — REVIEW 阶段审核下游产物。"""

from __future__ import annotations

import json
from typing import Any


def build_review_user_message(
    storyboard: dict[str, Any] | None = None,
    narration: dict[str, Any] | None = None,
    research_summary: dict[str, Any] | None = None,
    formula_catalog: dict[str, Any] | None = None,
    worker_outputs: dict[str, Any] | None = None,
) -> str:
    parts: list[str] = [
        "你是一个数学科普项目的审核 Agent。请基于原材料和分镜表，审核下游 Worker 产出的动画片段。",
        "审核标准：数学正确性、叙事一致性、渲染可执行性。",
        "审核结论只能是 pass（通过）或 block（阻塞），阻塞必须给出具体修改建议。",
    ]

    if storyboard:
        parts.extend([
            "",
            "## 分镜主表",
            json.dumps(default=str, obj=storyboard, ensure_ascii=False, indent=2),
        ])

    if narration:
        parts.extend([
            "",
            "## 讲解脚本",
            json.dumps(default=str, obj=narration, ensure_ascii=False, indent=2),
        ])

    if research_summary:
        parts.extend([
            "",
            "## 研究总结",
            json.dumps(default=str, obj=research_summary, ensure_ascii=False, indent=2),
        ])

    if formula_catalog:
        parts.extend([
            "",
            "## 公式目录",
            json.dumps(default=str, obj=formula_catalog, ensure_ascii=False, indent=2),
        ])

    if worker_outputs:
        parts.extend([
            "",
            "## Worker 产出",
            json.dumps(default=str, obj=worker_outputs, ensure_ascii=False, indent=2),
        ])

    parts.extend([
        "",
        "## 任务",
        "1. 逐镜头检查数学公式是否正确（符号、推导步骤）",
        "2. 验证动画内容是否与讲解词一致",
        "3. 检查每个镜头的渲染代码是否可执行（语法正确、依赖满足）",
        "4. 对每个镜头给出 pass/block 结论",
        "5. 对 block 的镜头，列出具体问题与修改建议",
        "6. 给出整体审核结论和下一步建议",
    ])
    return "\n".join(parts)


# REVIEW 阶段的输出 Schema
REVIEW_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "overall_verdict": {
            "type": "string",
            "enum": ["pass", "block"],
            "description": "整体审核结论",
        },
        "segment_reviews": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "segment_id": {"type": "string"},
                    "verdict": {
                        "type": "string",
                        "enum": ["pass", "block"],
                    },
                    "math_correctness": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["pass", "block"]},
                            "issues": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["status", "issues"],
                        "additionalProperties": False,
                    },
                    "narrative_consistency": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["pass", "block"]},
                            "issues": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["status", "issues"],
                        "additionalProperties": False,
                    },
                    "render_feasibility": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["pass", "block"]},
                            "issues": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["status", "issues"],
                        "additionalProperties": False,
                    },
                    "blocking_issues": {"type": "array", "items": {"type": "string"}},
                    "fix_suggestions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["segment_id", "verdict", "math_correctness", "narrative_consistency", "render_feasibility"],
                "additionalProperties": False,
            },
        },
        "summary": {"type": "string"},
        "next_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["overall_verdict", "segment_reviews", "summary"],
    "additionalProperties": False,
}

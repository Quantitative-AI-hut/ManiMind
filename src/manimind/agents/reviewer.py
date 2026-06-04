"""Reviewer Agent — 审核下游 Worker 产物，硬关卡。"""

from __future__ import annotations

from typing import Any

from ..llm.templates.reviewer import REVIEW_OUTPUT_SCHEMA, build_review_user_message
from ..models import ContextScope, PipelineStage
from .base import BaseAgent


class ReviewerAgent(BaseAgent):
    """审核 Agent — VERIFY_ONLY 模式，只读不写。

    REVIEW 阶段:
        - 读取 storyboard + narration + research + formula + worker outputs
        - 逐镜头审核数学正确性、叙事一致性、渲染可执行性
        - 输出: review.report → 长期上下文
    """

    role_id = "reviewer"

    def run(self, stage: PipelineStage, task_id: str, **kwargs: Any) -> dict[str, Any]:
        if stage != PipelineStage.REVIEW:
            return {
                "success": False,
                "task_id": task_id,
                "error": f"Reviewer only supports REVIEW stage, got {stage.value}",
            }
        return self._run_review(task_id, **kwargs)

    def _run_review(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        pid = self.plan.project_id
        storyboard = kwargs.get("storyboard") or self._read_context(f"{pid}.storyboard.master")
        narration = kwargs.get("narration") or self._read_context(f"{pid}.narration.script")
        research = kwargs.get("research_summary") or self._read_context(f"{pid}.research.summary")
        formula = kwargs.get("formula_catalog") or self._read_context(f"{pid}.formula.catalog")
        worker_outputs = kwargs.get("worker_outputs") or self._collect_worker_outputs(pid)

        user_message = build_review_user_message(
            storyboard=storyboard,
            narration=narration,
            research_summary=research,
            formula_catalog=formula,
            worker_outputs=worker_outputs,
        )
        system_prompt = self._build_system_prompt_text(PipelineStage.REVIEW)

        try:
            llm = self._require_llm()
            result = llm.chat_structured(system_prompt, user_message, REVIEW_OUTPUT_SCHEMA)
        except RuntimeError:
            return {"success": False, "task_id": task_id, "error": "llm_unavailable"}

        validation_errors = _validate_output(result)
        if validation_errors:
            return {
                "success": False,
                "task_id": task_id,
                "error": "validation_failed",
                "validation_errors": validation_errors,
            }

        key = f"{pid}.review.report"
        self._write_context(key, result, ContextScope.LONG_TERM)

        return {
            "success": True,
            "task_id": task_id,
            "outputs": [key],
            "verdict": result["overall_verdict"],
            "pass_count": sum(1 for s in result["segment_reviews"] if s["verdict"] == "pass"),
            "block_count": sum(1 for s in result["segment_reviews"] if s["verdict"] == "block"),
        }

    def _collect_worker_outputs(self, pid: str) -> dict[str, Any]:
        outputs: dict[str, list] = {"html": [], "manim": [], "svg": []}
        for segment in self.plan.segments:
            sid = segment.id
            html_key = f"{pid}.html.{sid}.approved"
            manim_key = f"{pid}.manim.{sid}.approved"
            svg_key = f"{pid}.svg.{sid}.approved"
            for key in (html_key, manim_key, svg_key):
                content = self._read_context(key)
                if content:
                    if "html" in key:
                        outputs["html"].append({"segment_id": sid, "content": content})
                    elif "manim" in key:
                        outputs["manim"].append({"segment_id": sid, "content": content})
                    elif "svg" in key:
                        outputs["svg"].append({"segment_id": sid, "content": content})
        return outputs

    def _build_system_prompt_text(self, stage: PipelineStage) -> str:
        return "\n".join(self.build_system_prompt(stage))


def _validate_output(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    verdict = result.get("overall_verdict")
    if verdict not in ("pass", "block"):
        errors.append("overall_verdict must be pass or block")
    reviews = result.get("segment_reviews")
    if not isinstance(reviews, list) or len(reviews) == 0:
        errors.append("segment_reviews must be a non-empty array")
    return errors

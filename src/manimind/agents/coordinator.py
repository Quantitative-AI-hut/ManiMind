"""Coordinator Agent — 生成讲解脚本、分镜和任务分发。"""

from __future__ import annotations

from typing import Any

from ..llm.templates.coordinator import (
    DISPATCH_OUTPUT_SCHEMA,
    PLAN_OUTPUT_SCHEMA,
    build_dispatch_user_message,
    build_plan_user_message,
)
from ..models import ContextScope, PipelineStage
from .base import BaseAgent


class CoordinatorAgent(BaseAgent):
    """协调 Agent — 第一个有写入权的 Agent。

    PLAN 阶段:
        - 读取 Explorer 研究总结 + Planner 建议
        - 生成 narration.script + storyboard.master
        - 写入长期上下文

    DISPATCH 阶段:
        - 读取 storyboard.master
        - 生成任务分派 + session.handoff
        - 写入长期上下文
    """

    role_id = "coordinator"

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def run(self, stage: PipelineStage, task_id: str, **kwargs: Any) -> dict[str, Any]:
        if stage == PipelineStage.PLAN:
            return self._run_plan(task_id)
        if stage == PipelineStage.DISPATCH:
            return self._run_dispatch(task_id)
        return {
            "success": False,
            "task_id": task_id,
            "error": f"Coordinator does not support stage: {stage.value}",
        }

    # ------------------------------------------------------------------
    # PLAN 阶段
    # ------------------------------------------------------------------

    def _run_plan(self, task_id: str) -> dict[str, Any]:
        pid = self.plan.project_id

        # 收集上游数据
        research_summary = self._read_context(f"{pid}.research.summary")
        planner_constraints = self._read_context("planner.constraint.analysis")
        planner_storyboard = self._read_context("planner.storyboard.suggestions")

        planner_suggestions = None
        if planner_constraints or planner_storyboard:
            planner_suggestions = {}
            if planner_constraints:
                planner_suggestions["constraint_analysis"] = planner_constraints
            if planner_storyboard:
                planner_suggestions["storyboard_suggestions"] = planner_storyboard

        segments = [s.to_dict() for s in self.plan.segments]

        # 构建 prompt
        user_message = build_plan_user_message(
            segments=segments,
            research_summary=research_summary,
            planner_suggestions=planner_suggestions,
        )
        system_prompt = self._build_system_prompt_text(PipelineStage.PLAN)

        # 调用 LLM
        try:
            llm = self._require_llm()
            result = llm.chat_structured(system_prompt, user_message, PLAN_OUTPUT_SCHEMA)
        except RuntimeError:
            return {
                "success": False,
                "task_id": task_id,
                "error": "llm_unavailable",
            }

        # 校验关键字段
        validation_errors = _validate_plan_output(result)
        if validation_errors:
            return {
                "success": False,
                "task_id": task_id,
                "error": "validation_failed",
                "validation_errors": validation_errors,
            }

        # 写入长期上下文
        narration_key = f"{pid}.narration.script"
        storyboard_key = f"{pid}.storyboard.master"

        self._write_context(narration_key, result["narration_script"], ContextScope.LONG_TERM)
        self._write_context(storyboard_key, result["storyboard_master"], ContextScope.LONG_TERM)

        return {
            "success": True,
            "task_id": task_id,
            "outputs": [narration_key, storyboard_key],
            "segment_count": len(result["narration_script"].get("segments", [])),
            "total_duration_seconds": (
                result["narration_script"]
                .get("voiceover_notes", {})
                .get("total_estimated_duration_seconds", 0)
            ),
        }

    # ------------------------------------------------------------------
    # DISPATCH 阶段
    # ------------------------------------------------------------------

    def _run_dispatch(self, task_id: str) -> dict[str, Any]:
        pid = self.plan.project_id

        # 读取分镜主表
        storyboard = self._read_context(f"{pid}.storyboard.master")
        segments = [s.to_dict() for s in self.plan.segments]

        user_message = build_dispatch_user_message(
            storyboard=storyboard,
            segments=segments,
        )
        system_prompt = self._build_system_prompt_text(PipelineStage.DISPATCH)

        try:
            llm = self._require_llm()
            result = llm.chat_structured(system_prompt, user_message, DISPATCH_OUTPUT_SCHEMA)
        except RuntimeError:
            return {
                "success": False,
                "task_id": task_id,
                "error": "llm_unavailable",
            }

        validation_errors = _validate_dispatch_output(result)
        if validation_errors:
            return {
                "success": False,
                "task_id": task_id,
                "error": "validation_failed",
                "validation_errors": validation_errors,
            }

        # 写入会话交接（短期上下文）
        handoff_key = f"{pid}.session.handoff"
        self._write_context(
            handoff_key,
            result["session_handoff"],
            ContextScope.SHORT_TERM,
        )

        return {
            "success": True,
            "task_id": task_id,
            "outputs": [handoff_key],
            "task_assignments": result["task_assignments"],
            "assigned_count": len(result.get("task_assignments", [])),
        }

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    def _build_system_prompt_text(self, stage: PipelineStage) -> str:
        parts = self.build_system_prompt(stage)
        return "\n".join(parts)


# -----------------------------------------------------------------------
# 输出校验
# -----------------------------------------------------------------------

def _validate_plan_output(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    narration = result.get("narration_script")
    storyboard = result.get("storyboard_master")

    if not isinstance(narration, dict):
        errors.append("narration_script must be an object")
    elif not narration.get("segments"):
        errors.append("narration_script.segments is empty")

    if not isinstance(storyboard, dict):
        errors.append("storyboard_master must be an object")
    elif not storyboard.get("segments"):
        errors.append("storyboard_master.segments is empty")

    # 一致性校验：narration 和 storyboard 的 segment_ids 应一致
    if isinstance(narration, dict) and isinstance(storyboard, dict):
        n_ids = {s.get("segment_id") for s in narration.get("segments", [])}
        s_ids = {s.get("segment_id") for s in storyboard.get("segments", [])}
        if n_ids != s_ids:
            missing_in_narration = s_ids - n_ids
            missing_in_storyboard = n_ids - s_ids
            if missing_in_narration:
                errors.append(f"segments missing from narration_script: {sorted(missing_in_narration)}")
            if missing_in_storyboard:
                errors.append(f"segments missing from storyboard_master: {sorted(missing_in_storyboard)}")

    return errors


def _validate_dispatch_output(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    assignments = result.get("task_assignments")
    handoff = result.get("session_handoff")

    if not isinstance(assignments, list) or len(assignments) == 0:
        errors.append("task_assignments must be a non-empty array")

    if not isinstance(handoff, dict):
        errors.append("session_handoff must be an object")

    return errors

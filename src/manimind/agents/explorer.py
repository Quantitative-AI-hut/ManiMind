"""Explorer Agent — 资料探索、论文分析、研究总结生成。"""

from __future__ import annotations

from typing import Any

from ..llm.templates.explorer import (
    INGEST_OUTPUT_SCHEMA,
    PLAN_OUTPUT_SCHEMA,
    PRESTART_OUTPUT_SCHEMA,
    SUMMARIZE_OUTPUT_SCHEMA,
    build_ingest_user_message,
    build_plan_user_message,
    build_prestart_user_message,
    build_summarize_user_message,
)
from ..models import ContextScope, PipelineStage
from .base import BaseAgent


class ExplorerAgent(BaseAgent):
    """资料探索 Agent — 只读角色。

    负责四个阶段的工作:

    PRESTART:
        - 检查环境就绪状态
        - 输出: env-readiness 建议稿 → 短期上下文

    INGEST:
        - 分析论文、笔记、资产
        - 输出: 初步分析发现 → 短期上下文

    SUMMARIZE:
        - 生成研究总结、术语表、公式目录
        - 输出: 三份结构化草案 → 短期上下文

    PLAN:
        - 为镜头匹配参考资源
        - 输出: 参考匹配建议 → 短期上下文
    """

    role_id = "explorer"

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def run(self, stage: PipelineStage, task_id: str, **kwargs: Any) -> dict[str, Any]:
        if stage == PipelineStage.PRESTART:
            return self._run_prestart(task_id, **kwargs)
        if stage == PipelineStage.INGEST:
            return self._run_ingest(task_id, **kwargs)
        if stage == PipelineStage.SUMMARIZE:
            return self._run_summarize(task_id, **kwargs)
        if stage == PipelineStage.PLAN:
            return self._run_plan(task_id, **kwargs)
        return {
            "success": False,
            "task_id": task_id,
            "error": f"Explorer does not support stage: {stage.value}",
        }

    # ------------------------------------------------------------------
    # PRESTART — 环境就绪检查
    # ------------------------------------------------------------------

    def _run_prestart(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        pid = self.plan.project_id

        env_report = kwargs.get("env_report")
        user_message = build_prestart_user_message(env_report)
        system_prompt = self._build_system_prompt_text(PipelineStage.PRESTART)

        try:
            llm = self._require_llm()
            result = llm.chat_structured(system_prompt, user_message, PRESTART_OUTPUT_SCHEMA)
        except RuntimeError:
            return {"success": False, "task_id": task_id, "error": "llm_unavailable"}

        key = f"{pid}.env.readiness"
        self._write_context(key, result, ContextScope.SHORT_TERM)

        return {
            "success": True,
            "task_id": task_id,
            "outputs": [key],
            "overall_status": result.get("overall_status", "unknown"),
        }

    # ------------------------------------------------------------------
    # INGEST — 材料初步分析
    # ------------------------------------------------------------------

    def _run_ingest(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        pid = self.plan.project_id

        paper_text = kwargs.get("paper_text")
        notes = kwargs.get("notes")
        assets = kwargs.get("assets")

        user_message = build_ingest_user_message(
            paper_text=paper_text,
            notes=notes,
            assets=assets,
        )
        system_prompt = self._build_system_prompt_text(PipelineStage.INGEST)

        try:
            llm = self._require_llm()
            result = llm.chat_structured(system_prompt, user_message, INGEST_OUTPUT_SCHEMA)
        except RuntimeError:
            return {"success": False, "task_id": task_id, "error": "llm_unavailable"}

        key = f"{pid}.ingest.findings"
        self._write_context(key, result, ContextScope.SHORT_TERM)

        return {
            "success": True,
            "task_id": task_id,
            "outputs": [key],
            "domain": result.get("domain", ""),
            "difficulty_level": result.get("difficulty_level", ""),
            "concepts_found": len(result.get("identified_concepts", [])),
        }

    # ------------------------------------------------------------------
    # SUMMARIZE — 生成研究总结、术语表、公式目录
    # ------------------------------------------------------------------

    def _run_summarize(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        pid = self.plan.project_id

        paper_text = kwargs.get("paper_text")
        notes = kwargs.get("notes")
        ingest_findings = kwargs.get("ingest_findings") or self._read_context(
            f"{pid}.ingest.findings"
        )

        user_message = build_summarize_user_message(
            paper_text=paper_text,
            notes=notes,
            ingest_findings=ingest_findings,
        )
        system_prompt = self._build_system_prompt_text(PipelineStage.SUMMARIZE)

        try:
            llm = self._require_llm()
            result = llm.chat_structured(system_prompt, user_message, SUMMARIZE_OUTPUT_SCHEMA)
        except RuntimeError:
            return {"success": False, "task_id": task_id, "error": "llm_unavailable"}

        validation_errors = _validate_summarize_output(result)
        if validation_errors:
            return {
                "success": False,
                "task_id": task_id,
                "error": "validation_failed",
                "validation_errors": validation_errors,
            }

        # 三份产出写入短期上下文（Explorer 是 read_only，只能写短期）
        research_key = f"{pid}.research.summary"
        glossary_key = f"{pid}.glossary"
        formula_key = f"{pid}.formula.catalog"

        self._write_context(research_key, result["research_summary"], ContextScope.SHORT_TERM)
        self._write_context(glossary_key, result["glossary"], ContextScope.SHORT_TERM)
        self._write_context(formula_key, result["formula_catalog"], ContextScope.SHORT_TERM)

        return {
            "success": True,
            "task_id": task_id,
            "outputs": [research_key, glossary_key, formula_key],
            "concepts_count": len(result["research_summary"].get("core_concepts", [])),
            "terms_count": len(result["glossary"].get("terms", [])),
            "formulas_count": len(result["formula_catalog"].get("formulas", [])),
        }

    # ------------------------------------------------------------------
    # PLAN — 为镜头匹配参考资源
    # ------------------------------------------------------------------

    def _run_plan(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        pid = self.plan.project_id

        segments = [s.to_dict() for s in self.plan.segments]
        research_summary = kwargs.get("research_summary") or self._read_context(
            f"{pid}.research.summary"
        )
        glossary = kwargs.get("glossary") or self._read_context(f"{pid}.glossary")
        formula_catalog = kwargs.get("formula_catalog") or self._read_context(
            f"{pid}.formula.catalog"
        )
        assets = kwargs.get("assets")

        user_message = build_plan_user_message(
            segments=segments,
            research_summary=research_summary,
            glossary=glossary,
            formula_catalog=formula_catalog,
            assets=assets,
        )
        system_prompt = self._build_system_prompt_text(PipelineStage.PLAN)

        try:
            llm = self._require_llm()
            result = llm.chat_structured(system_prompt, user_message, PLAN_OUTPUT_SCHEMA)
        except RuntimeError:
            return {"success": False, "task_id": task_id, "error": "llm_unavailable"}

        validation_errors = _validate_plan_output(result)
        if validation_errors:
            return {
                "success": False,
                "task_id": task_id,
                "error": "validation_failed",
                "validation_errors": validation_errors,
            }

        key = f"{pid}.explorer.references"
        self._write_context(key, result, ContextScope.SHORT_TERM)

        return {
            "success": True,
            "task_id": task_id,
            "outputs": [key],
            "segments_matched": len(result.get("segment_references", [])),
        }

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    def _build_system_prompt_text(self, stage: PipelineStage) -> str:
        parts = self.build_system_prompt(stage)
        return "\n".join(parts)


# ============================================================================
# 输出校验
# ============================================================================


def _validate_summarize_output(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    research = result.get("research_summary")
    glossary = result.get("glossary")
    formula_catalog = result.get("formula_catalog")

    if not isinstance(research, dict):
        errors.append("research_summary must be an object")
    else:
        if not research.get("core_concepts"):
            errors.append("research_summary.core_concepts is empty")
        if not research.get("key_findings"):
            errors.append("research_summary.key_findings is empty")

    if not isinstance(glossary, dict):
        errors.append("glossary must be an object")
    elif not glossary.get("terms"):
        errors.append("glossary.terms is empty")

    if not isinstance(formula_catalog, dict):
        errors.append("formula_catalog must be an object")
    elif not formula_catalog.get("formulas"):
        errors.append("formula_catalog.formulas is empty")

    return errors


def _validate_plan_output(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    references = result.get("segment_references")
    if not isinstance(references, list) or len(references) == 0:
        errors.append("segment_references must be a non-empty array")
    else:
        for i, ref in enumerate(references):
            if not isinstance(ref, dict):
                errors.append(f"segment_references[{i}] must be an object")
            elif not ref.get("segment_id"):
                errors.append(f"segment_references[{i}] missing segment_id")

    return errors

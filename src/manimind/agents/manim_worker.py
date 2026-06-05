"""Manim Worker Agent — 生成 Manim 数学动画代码。"""

from __future__ import annotations

from typing import Any

from ..llm.templates.manim_worker import DISPATCH_OUTPUT_SCHEMA, build_dispatch_user_message
from ..models import ContextScope, PipelineStage
from .base import BaseAgent


class ManimWorkerAgent(BaseAgent):
    """Manim Worker — 逐镜头生成 Manim 动画代码。

    DISPATCH 阶段:
        - 读取 storyboard.master + narration.script + formula.catalog
        - 为每个 Manim/hybrid 镜头单独调用 LLM 生成 Scene 代码
        - 写入长期上下文
    """

    role_id = "manim_worker"

    def run(self, stage: PipelineStage, task_id: str, **kwargs: Any) -> dict[str, Any]:
        if stage != PipelineStage.DISPATCH:
            return {
                "success": False,
                "task_id": task_id,
                "error": f"Manim Worker only supports DISPATCH stage, got {stage.value}",
            }
        return self._run_dispatch(task_id, **kwargs)

    def _run_dispatch(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        pid = self.plan.project_id
        storyboard = kwargs.get("storyboard") or self._read_context(f"{pid}.storyboard.master")
        narration = kwargs.get("narration") or self._read_context(f"{pid}.narration.script")
        formula_catalog = kwargs.get("formula_catalog") or self._read_context(f"{pid}.formula.catalog")

        # 只提取 Manim/hybrid 镜头
        manim_segs = _get_manim_segments(storyboard, narration)
        if not manim_segs:
            return {"success": True, "task_id": task_id, "outputs": [], "segment_count": 0}

        outputs: list[str] = []
        errors: list[dict] = []
        system_prompt = self._build_system_prompt_text(PipelineStage.DISPATCH)

        # 逐镜头生成，每次只传一个镜头的信息
        for seg in manim_segs:
            try:
                llm = self._require_llm()
                user_message = _build_single_segment_prompt(seg, formula_catalog)
                result = llm.chat_structured(
                    system_prompt, user_message, DISPATCH_OUTPUT_SCHEMA,
                    temperature=0.2, max_tokens=16384,
                )
                if result.get("manim_segments"):
                    for mseg in result["manim_segments"]:
                        sid = mseg.get("segment_id", seg.get("segment_id", "unknown"))
                        key = f"{pid}.manim.{sid}.approved"
                        self._write_context(key, mseg, ContextScope.LONG_TERM)
                        outputs.append(key)
            except RuntimeError as e:
                errors.append({"segment_id": seg.get("segment_id"), "error": str(e)})

        return {
            "success": len(outputs) > 0 or len(manim_segs) == 0,
            "task_id": task_id,
            "outputs": outputs,
            "segment_count": len(outputs),
            "errors": errors if errors else None,
        }

    def _build_system_prompt_text(self, stage: PipelineStage) -> str:
        return "\n".join(self.build_system_prompt(stage))


def _get_manim_segments(storyboard: dict, narration: dict) -> list[dict]:
    """从分镜表中提取 Manim/hybrid 镜头，附上对应的讲解词。"""
    if not storyboard:
        return []
    all_segs = storyboard.get("segments", [])
    manim_segs = [s for s in all_segs if s.get("modality") in ("manim", "hybrid")]
    if not manim_segs:
        return []

    nar_map = {}
    if narration:
        for ns in narration.get("segments", []):
            nar_map[ns["segment_id"]] = ns

    for s in manim_segs:
        sid = s["segment_id"]
        if sid in nar_map:
            s["_narration_text"] = nar_map[sid].get("narration_text", "")
            s["_emphasis"] = nar_map[sid].get("emphasis", [])
        else:
            s["_narration_text"] = ""
            s["_emphasis"] = []

    return manim_segs


def _build_single_segment_prompt(seg: dict, formula_catalog: dict | None) -> str:
    """为一个镜头构建精简 prompt。"""
    parts = [
        "为以下数学科普镜头生成 Manim 动画 Python 代码。",
        "",
        f"## 镜头: {seg.get('title', '')}",
        f"segment_id: {seg.get('segment_id', '')}",
        f"目标: {seg.get('goal', '')}",
        f"modality: {seg.get('modality', '')}",
        f"预计时长: {seg.get('estimated_seconds', 30)}秒",
    ]

    formulas = seg.get("formulas", [])
    if formulas:
        parts.append(f"公式: {', '.join(formulas)}")

    notes = seg.get("animation_notes", [])
    if notes:
        parts.append(f"动画备注: {'; '.join(notes)}")

    narration_text = seg.get("_narration_text", "")
    if narration_text:
        parts.extend(["", f"讲解词: {narration_text}"])

    if formula_catalog:
        # 只传相关公式
        relevant = [f for f in formula_catalog.get("formulas", [])
                    if f.get("latex") in str(formulas)]
        if relevant:
            import json
            parts.extend(["", "## 公式参考", json.dumps(default=str, obj=relevant, ensure_ascii=False, indent=2)])

    parts.extend([
        "",
        "## 要求",
        "1. 生成完整的 Manim Scene 类，class 名用英文（如 SegmentTitle）",
        "2. 使用 MathTex 渲染公式，Text 渲染中文（font='SimHei'）",
        "3. 公式分步展示：每个符号依次 Write/FadeIn，用不同颜色高亮",
        "4. self.wait() 留阅读时间",
        "5. 输出 JSON 格式: {\"manim_segments\": [{\"segment_id\": \"...\", \"title\": \"...\", \"scene_code\": \"...\", \"scene_class_name\": \"...\", \"formulas_displayed\": [...], \"animation_sequence\": [...]}]}",
        f"6. 代码控制在 40-60 行，简洁有效即可",
    ])
    return "\n".join(parts)


def _validate_output(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    segments = result.get("manim_segments")
    if not isinstance(segments, list) or len(segments) == 0:
        errors.append("manim_segments must be a non-empty array")
    else:
        for i, seg in enumerate(segments):
            if not seg.get("segment_id"):
                errors.append(f"manim_segments[{i}] missing segment_id")
            if not seg.get("scene_code"):
                errors.append(f"manim_segments[{i}] missing scene_code")
    return errors

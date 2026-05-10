"""Coordinator Agent 单元测试。"""

from typing import Any

from manimind.agents.coordinator import (
    CoordinatorAgent,
    _validate_dispatch_output,
    _validate_plan_output,
)
from manimind.agents.base import LlmClientProtocol
from manimind.models import PipelineStage, SegmentModality, SegmentSpec, SourceBundle
from manimind.workflow import build_project_plan


# ---------------------------------------------------------------------------
# Mock LLM 客户端 — 实现 LlmClientProtocol，不依赖真实的 llm/client.py
# ---------------------------------------------------------------------------

class MockLlmClient:
    """可预设返回值的 mock LLM 客户端。"""

    def __init__(self, chat_response: str = "", structured_response: dict[str, Any] | None = None):
        self.chat_response = chat_response
        self.structured_response = structured_response or {}
        self.calls: list[dict[str, Any]] = []

    def chat(self, system_prompt: str, user_message: str, *, temperature: float = 0.3, max_tokens: int = 4096) -> str:
        self.calls.append({"method": "chat", "system_prompt": system_prompt, "user_message": user_message})
        return self.chat_response

    def chat_structured(self, system_prompt: str, user_message: str, output_schema: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({
            "method": "chat_structured",
            "system_prompt": system_prompt,
            "user_message": user_message,
            "output_schema": output_schema,
        })
        return self.structured_response


# ---------------------------------------------------------------------------
# 测试夹具
# ---------------------------------------------------------------------------

def _make_plan() -> Any:
    return build_project_plan(
        project_id="test-project",
        title="Test Project",
        source_bundle=SourceBundle(paper_path="paper.pdf"),
        segments=[
            SegmentSpec(
                id="seg-1",
                title="introduction",
                goal="Introduce the concept",
                narration="Let's explore this topic.",
                modality=SegmentModality.HTML,
                estimated_seconds=30,
            ),
            SegmentSpec(
                id="seg-2",
                title="main_derivation",
                goal="Walk through the derivation",
                narration="Now let's derive the formula.",
                modality=SegmentModality.MANIM,
                formulas=["E = mc^2", "\\nabla \\cdot F"],
                estimated_seconds=45,
            ),
        ],
    )


def _valid_plan_output() -> dict[str, Any]:
    return {
        "narration_script": {
            "segments": [
                {
                    "segment_id": "seg-1",
                    "title": "introduction",
                    "narration_text": "Welcome! Today we explore a fascinating topic.",
                    "timing_hints": {"estimated_seconds": 30, "pause_after": 2},
                    "emphasis": ["fascinating"],
                    "formulas_in_context": [],
                },
                {
                    "segment_id": "seg-2",
                    "title": "main_derivation",
                    "narration_text": "Let's look at the famous equation E equals m c squared.",
                    "timing_hints": {"estimated_seconds": 45, "pause_after": 3},
                    "emphasis": ["E equals m c squared"],
                    "formulas_in_context": [
                        {
                            "latex": "E = mc^2",
                            "spoken_form": "E equals m c squared",
                            "display_timing": "during_narration",
                        }
                    ],
                },
            ],
            "voiceover_notes": {
                "style": "conversational",
                "tone": "enthusiastic",
                "total_estimated_duration_seconds": 75,
            },
        },
        "storyboard_master": {
            "segments": [
                {
                    "segment_id": "seg-1",
                    "title": "introduction",
                    "order": 1,
                    "modality": "html",
                    "estimated_seconds": 30,
                    "goal": "Introduce the concept",
                    "formulas": [],
                    "animation_notes": ["fade in title"],
                    "visual_references": [],
                    "html_motion_notes": ["smooth scroll reveal"],
                    "requires_svg_motion": False,
                    "worker_tasks": [
                        {
                            "worker": "html",
                            "task_id": "render.seg-1.html",
                            "objective": "Create HTML intro segment",
                        }
                    ],
                },
                {
                    "segment_id": "seg-2",
                    "title": "main_derivation",
                    "order": 2,
                    "modality": "manim",
                    "estimated_seconds": 45,
                    "goal": "Walk through the derivation",
                    "formulas": ["E = mc^2"],
                    "animation_notes": ["animate formula step by step"],
                    "visual_references": [],
                    "html_motion_notes": [],
                    "requires_svg_motion": False,
                    "worker_tasks": [
                        {
                            "worker": "manim",
                            "task_id": "render.seg-2.manim",
                            "objective": "Create Manim derivation segment",
                        }
                    ],
                },
            ],
            "style_sheet": {
                "color_palette": ["#1a1a2e", "#e94560"],
                "font_scale": "1.2",
                "animation_pacing": "medium",
            },
        },
    }


def _valid_dispatch_output() -> dict[str, Any]:
    return {
        "task_assignments": [
            {
                "task_id": "render.seg-1.html",
                "worker": "html",
                "segment_id": "seg-1",
                "objective": "Create HTML intro segment",
                "dependencies": [],
            },
            {
                "task_id": "render.seg-2.manim",
                "worker": "manim",
                "segment_id": "seg-2",
                "objective": "Create Manim derivation segment",
                "dependencies": [],
            },
        ],
        "session_handoff": {
            "session_summary": "All segments planned and assigned.",
            "completed_tasks": ["plan.storyboard"],
            "pending_tasks": ["render.seg-1.html", "render.seg-2.manim"],
            "blockers": [],
            "notes_for_workers": {
                "html_worker": "Use conversational tone.",
                "manim_worker": "Animate step by step.",
                "svg_worker": "No SVG needed.",
            },
            "review_checkpoints": ["math correctness", "style consistency"],
        },
    }


# ---------------------------------------------------------------------------
# PLAN 阶段测试
# ---------------------------------------------------------------------------

def test_plan_stage_success() -> None:
    """PLAN 阶段：正常输入 → 成功输出讲解脚本和分镜主表。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response=_valid_plan_output())
    agent = CoordinatorAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(PipelineStage.PLAN, "plan.storyboard")

    assert result["success"] is True
    assert result["task_id"] == "plan.storyboard"
    assert "test-project.narration.script" in result["outputs"]
    assert "test-project.storyboard.master" in result["outputs"]
    assert result["segment_count"] == 2
    assert result["total_duration_seconds"] == 75

    # 验证 LLM 被调用
    assert len(mock_llm.calls) == 1
    assert mock_llm.calls[0]["method"] == "chat_structured"
    assert "seg-1" in mock_llm.calls[0]["user_message"]
    assert "seg-2" in mock_llm.calls[0]["user_message"]

    # 验证输出已写入 runtime
    narration = agent._read_context("test-project.narration.script")
    assert narration is not None
    assert narration["segments"][0]["segment_id"] == "seg-1"

    storyboard = agent._read_context("test-project.storyboard.master")
    assert storyboard is not None
    assert storyboard["segments"][0]["segment_id"] == "seg-1"


def test_plan_stage_with_upstream_context() -> None:
    """PLAN 阶段：上游有 Explorer/Planner 产出时，注入用户消息。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response=_valid_plan_output())
    agent = CoordinatorAgent(plan, llm_client=mock_llm, session_id="test-session")

    from manimind.models import ContextScope
    agent._write_context(
        "test-project.research.summary",
        {"core_concepts": [{"name": "relativity"}]},
        scope=ContextScope.SHORT_TERM,
    )

    result = agent.run(PipelineStage.PLAN, "plan.storyboard")
    assert result["success"] is True


def test_plan_stage_no_llm_client() -> None:
    """PLAN 阶段：未注入 LLM 客户端 → 返回错误。"""

    plan = _make_plan()
    agent = CoordinatorAgent(plan, llm_client=None, session_id="test-session")

    result = agent.run(PipelineStage.PLAN, "plan.storyboard")

    assert result["success"] is False
    assert result["error"] == "llm_unavailable"


def test_plan_stage_validation_error() -> None:
    """PLAN 阶段：LLM 返回缺少字段的输出 → 校验失败。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response={"narration_script": {}, "storyboard_master": {}})
    agent = CoordinatorAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(PipelineStage.PLAN, "plan.storyboard")

    assert result["success"] is False
    assert result["error"] == "validation_failed"
    assert len(result["validation_errors"]) >= 2


# ---------------------------------------------------------------------------
# DISPATCH 阶段测试
# ---------------------------------------------------------------------------

def test_dispatch_stage_success() -> None:
    """DISPATCH 阶段：有分镜主表 → 成功生成任务分发和会话交接。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response=_valid_dispatch_output())
    agent = CoordinatorAgent(plan, llm_client=mock_llm, session_id="test-session")

    # 预先写入分镜主表（模拟 PLAN 阶段产出）
    from manimind.models import ContextScope
    agent._write_context(
        "test-project.storyboard.master",
        _valid_plan_output()["storyboard_master"],
        scope=ContextScope.LONG_TERM,
    )

    result = agent.run(PipelineStage.DISPATCH, "dispatch.task")

    assert result["success"] is True
    assert result["task_id"] == "dispatch.task"
    assert "test-project.session.handoff" in result["outputs"]
    assert result["assigned_count"] == 2

    # 验证会话交接已写入
    handoff = agent._read_context("test-project.session.handoff")
    assert handoff is not None
    assert handoff["session_summary"] == "All segments planned and assigned."


def test_dispatch_stage_no_llm_client() -> None:
    """DISPATCH 阶段：未注入 LLM 客户端 → 返回错误。"""

    plan = _make_plan()
    agent = CoordinatorAgent(plan, llm_client=None, session_id="test-session")

    result = agent.run(PipelineStage.DISPATCH, "dispatch.task")

    assert result["success"] is False
    assert result["error"] == "llm_unavailable"


def test_dispatch_stage_validation_error() -> None:
    """DISPATCH 阶段：LLM 返回残缺输出 → 校验失败。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response={
        "task_assignments": [],
        "session_handoff": {},
    })
    agent = CoordinatorAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(PipelineStage.DISPATCH, "dispatch.task")

    assert result["success"] is False
    assert result["error"] == "validation_failed"


# ---------------------------------------------------------------------------
# 边界情况
# ---------------------------------------------------------------------------

def test_unsupported_stage() -> None:
    """不支持的阶段 → 返回错误。"""

    plan = _make_plan()
    agent = CoordinatorAgent(plan, llm_client=MockLlmClient(), session_id="test-session")

    result = agent.run(PipelineStage.REVIEW, "review.task")

    assert result["success"] is False
    assert "does not support" in result["error"]


def test_mode_is_structured_write() -> None:
    """Coordinator 应为 structured_write 模式。"""

    plan = _make_plan()
    agent = CoordinatorAgent(plan, llm_client=MockLlmClient(), session_id="test-session")

    from manimind.models import AgentMode
    assert agent.mode == AgentMode.STRUCTURED_WRITE


def test_profile_auto_resolved() -> None:
    """Agent 应自动从 ProjectPlan 匹配到 coordinator profile。"""

    plan = _make_plan()
    agent = CoordinatorAgent(plan, llm_client=MockLlmClient(), session_id="test-session")

    assert agent.profile.id == "coordinator"
    assert PipelineStage.PLAN in agent.profile.allowed_stages
    assert PipelineStage.DISPATCH in agent.profile.allowed_stages


# ---------------------------------------------------------------------------
# 输出校验器单元测试
# ---------------------------------------------------------------------------

def test_validate_plan_output_valid() -> None:
    errors = _validate_plan_output(_valid_plan_output())
    assert errors == []


def test_validate_plan_output_empty_narration() -> None:
    output = {
        "narration_script": {"segments": []},
        "storyboard_master": _valid_plan_output()["storyboard_master"],
    }
    errors = _validate_plan_output(output)
    assert any("narration_script.segments is empty" in e for e in errors)


def test_validate_plan_output_empty_storyboard() -> None:
    output = {
        "narration_script": _valid_plan_output()["narration_script"],
        "storyboard_master": {"segments": []},
    }
    errors = _validate_plan_output(output)
    assert any("storyboard_master.segments is empty" in e for e in errors)


def test_validate_plan_output_mismatched_segments() -> None:
    """两个表的 segment_id 不一致 → 报错。"""

    narration = _valid_plan_output()["narration_script"]
    storyboard = _valid_plan_output()["storyboard_master"]

    # 给 narration 多加一个 segment
    narration["segments"].append({
        "segment_id": "seg-extra",
        "title": "extra",
        "narration_text": "extra",
        "timing_hints": {"estimated_seconds": 10},
        "emphasis": [],
        "formulas_in_context": [],
    })

    errors = _validate_plan_output({"narration_script": narration, "storyboard_master": storyboard})
    assert any("missing from storyboard_master" in e for e in errors)


def test_validate_dispatch_output_valid() -> None:
    errors = _validate_dispatch_output(_valid_dispatch_output())
    assert errors == []


def test_validate_dispatch_output_empty_assignments() -> None:
    output = {
        "task_assignments": [],
        "session_handoff": _valid_dispatch_output()["session_handoff"],
    }
    errors = _validate_dispatch_output(output)
    assert any("task_assignments must be a non-empty array" in e for e in errors)


def test_validate_dispatch_output_missing_handoff() -> None:
    output = {
        "task_assignments": _valid_dispatch_output()["task_assignments"],
        "session_handoff": None,
    }
    errors = _validate_dispatch_output(output)
    assert any("session_handoff must be an object" in e for e in errors)

"""Worker Agent 单元测试 — HTML / Manim / SVG Worker + Reviewer。"""

from typing import Any

from manimind.agents.html_worker import HtmlWorkerAgent, _validate_output as _validate_html
from manimind.agents.manim_worker import ManimWorkerAgent, _validate_output as _validate_manim
from manimind.agents.svg_worker import SvgWorkerAgent, _validate_output as _validate_svg
from manimind.agents.reviewer import ReviewerAgent, _validate_output as _validate_review
from manimind.models import (
    AgentMode,
    ContextScope,
    PipelineStage,
    SegmentModality,
    SegmentSpec,
    SourceBundle,
)
from manimind.workflow import build_project_plan


class MockLlmClient:
    def __init__(self):
        self.calls: list[dict[str, Any]] = []
        self._default_response: dict[str, Any] = {}

    def set_response(self, response: dict[str, Any]) -> None:
        self._default_response = response

    def chat(self, system_prompt: str, user_message: str, *, temperature: float = 0.3, max_tokens: int = 4096) -> str:
        self.calls.append({"method": "chat"})
        return "mock"

    def chat_structured(self, system_prompt: str, user_message: str, output_schema: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"method": "chat_structured", "user_message": user_message[:200]})
        return self._default_response


def _make_plan() -> Any:
    return build_project_plan(
        project_id="test-project",
        title="Test",
        source_bundle=SourceBundle(paper_path="paper.pdf"),
        segments=[
            SegmentSpec(id="seg-1", title="intro", goal="Introduce", narration="Hello",
                        modality=SegmentModality.HTML, estimated_seconds=30),
            SegmentSpec(id="seg-2", title="main", goal="Derive", narration="Now derive",
                        modality=SegmentModality.MANIM, formulas=["E=mc^2"], estimated_seconds=60),
        ],
    )


def _valid_html_output() -> dict[str, Any]:
    return {
        "html_segments": [
            {
                "segment_id": "seg-1",
                "title": "intro",
                "html_code": "<html><body><h1>Intro</h1></body></html>",
                "template_used": "PPT-level2/1.html",
                "animation_notes": ["fade-in title"],
                "estimated_render_time_seconds": 10,
            }
        ],
        "summary": "Generated 1 HTML segment",
    }


def _valid_manim_output() -> dict[str, Any]:
    return {
        "manim_segments": [
            {
                "segment_id": "seg-2",
                "title": "main",
                "scene_code": "from manim import *\nclass Main(Scene):\n    def construct(self):\n        self.play(Write(MathTex(r'E=mc^2')))",
                "scene_class_name": "Main",
                "formulas_displayed": ["E=mc^2"],
                "animation_sequence": ["Write formula", "Highlight variables"],
                "estimated_render_time_seconds": 30,
            }
        ],
        "summary": "Generated 1 Manim segment",
    }


def _valid_svg_output() -> dict[str, Any]:
    return {
        "svg_segments": [
            {
                "segment_id": "seg-1",
                "title": "intro",
                "svg_code": '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40"/></svg>',
                "animation_type": "fade-in",
                "icon_elements": ["circle"],
                "estimated_render_time_seconds": 5,
            }
        ],
        "summary": "Generated 1 SVG segment",
    }


def _valid_review_output() -> dict[str, Any]:
    return {
        "overall_verdict": "pass",
        "segment_reviews": [
            {
                "segment_id": "seg-1",
                "verdict": "pass",
                "math_correctness": {"status": "pass", "issues": []},
                "narrative_consistency": {"status": "pass", "issues": []},
                "render_feasibility": {"status": "pass", "issues": []},
                "blocking_issues": [],
                "fix_suggestions": [],
            },
            {
                "segment_id": "seg-2",
                "verdict": "pass",
                "math_correctness": {"status": "pass", "issues": []},
                "narrative_consistency": {"status": "pass", "issues": []},
                "render_feasibility": {"status": "pass", "issues": []},
                "blocking_issues": [],
                "fix_suggestions": [],
            },
        ],
        "summary": "All segments pass review.",
        "next_steps": ["Proceed to post-produce."],
    }


# ============================================================================
# HTML Worker 测试
# ============================================================================


def test_html_worker_dispatch_success() -> None:
    plan = _make_plan()
    mock = MockLlmClient()
    mock.set_response(_valid_html_output())
    agent = HtmlWorkerAgent(plan, llm_client=mock, session_id="test")

    result = agent.run(PipelineStage.DISPATCH, "render.html")
    assert result["success"] is True
    assert result["segment_count"] == 1
    assert len(mock.calls) == 1


def test_html_worker_wrong_stage() -> None:
    plan = _make_plan()
    agent = HtmlWorkerAgent(plan, llm_client=MockLlmClient(), session_id="test")
    result = agent.run(PipelineStage.PLAN, "test")
    assert result["success"] is False
    assert "DISPATCH" in result["error"]


def test_html_worker_no_llm() -> None:
    plan = _make_plan()
    agent = HtmlWorkerAgent(plan, llm_client=None, session_id="test")
    result = agent.run(PipelineStage.DISPATCH, "render.html")
    assert result["success"] is False
    assert result["error"] == "llm_unavailable"


def test_html_worker_mode() -> None:
    plan = _make_plan()
    agent = HtmlWorkerAgent(plan, llm_client=MockLlmClient(), session_id="test")
    assert agent.mode == AgentMode.STRUCTURED_WRITE


def test_validate_html_output_valid() -> None:
    assert _validate_html(_valid_html_output()) == []


def test_validate_html_output_missing_code() -> None:
    errors = _validate_html({"html_segments": [{"segment_id": "seg-1"}]})
    assert any("missing html_code" in e for e in errors)


# ============================================================================
# Manim Worker 测试
# ============================================================================


def test_manim_worker_dispatch_success() -> None:
    plan = _make_plan()
    mock = MockLlmClient()
    mock.set_response(_valid_manim_output())
    agent = ManimWorkerAgent(plan, llm_client=mock, session_id="test")

    result = agent.run(PipelineStage.DISPATCH, "render.manim")
    assert result["success"] is True
    assert result["segment_count"] == 1


def test_manim_worker_wrong_stage() -> None:
    plan = _make_plan()
    agent = ManimWorkerAgent(plan, llm_client=MockLlmClient(), session_id="test")
    result = agent.run(PipelineStage.PLAN, "test")
    assert result["success"] is False


def test_validate_manim_output_valid() -> None:
    assert _validate_manim(_valid_manim_output()) == []


def test_validate_manim_output_empty() -> None:
    errors = _validate_manim({"manim_segments": []})
    assert any("non-empty array" in e for e in errors)


# ============================================================================
# SVG Worker 测试
# ============================================================================


def test_svg_worker_dispatch_success() -> None:
    plan = _make_plan()
    mock = MockLlmClient()
    mock.set_response(_valid_svg_output())
    agent = SvgWorkerAgent(plan, llm_client=mock, session_id="test")

    result = agent.run(PipelineStage.DISPATCH, "render.svg")
    assert result["success"] is True
    assert result["segment_count"] == 1


def test_svg_worker_wrong_stage() -> None:
    plan = _make_plan()
    agent = SvgWorkerAgent(plan, llm_client=MockLlmClient(), session_id="test")
    result = agent.run(PipelineStage.PLAN, "test")
    assert result["success"] is False


def test_validate_svg_output_valid() -> None:
    assert _validate_svg(_valid_svg_output()) == []


def test_validate_svg_output_missing_code() -> None:
    errors = _validate_svg({"svg_segments": [{"segment_id": "seg-1"}]})
    assert any("missing svg_code" in e for e in errors)


# ============================================================================
# Reviewer 测试
# ============================================================================


def test_reviewer_review_success() -> None:
    plan = _make_plan()
    mock = MockLlmClient()
    mock.set_response(_valid_review_output())
    agent = ReviewerAgent(plan, llm_client=mock, session_id="test")

    result = agent.run(PipelineStage.REVIEW, "review.outputs")
    assert result["success"] is True
    assert result["verdict"] == "pass"
    assert result["pass_count"] == 2
    assert result["block_count"] == 0


def test_reviewer_review_block() -> None:
    plan = _make_plan()
    mock = MockLlmClient()
    output = _valid_review_output()
    output["overall_verdict"] = "block"
    output["segment_reviews"][0]["verdict"] = "block"
    output["segment_reviews"][0]["blocking_issues"] = ["Formula incorrect"]
    mock.set_response(output)
    agent = ReviewerAgent(plan, llm_client=mock, session_id="test")

    result = agent.run(PipelineStage.REVIEW, "review.outputs")
    assert result["success"] is True
    assert result["verdict"] == "block"
    assert result["block_count"] == 1


def test_reviewer_wrong_stage() -> None:
    plan = _make_plan()
    agent = ReviewerAgent(plan, llm_client=MockLlmClient(), session_id="test")
    result = agent.run(PipelineStage.PLAN, "test")
    assert result["success"] is False


def test_reviewer_mode() -> None:
    plan = _make_plan()
    agent = ReviewerAgent(plan, llm_client=MockLlmClient(), session_id="test")
    assert agent.mode == AgentMode.VERIFY_ONLY


def test_validate_review_output_valid() -> None:
    assert _validate_review(_valid_review_output()) == []


def test_validate_review_output_invalid() -> None:
    errors = _validate_review({"overall_verdict": "unknown", "segment_reviews": []})
    assert any("overall_verdict" in e for e in errors)
    assert any("non-empty array" in e for e in errors)

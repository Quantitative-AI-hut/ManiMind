"""Explorer Agent 单元测试。"""

from typing import Any

from manimind.agents.explorer import (
    ExplorerAgent,
    _validate_summarize_output,
    _validate_plan_output,
)
from manimind.models import PipelineStage, SegmentModality, SegmentSpec, SourceBundle
from manimind.workflow import build_project_plan


# ============================================================================
# Mock LLM 客户端
# ============================================================================

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


# ============================================================================
# 测试夹具
# ============================================================================

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
                formulas=["E = mc^2"],
                estimated_seconds=45,
            ),
        ],
    )


def _valid_prestart_output() -> dict[str, Any]:
    return {
        "overall_status": "ok",
        "tool_checks": [
            {"tool": "python", "available": True, "version": "3.11.0", "status": "ok", "fix_suggestion": ""},
            {"tool": "node", "available": True, "version": "20.0.0", "status": "ok", "fix_suggestion": ""},
            {"tool": "manim", "available": True, "version": "0.18.0", "status": "ok", "fix_suggestion": ""},
            {"tool": "ffmpeg", "available": True, "version": "6.0", "status": "ok", "fix_suggestion": ""},
        ],
        "warnings": [],
        "recommendations": ["All tools ready."],
    }


def _valid_ingest_output() -> dict[str, Any]:
    return {
        "domain": "mathematics",
        "subject_area": "Special Relativity",
        "identified_concepts": [
            {"name": "Spacetime", "description": "Unified space and time continuum"},
            {"name": "Lorentz Transformation", "description": "Coordinate transformation between inertial frames"},
            {"name": "Time Dilation", "description": "Time passes slower for moving observers"},
            {"name": "Length Contraction", "description": "Objects contract along direction of motion"},
            {"name": "Mass-Energy Equivalence", "description": "E = mc^2 relationship"},
        ],
        "difficulty_level": "intermediate",
        "animation_suitability": "Well-suited for animated visualizations of spacetime diagrams and transformations.",
        "sections_needing_simplification": ["Lorentz transformation derivation", "Four-vector formalism"],
        "paper_unavailable": False,
    }


def _valid_summarize_output() -> dict[str, Any]:
    return {
        "research_summary": {
            "paper_available": True,
            "paper_title": "Introduction to Special Relativity",
            "core_concepts": [
                {
                    "name": "Spacetime",
                    "description": "The unified four-dimensional continuum of space and time",
                    "difficulty": "intermediate",
                    "visualizable": True,
                },
                {
                    "name": "Lorentz Transformation",
                    "description": "Mathematical transformation between inertial reference frames",
                    "difficulty": "advanced",
                    "visualizable": True,
                },
                {
                    "name": "Mass-Energy Equivalence",
                    "description": "The principle that mass and energy are interchangeable, expressed as E = mc^2",
                    "difficulty": "intermediate",
                    "visualizable": True,
                },
            ],
            "key_findings": [
                "The speed of light is constant in all inertial frames",
                "Time and space are relative to the observer's motion",
                "Mass and energy are two forms of the same thing",
            ],
            "audience_assessment": {
                "level": "intermediate",
                "prerequisites": ["Basic algebra", "Newtonian mechanics", "Coordinate systems"],
                "simplification_needed": ["Tensor notation", "Four-vector formalism", "Rapidity parameter"],
            },
            "visual_suggestions": [
                {
                    "concept": "Spacetime",
                    "visual_type": "graph",
                    "notes": "Use a 2D spacetime diagram with light cones",
                },
                {
                    "concept": "Mass-Energy Equivalence",
                    "visual_type": "comparison",
                    "notes": "Side-by-side comparison of mass and energy in different scenarios",
                },
            ],
        },
        "glossary": {
            "terms": [
                {
                    "term": "Spacetime",
                    "definition": "A four-dimensional continuum combining three spatial dimensions and one time dimension",
                    "latex": None,
                    "category": "物理",
                    "related_terms": ["Minkowski space", "World line"],
                },
                {
                    "term": "Lorentz Factor",
                    "definition": "The factor by which time dilates and length contracts for a moving object",
                    "latex": "\\gamma = \\frac{1}{\\sqrt{1 - v^2/c^2}}",
                    "category": "数学",
                    "related_terms": ["Time dilation", "Length contraction"],
                },
                {
                    "term": "Mass-Energy Equivalence",
                    "definition": "The principle that mass can be converted to energy and vice versa",
                    "latex": "E = mc^2",
                    "category": "物理",
                    "related_terms": ["Rest energy", "Nuclear reaction"],
                },
            ],
        },
        "formula_catalog": {
            "formulas": [
                {
                    "id": "lorentz-factor",
                    "latex": "\\gamma = \\frac{1}{\\sqrt{1 - v^2/c^2}}",
                    "description": "The Lorentz factor describes how time and space transform for moving objects",
                    "variables": {"\\gamma": "Lorentz factor", "v": "Relative velocity", "c": "Speed of light"},
                    "importance": "core",
                    "visual_approach": "Plot gamma as a function of v/c, showing the asymptote at v=c",
                },
                {
                    "id": "mass-energy",
                    "latex": "E = mc^2",
                    "description": "Mass-energy equivalence — the most famous equation in physics",
                    "variables": {"E": "Energy", "m": "Mass", "c": "Speed of light"},
                    "importance": "core",
                    "visual_approach": "Animate mass converting to energy with particle-antiparticle annihilation",
                },
            ],
        },
    }


def _valid_plan_output() -> dict[str, Any]:
    return {
        "segment_references": [
            {
                "segment_id": "seg-1",
                "matched_assets": ["html-animation/templates/Animation"],
                "recommended_style": "clean-corporate with bold-energetic accent",
                "formulas_to_show": [],
                "pattern_suggestions": ["fade-in with smooth scroll reveal"],
                "resource_gaps": [],
            },
            {
                "segment_id": "seg-2",
                "matched_assets": ["manim/assets/templates"],
                "recommended_style": "dark-premium",
                "formulas_to_show": ["E = mc^2"],
                "pattern_suggestions": ["step-by-step formula reveal", "variable highlighting"],
                "resource_gaps": ["可能需要自定义 3D 变换模板"],
            },
        ],
        "overall_recommendations": [
            "保持两段风格统一但通过配色区分",
            "seg-2 的公式动画需要预渲染检查",
        ],
    }


# ============================================================================
# PRESTART 阶段测试
# ============================================================================

def test_prestart_stage_success() -> None:
    """PRESTART 阶段：正常输入 → 成功分析环境就绪状态。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response=_valid_prestart_output())
    agent = ExplorerAgent(plan, llm_client=mock_llm, session_id="test-session")

    env_report = {
        "overall_status": "ok",
        "python": {"available": True, "version": "3.11.0"},
        "node": {"available": True, "version": "20.0.0"},
        "manim": {"available": True, "version": "0.18.0"},
        "ffmpeg": {"available": True, "version": "6.0"},
        "warnings": [],
    }

    result = agent.run(PipelineStage.PRESTART, "prestart.check", env_report=env_report)

    assert result["success"] is True
    assert result["task_id"] == "prestart.check"
    assert "test-project.env.readiness" in result["outputs"]
    assert result["overall_status"] == "ok"

    # 验证 LLM 被调用
    assert len(mock_llm.calls) == 1
    assert mock_llm.calls[0]["method"] == "chat_structured"

    # 验证已写入短期上下文
    readiness = agent._read_context("test-project.env.readiness")
    assert readiness is not None
    assert readiness["overall_status"] == "ok"


def test_prestart_stage_no_env_report() -> None:
    """PRESTART 阶段：无环境报告 → 仍可运行并降级分析。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response=_valid_prestart_output())
    agent = ExplorerAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(PipelineStage.PRESTART, "prestart.check")

    assert result["success"] is True
    assert result["overall_status"] == "ok"


def test_prestart_stage_no_llm_client() -> None:
    """PRESTART 阶段：未注入 LLM → 返回错误。"""

    plan = _make_plan()
    agent = ExplorerAgent(plan, llm_client=None, session_id="test-session")

    result = agent.run(PipelineStage.PRESTART, "prestart.check")

    assert result["success"] is False
    assert result["error"] == "llm_unavailable"


# ============================================================================
# INGEST 阶段测试
# ============================================================================

def test_ingest_stage_success() -> None:
    """INGEST 阶段：有论文和笔记 → 成功输出初步分析。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response=_valid_ingest_output())
    agent = ExplorerAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(
        PipelineStage.INGEST,
        "ingest.sources",
        paper_text="This paper discusses special relativity...",
        notes=[{"title": "Note 1", "body_text": "Key points about relativity"}],
        assets={"components": [], "manim_assets": [], "references": []},
    )

    assert result["success"] is True
    assert result["task_id"] == "ingest.sources"
    assert "test-project.ingest.findings" in result["outputs"]
    assert result["domain"] == "mathematics"
    assert result["difficulty_level"] == "intermediate"
    assert result["concepts_found"] == 5

    # 验证 LLM 调用参数包含论文内容
    assert len(mock_llm.calls) == 1
    user_msg = mock_llm.calls[0]["user_message"]
    assert "special relativity" in user_msg
    assert "Key points about relativity" in user_msg

    # 验证已落盘
    findings = agent._read_context("test-project.ingest.findings")
    assert findings is not None
    assert findings["domain"] == "mathematics"


def test_ingest_stage_paper_unavailable() -> None:
    """INGEST 阶段：论文不可用 → 降级为仅基于笔记分析。"""

    plan = _make_plan()
    output = _valid_ingest_output()
    output["paper_unavailable"] = True
    mock_llm = MockLlmClient(structured_response=output)
    agent = ExplorerAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(
        PipelineStage.INGEST,
        "ingest.sources",
        paper_text=None,
        notes=[{"title": "Note 1", "body_text": "Notes only"}],
    )

    assert result["success"] is True
    user_msg = mock_llm.calls[0]["user_message"]
    assert "论文文件未找到" in user_msg


def test_ingest_stage_no_llm_client() -> None:
    """INGEST 阶段：未注入 LLM → 返回错误。"""

    plan = _make_plan()
    agent = ExplorerAgent(plan, llm_client=None, session_id="test-session")

    result = agent.run(PipelineStage.INGEST, "ingest.sources")

    assert result["success"] is False
    assert result["error"] == "llm_unavailable"


# ============================================================================
# SUMMARIZE 阶段测试
# ============================================================================

def test_summarize_stage_success() -> None:
    """SUMMARIZE 阶段：正常输入 → 生成研究总结、术语表、公式目录。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response=_valid_summarize_output())
    agent = ExplorerAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(
        PipelineStage.SUMMARIZE,
        "summarize.research",
        paper_text="Special relativity paper...",
        notes=[{"title": "Note", "body_text": "Details..."}],
    )

    assert result["success"] is True
    assert result["task_id"] == "summarize.research"
    assert "test-project.research.summary" in result["outputs"]
    assert "test-project.glossary" in result["outputs"]
    assert "test-project.formula.catalog" in result["outputs"]
    assert result["concepts_count"] == 3
    assert result["terms_count"] == 3
    assert result["formulas_count"] == 2

    # 验证 LLM 被调用
    assert len(mock_llm.calls) == 1
    assert mock_llm.calls[0]["method"] == "chat_structured"

    # 验证三份产出均写入短期上下文
    research = agent._read_context("test-project.research.summary")
    assert research is not None
    assert len(research["core_concepts"]) == 3

    glossary = agent._read_context("test-project.glossary")
    assert glossary is not None
    assert len(glossary["terms"]) == 3

    formula = agent._read_context("test-project.formula.catalog")
    assert formula is not None
    assert len(formula["formulas"]) == 2


def test_summarize_stage_with_ingest_findings() -> None:
    """SUMMARIZE 阶段：有 INGEST 初步发现 → 注入 prompt 增强分析。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response=_valid_summarize_output())
    agent = ExplorerAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(
        PipelineStage.SUMMARIZE,
        "summarize.research",
        paper_text="Paper text...",
        ingest_findings=_valid_ingest_output(),
    )

    assert result["success"] is True
    user_msg = mock_llm.calls[0]["user_message"]
    assert "INGEST 阶段初步发现" in user_msg


def test_summarize_stage_reads_context_fallback() -> None:
    """SUMMARIZE 阶段：kwargs 未提供 ingest_findings → 从上下文回退读取。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response=_valid_summarize_output())
    agent = ExplorerAgent(plan, llm_client=mock_llm, session_id="test-session")

    # 预先写入 INGEST 发现
    agent._write_context(
        "test-project.ingest.findings",
        _valid_ingest_output(),
        scope=__import__("manimind.models", fromlist=["ContextScope"]).ContextScope.SHORT_TERM,
    )

    result = agent.run(PipelineStage.SUMMARIZE, "summarize.research", paper_text="Paper...")

    assert result["success"] is True
    user_msg = mock_llm.calls[0]["user_message"]
    assert "INGEST 阶段初步发现" in user_msg


def test_summarize_stage_no_llm_client() -> None:
    """SUMMARIZE 阶段：未注入 LLM → 返回错误。"""

    plan = _make_plan()
    agent = ExplorerAgent(plan, llm_client=None, session_id="test-session")

    result = agent.run(PipelineStage.SUMMARIZE, "summarize.research")

    assert result["success"] is False
    assert result["error"] == "llm_unavailable"


def test_summarize_stage_validation_error() -> None:
    """SUMMARIZE 阶段：LLM 返回残缺输出 → 校验失败。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response={
        "research_summary": {"core_concepts": [], "key_findings": []},
        "glossary": {"terms": []},
        "formula_catalog": {"formulas": []},
    })
    agent = ExplorerAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(PipelineStage.SUMMARIZE, "summarize.research")

    assert result["success"] is False
    assert result["error"] == "validation_failed"
    assert len(result["validation_errors"]) >= 3


# ============================================================================
# PLAN 阶段测试
# ============================================================================

def test_plan_stage_success() -> None:
    """PLAN 阶段：有分镜和研究成果 → 成功匹配参考资源。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response=_valid_plan_output())
    agent = ExplorerAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(
        PipelineStage.PLAN,
        "explorer.plan",
        research_summary=_valid_summarize_output()["research_summary"],
        glossary=_valid_summarize_output()["glossary"],
        formula_catalog=_valid_summarize_output()["formula_catalog"],
    )

    assert result["success"] is True
    assert result["task_id"] == "explorer.plan"
    assert "test-project.explorer.references" in result["outputs"]
    assert result["segments_matched"] == 2

    # 验证 LLM 调用
    assert len(mock_llm.calls) == 1
    user_msg = mock_llm.calls[0]["user_message"]
    assert "seg-1" in user_msg
    assert "seg-2" in user_msg

    # 验证已落盘
    refs = agent._read_context("test-project.explorer.references")
    assert refs is not None
    assert len(refs["segment_references"]) == 2


def test_plan_stage_no_llm_client() -> None:
    """PLAN 阶段：未注入 LLM → 返回错误。"""

    plan = _make_plan()
    agent = ExplorerAgent(plan, llm_client=None, session_id="test-session")

    result = agent.run(PipelineStage.PLAN, "explorer.plan")

    assert result["success"] is False
    assert result["error"] == "llm_unavailable"


def test_plan_stage_validation_error() -> None:
    """PLAN 阶段：LLM 返回空数组 → 校验失败。"""

    plan = _make_plan()
    mock_llm = MockLlmClient(structured_response={"segment_references": []})
    agent = ExplorerAgent(plan, llm_client=mock_llm, session_id="test-session")

    result = agent.run(PipelineStage.PLAN, "explorer.plan")

    assert result["success"] is False
    assert result["error"] == "validation_failed"


# ============================================================================
# 边界情况
# ============================================================================

def test_unsupported_stage() -> None:
    """不支持的阶段 → 返回错误。"""

    plan = _make_plan()
    agent = ExplorerAgent(plan, llm_client=MockLlmClient(), session_id="test-session")

    result = agent.run(PipelineStage.DISPATCH, "dispatch.task")

    assert result["success"] is False
    assert "does not support" in result["error"]


def test_mode_is_read_only() -> None:
    """Explorer 应为 read_only 模式。"""

    plan = _make_plan()
    agent = ExplorerAgent(plan, llm_client=MockLlmClient(), session_id="test-session")

    from manimind.models import AgentMode
    assert agent.mode == AgentMode.READ_ONLY


def test_profile_auto_resolved() -> None:
    """Agent 应自动从 ProjectPlan 匹配到 explorer profile。"""

    plan = _make_plan()
    agent = ExplorerAgent(plan, llm_client=MockLlmClient(), session_id="test-session")

    assert agent.profile.id == "explorer"
    assert PipelineStage.PRESTART in agent.profile.allowed_stages
    assert PipelineStage.INGEST in agent.profile.allowed_stages
    assert PipelineStage.SUMMARIZE in agent.profile.allowed_stages
    assert PipelineStage.PLAN in agent.profile.allowed_stages


def test_read_only_cannot_write_long_term() -> None:
    """Explorer 是 read_only → 写入长期上下文应抛出 PermissionError。"""

    plan = _make_plan()
    agent = ExplorerAgent(plan, llm_client=MockLlmClient(), session_id="test-session")

    from manimind.models import ContextScope
    import pytest
    with pytest.raises(PermissionError, match="READ_ONLY"):
        agent._write_context("test-project.research.summary", {"data": "test"}, ContextScope.LONG_TERM)


def test_read_only_can_write_short_term() -> None:
    """Explorer 是 read_only → 写入短期上下文应成功。"""

    plan = _make_plan()
    agent = ExplorerAgent(plan, llm_client=MockLlmClient(), session_id="test-session")

    from manimind.models import ContextScope
    path = agent._write_context("test.suggestion", {"data": "test"}, ContextScope.SHORT_TERM)
    assert path.exists()
    content = agent._read_context("test.suggestion")
    assert content == {"data": "test"}


# ============================================================================
# 输出校验器单元测试
# ============================================================================

def test_validate_summarize_output_valid() -> None:
    errors = _validate_summarize_output(_valid_summarize_output())
    assert errors == []


def test_validate_summarize_output_empty_research() -> None:
    output = _valid_summarize_output()
    output["research_summary"] = {"core_concepts": [], "key_findings": []}
    errors = _validate_summarize_output(output)
    assert any("research_summary.core_concepts is empty" in e for e in errors)
    assert any("research_summary.key_findings is empty" in e for e in errors)


def test_validate_summarize_output_empty_glossary() -> None:
    output = _valid_summarize_output()
    output["glossary"] = {"terms": []}
    errors = _validate_summarize_output(output)
    assert any("glossary.terms is empty" in e for e in errors)


def test_validate_summarize_output_empty_formula_catalog() -> None:
    output = _valid_summarize_output()
    output["formula_catalog"] = {"formulas": []}
    errors = _validate_summarize_output(output)
    assert any("formula_catalog.formulas is empty" in e for e in errors)


def test_validate_plan_output_valid() -> None:
    errors = _validate_plan_output(_valid_plan_output())
    assert errors == []


def test_validate_plan_output_empty() -> None:
    errors = _validate_plan_output({"segment_references": []})
    assert any("non-empty array" in e for e in errors)


def test_validate_plan_output_missing_segment_id() -> None:
    errors = _validate_plan_output({"segment_references": [{"matched_assets": [], "recommended_style": "test"}]})
    assert any("missing segment_id" in e for e in errors)

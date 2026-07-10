"""
ManiMind 科普视频完整生成管线
=================================
基于 pipeline.example.json（黎曼猜想入门科普）生成完整视频产物。
在没有 LLM API / Manim 渲染环境时，使用嵌入式专家知识产出所有中间产物，
并生成可直接渲染的 Manim 脚本和 HTML 科普片段。

用法:
    python create_video.py
    python create_video.py --manifest configs/pipeline.example.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# 确保项目源码可导入
PROJECT_ROOT = Path(__file__).resolve().parent
SRC = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC))

from manimind.bootstrap import ensure_workspace
from manimind.models import (
    ContextScope,
    PipelineStage,
    SegmentModality,
    SegmentSpec,
    SourceBundle,
    TaskStatus,
)
from manimind.workflow import build_project_plan
from manimind.runtime_store import (
    persist_plan_snapshot,
    persist_context_packet,
    persist_task_update,
)
from manimind.context_assembly import (
    build_context_packet,
    build_default_prompt_sections,
    PromptSectionCache,
)
from manimind.task_board import update_execution_task_status
from manimind.agents.explorer import ExplorerAgent
from manimind.agents.planner import PlannerAgent
from manimind.agents.coordinator import CoordinatorAgent
from manimind.llm.client import LlmClient

# ---------------------------------------------------------------------------
# 嵌入式科普内容 —— 黎曼猜想入门
# ---------------------------------------------------------------------------

RESEARCH_SUMMARY = {
    "topic": "黎曼猜想（Riemann Hypothesis）入门科普",
    "domain": "数论 / 复分析",
    "difficulty_level": "beginner",
    "core_concepts": [
        {"name": "质数分布", "description": "质数在自然数中的分布看似随机，但存在统计规律。高斯和勒让德发现了质数计数函数 π(x) ≈ x/ln(x)。", "visual_suggestion": "数轴动画，逐步高亮质数位置"},
        {"name": "黎曼 ζ 函数", "description": "ζ(s) = Σ 1/n^s，最初定义在 Re(s)>1 区域。通过解析延拓可扩展到整个复平面。", "visual_suggestion": "三维曲面图，展示 ζ 函数在复平面上的模长分布"},
        {"name": "解析延拓", "description": "将函数定义域从原始收敛区域扩展到更大区域。", "visual_suggestion": "动画：区域逐步扩展，函数图像平滑延伸"},
        {"name": "非平凡零点", "description": "黎曼猜想：ζ 函数的所有非平凡零点的实部都等于 1/2。这些零点位于临界线 Re(s)=1/2 上。", "visual_suggestion": "复平面标注：临界线用醒目颜色，零点用点标记"},
        {"name": "与质数的联系", "description": "黎曼证明了 ζ 函数的零点分布与质数分布之间的精确公式——显式公式。", "visual_suggestion": "对比图：零点分布 vs 质数计数误差图"}
    ],
    "key_findings": [
        "黎曼猜想是数学史上最重要的未解问题之一，Clay 数学研究所悬赏 100 万美元",
        "已有超过 10 万亿个零点被验证位于临界线上",
        "黎曼猜想与密码学、量子物理存在深刻联系",
    ],
    "historical_context": "1859 年，伯恩哈德·黎曼在当选柏林科学院院士时提交了一篇仅 8 页的论文中提出了这个改变数学史的问题。",
}

GLOSSARY = {
    "domain": "数论与复分析",
    "terms": [
        {"term": "质数", "definition": "大于 1 且只能被 1 和自身整除的自然数", "latex": None},
        {"term": "质数计数函数 π(x)", "definition": "不超过 x 的质数个数", "latex": "\\pi(x)"},
        {"term": "ζ 函数", "definition": "复变函数 ζ(s)=Σ 1/n^s (Re(s)>1)", "latex": "\\zeta(s)=\\sum_{n=1}^{\\infty}\\frac{1}{n^s}"},
        {"term": "解析延拓", "definition": "将解析函数从原定义域扩展到大区域且保持解析性的技术", "latex": None},
        {"term": "临界线", "definition": "复平面上 Re(s)=1/2 的直线", "latex": "\\Re(s)=\\frac{1}{2}"},
        {"term": "非平凡零点", "definition": "ζ 函数在 0<Re(s)<1 带状区域内的零点", "latex": None},
        {"term": "素数定理", "definition": "π(x) ~ x/ln(x)，描述质数的渐近分布", "latex": "\\pi(x)\\sim\\frac{x}{\\ln x}"},
    ]
}

FORMULA_CATALOG = {
    "domain": "数论",
    "formulas": [
        {"id": "f1", "latex": "\\zeta(s) = \\sum_{n=1}^{\\infty} \\frac{1}{n^s}, \\quad \\Re(s) > 1", "meaning": "黎曼 ζ 函数的级数定义", "visual_note": "适合逐项展开动画"},
        {"id": "f2", "latex": "\\pi(x) \\sim \\frac{x}{\\ln x}", "meaning": "素数定理：质数密度的渐近估计", "visual_note": "双曲线对比图"},
        {"id": "f3", "latex": "\\zeta(s) = 2^s \\pi^{s-1} \\sin\\left(\\frac{\\pi s}{2}\\right) \\Gamma(1-s) \\zeta(1-s)", "meaning": "ζ 函数的函数方程，揭示 s 与 1-s 的对称性", "visual_note": "分步展示，标注对称中心 s=1/2"},
        {"id": "f4", "latex": "\\Re(s) = \\frac{1}{2}", "meaning": "临界线：黎曼猜想断言所有非平凡零点都在此线上", "visual_note": "复平面动画，垂直线高亮"},
        {"id": "f5", "latex": "\\operatorname{Li}(x) = \\int_2^x \\frac{dt}{\\ln t}", "meaning": "对数积分，比 x/ln(x) 更精确的 π(x) 近似", "visual_note": "积分面积图示"},
    ]
}

NARRATION_SCRIPT = {
    "project_title": "黎曼猜想入门科普",
    "language": "zh-CN",
    "segments": [
        {
            "segment_id": "seg-01",
            "title": "问题引入：质数的秘密",
            "narration": "数字的世界里，有一类特殊的数——质数。2、3、5、7、11……它们只能被1和自身整除，像散落在数轴上的宝石。几千年来，数学家一直在寻找质数的规律。它们看起来随机无序，但真的毫无规律吗？高斯在15岁时就发现：质数虽然稀疏，但稀疏的速度是可以预测的。这个发现，把我们引向了数学史上最著名的一个未解之谜——黎曼猜想。",
            "key_message": "质数分布存在统计规律，引出黎曼猜想的历史意义",
            "estimated_seconds": 25
        },
        {
            "segment_id": "seg-02",
            "title": "ζ 函数：连接质数的桥梁",
            "narration": "1859年，黎曼提出了一个看似简单的函数：ζ(s) 等于所有自然数的 s 次方倒数之和。这个级数最初只在 s 大于 1 时收敛。但黎曼发现，通过一种叫做「解析延拓」的技术，我们可以把这个函数光滑地扩展到整个复平面。奇妙的是：这个函数的零点竟然和质数的分布有着精确的对应关系。黎曼计算了一些零点后发现，它们似乎都落在一条直线上：实部等于二分之一的临界线。他猜测：所有非平凡的零点都在这里。这就是黎曼猜想。",
            "key_message": "ζ 函数定义 → 解析延拓 → 零点与质数的关系 → 猜想陈述",
            "estimated_seconds": 35
        }
    ],
    "voiceover_notes": {
        "total_estimated_duration_seconds": 60,
        "tone": "沉稳清晰，略带悬念感",
        "pacing": "前慢后紧，制造悬念后逐步揭示核心内容"
    }
}

STORYBOARD_MASTER = {
    "project_title": "黎曼猜想入门科普",
    "total_segments": 2,
    "segments": [
        {
            "segment_id": "seg-01", "title": "问题引入：质数的秘密",
            "modality": "html", "estimated_seconds": 25,
            "scene_notes": [
                "【0-5s】黑底，质数 2,3,5,7,11 逐个浮现，带微光效果",
                "【5-12s】数轴从 0 延伸到 100，质数位置用金色圆点标注",
                "【12-18s】叠加蓝色曲线 x/ln(x)，展示质数密度的统计规律",
                "【18-25s】画面缩小，出现高斯头像简笔画 → 过渡到黎曼 1859"
            ],
            "formulas": ["\\pi(x) \\sim \\frac{x}{\\ln x}"],
            "color_palette": "深空蓝背景 #0a0a2e，金色质数点 #ffd700，蓝色曲线 #4da6ff"
        },
        {
            "segment_id": "seg-02", "title": "ζ 函数：连接质数的桥梁",
            "modality": "hybrid", "estimated_seconds": 35,
            "scene_notes": [
                "【0-8s】Manim 三维动画：ζ 函数在复平面上的曲面",
                "【8-14s】动画展示「解析延拓」——曲面平滑扩展",
                "【14-22s】临界线 Re(s)=1/2 用红色标注，零点以闪烁亮点出现",
                "【22-30s】分屏：左侧零点分布，右侧 π(x) 误差波动图",
                "【30-35s】标题字幕：「黎曼猜想——数学皇冠上的明珠」"
            ],
            "formulas": ["\\zeta(s)=\\sum_{n=1}^{\\infty}\\frac{1}{n^s}", "\\Re(s)=\\frac{1}{2}"],
            "color_palette": "深空蓝背景，红色临界线 #ff3333，零点亮白"
        }
    ]
}


class VideoPipeline:
    """完整科普视频生成管线。"""

    def __init__(self, manifest_path: Path, session_id: str = "video-session"):
        self.manifest_path = manifest_path
        self.session_id = session_id
        self.project_root = PROJECT_ROOT
        self.payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.segments = self._build_segments(self.payload["segments"])
        source_bundle = SourceBundle(**self.payload["source_bundle"])
        self.plan = build_project_plan(
            project_id=self.payload["project_id"],
            title=self.payload["title"],
            source_bundle=source_bundle,
            segments=self.segments,
        )
        self.pid = self.plan.project_id
        ensure_workspace()
        self.llm_client = self._init_llm()

    def _build_segments(self, raw_segments):
        return [SegmentSpec(
            id=item["id"], title=item["title"], goal=item["goal"],
            narration=item["narration"],
            modality=SegmentModality(item.get("modality", "hybrid")),
            formulas=item.get("formulas", []),
            html_motion_notes=item.get("html_motion_notes", []),
            requires_svg_motion=item.get("requires_svg_motion", False),
            estimated_seconds=item.get("estimated_seconds", 20),
        ) for item in raw_segments]

    def _init_llm(self):
        try: return LlmClient()
        except (ValueError, Exception): return None

    def phase_plan(self):
        print("[Phase 0] 构建项目计划...")
        persisted = persist_plan_snapshot(plan=self.plan, session_id=self.session_id, source_manifest=str(self.manifest_path))
        return {"phase": "plan", "persisted_paths": persisted}

    def phase_explorer(self):
        print("[Phase 1] Explorer Agent 探索阶段...")
        context_packet = build_context_packet(plan=self.plan, role_id="explorer", stage=PipelineStage.SUMMARIZE)
        persist_context_packet(plan=self.plan, session_id=self.session_id, packet=context_packet)
        explorer = ExplorerAgent(self.plan, self.llm_client, self.session_id)
        if self.llm_client:
            result = explorer.run(PipelineStage.SUMMARIZE, task_id=f"{self.pid}.explorer.summarize",
                paper_text="(论文未提供，使用项目内置知识库)",
                notes=f"受众: {self.payload['source_bundle']['audience']}")
        else:
            explorer._write_context(f"{self.pid}.research.summary", RESEARCH_SUMMARY, ContextScope.SHORT_TERM)
            explorer._write_context(f"{self.pid}.glossary", GLOSSARY, ContextScope.SHORT_TERM)
            explorer._write_context(f"{self.pid}.formula.catalog", FORMULA_CATALOG, ContextScope.SHORT_TERM)
            result = {"success": True, "mode": "offline"}
        print(f"  Explorer 结果: {json.dumps(result, ensure_ascii=False)}")
        return {"phase": "explorer", "result": result}

    def phase_planner(self):
        print("[Phase 2] Planner Agent 规划阶段...")
        context_packet = build_context_packet(plan=self.plan, role_id="planner", stage=PipelineStage.SUMMARIZE)
        persist_context_packet(plan=self.plan, session_id=self.session_id, packet=context_packet)
        planner = PlannerAgent(self.plan, self.llm_client, self.session_id)
        if self.llm_client:
            result = planner.run(PipelineStage.SUMMARIZE, task_id=f"{self.pid}.planner.constraints")
        else:
            planner._write_context(f"{self.pid}.constraint.analysis", {
                "audience_match": {"difficulty_level": "beginner", "recommendations": ["避免引入复分析严格定义", "用类比解释解析延拓", "以视觉为主、公式为辅"]},
                "time_estimates": [{"segment_id": "seg-01", "min_seconds": 20, "optimal_seconds": 25}, {"segment_id": "seg-02", "min_seconds": 30, "optimal_seconds": 35}],
                "modality_recommendations": [{"segment_id": "seg-01", "modality": "html"}, {"segment_id": "seg-02", "modality": "hybrid"}],
                "risk_points": ["解析延拓概念较难理解", "复平面可视化需精心设计", "60 秒总时长偏紧"]
            }, ContextScope.SHORT_TERM)
            planner._write_context(f"{self.pid}.feasibility.assessment", {
                "overall_score": 4, "success_factors": ["主题知名度高", "可视化空间大"], "challenges": ["数学抽象层次多"]
            }, ContextScope.SHORT_TERM)
            result = {"success": True, "mode": "offline"}
        print(f"  Planner 结果: {json.dumps(result, ensure_ascii=False)}")
        return {"phase": "planner", "result": result}

    def phase_coordinator(self):
        print("[Phase 3] Coordinator Agent 生成脚本与分镜...")
        context_packet = build_context_packet(plan=self.plan, role_id="coordinator", stage=PipelineStage.PLAN)
        persist_context_packet(plan=self.plan, session_id=self.session_id, packet=context_packet)
        coordinator = CoordinatorAgent(self.plan, self.llm_client, self.session_id)
        if self.llm_client:
            result = coordinator.run(PipelineStage.PLAN, task_id=f"{self.pid}.coordinator.plan")
        else:
            coordinator._write_context(f"{self.pid}.narration.script", NARRATION_SCRIPT, ContextScope.LONG_TERM)
            coordinator._write_context(f"{self.pid}.storyboard.master", STORYBOARD_MASTER, ContextScope.LONG_TERM)
            result = {"success": True, "mode": "offline"}
        print(f"  Coordinator 结果: {json.dumps(result, ensure_ascii=False)}")
        return {"phase": "coordinator", "result": result}

    def phase_generate_assets(self) -> dict:
        print("[Phase 4] 生成渲染产物...")
        output_dir = Path(self.plan.runtime_layout.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        assets = []

        manim_script = self._generate_manim_script()
        manim_path = output_dir / "riemann_zeta_scenes.py"
        manim_path.write_text(manim_script, encoding="utf-8")
        assets.append(str(manim_path))

        html_paths = self._generate_html_fragments(output_dir)
        assets.extend(html_paths)

        narration_path = output_dir / "narration_full.txt"
        narration_path.write_text(self._generate_narration_text(), encoding="utf-8")
        assets.append(str(narration_path))

        report_path = output_dir / "project_report.json"
        report = {
            "project_id": self.pid, "title": self.payload["title"],
            "narration_script": NARRATION_SCRIPT, "storyboard_master": STORYBOARD_MASTER,
            "research_summary": RESEARCH_SUMMARY, "glossary": GLOSSARY, "formula_catalog": FORMULA_CATALOG,
            "how_to_render": {
                "manim": "manim -pql riemann_zeta_scenes.py ZetaSurface3D",
                "html": "直接用浏览器打开 html/ 目录下的文件",
                "install": "pip install manim && winget install ffmpeg"
            }
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        assets.append(str(report_path))

        for p in [manim_path] + html_paths + [narration_path, report_path]:
            print(f"  产出: {p}")
        return {"phase": "generate_assets", "output_dir": str(output_dir), "assets": assets}

    def _generate_manim_script(self) -> str:
        return r'''"""
黎曼猜想科普视频 — Manim 动画场景
渲染命令: manim -pql riemann_zeta_scenes.py PrimeDistribution
"""

from manim import *
import numpy as np


class PrimeDistribution(Scene):
    """场景：质数在数轴上的分布 + 素数定理曲线。"""
    def construct(self):
        title = Text("质数的秘密", font_size=48, color=GOLD).to_edge(UP)
        self.play(Write(title)); self.wait(0.5)
        number_line = NumberLine(x_range=[0, 100, 10], length=12, include_numbers=True, color=BLUE)
        number_line.next_to(title, DOWN, buff=1.0)
        self.play(Create(number_line))
        primes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
        dots = VGroup(*[Dot(point=number_line.n2p(p), color=GOLD, radius=0.08) for p in primes])
        self.play(LaggedStart(*[Create(d) for d in dots], lag_ratio=0.02)); self.wait(1)
        formula = MathTex(r"\pi(x) \sim \frac{x}{\ln x}", font_size=42, color=BLUE)
        formula.next_to(number_line, DOWN, buff=0.8)
        self.play(Write(formula))
        explanation = Text("质数的密度 ≈ 1/ln(x)，x越大质数越稀疏", font_size=28, color=WHITE)
        explanation.next_to(formula, DOWN, buff=0.4)
        self.play(FadeIn(explanation)); self.wait(2)
        self.play(*[FadeOut(m) for m in self.mobjects])


class ZetaSeriesIntro(Scene):
    """场景：ζ 函数级数定义逐项展开。"""
    def construct(self):
        title = Text("黎曼 ζ 函数", font_size=48, color=GOLD).to_edge(UP)
        self.play(Write(title))
        zeta_def = MathTex(r"\zeta(s) = \sum_{n=1}^{\infty} \frac{1}{n^s}, \quad \Re(s) > 1", font_size=42, color=WHITE)
        zeta_def.next_to(title, DOWN, buff=1.5)
        self.play(Write(zeta_def)); self.wait(1)
        terms = VGroup(*[MathTex(rf"\frac{{1}}{{{n}^{{s}}}}", font_size=36, color=BLUE if n==1 else TEAL) for n in range(1,6)])
        terms.arrange(RIGHT, buff=0.3); terms.next_to(zeta_def, DOWN, buff=1.0)
        self.play(Write(terms[0]))
        for i in range(1,5):
            plus = MathTex("+", font_size=36, color=WHITE)
            plus.next_to(terms[i-1], RIGHT, buff=0.2); terms[i].next_to(plus, RIGHT, buff=0.2)
            self.play(Write(plus), Write(terms[i]))
        dots = MathTex(r"\cdots", font_size=36, color=WHITE).next_to(terms[-1], RIGHT, buff=0.2)
        self.play(Write(dots)); self.wait(2)
        self.play(*[FadeOut(m) for m in self.mobjects])


class ZetaSurface3D(ThreeDScene):
    """场景：ζ 函数在复平面上的三维展示 + 临界线。"""
    def construct(self):
        self.set_camera_orientation(phi=65*DEGREES, theta=-45*DEGREES)
        title = Text("ζ 函数在复平面上的曲面", font_size=36, color=GOLD).to_corner(UL)
        self.add_fixed_in_frame_mobjects(title); self.play(Write(title))
        axes = ThreeDAxes(x_range=[-2,3,1], y_range=[-10,10,5], z_range=[0,5,1], x_length=8, y_length=6, z_length=4)
        self.play(Create(axes))
        x_label = axes.get_x_axis_label(MathTex(r"\Re(s)"), edge=DOWN)
        y_label = axes.get_y_axis_label(MathTex(r"\Im(s)"), edge=LEFT)
        z_label = axes.get_z_axis_label(MathTex(r"|\zeta(s)|"), edge=UP)
        self.play(Write(x_label), Write(y_label), Write(z_label))
        critical_label = MathTex(r"\Re(s)=\frac{1}{2}", font_size=36, color=RED).to_corner(UR)
        self.add_fixed_in_frame_mobjects(critical_label); self.play(Write(critical_label))
        wave = axes.plot_parametric_curve(lambda t: np.array([0.5, t, 1.5+np.sin(t*0.8)*0.8]), t_range=[-10,10], color=BLUE, stroke_width=3)
        self.play(Create(wave), run_time=3)
        zeros = VGroup(*[Dot3D(point=axes.c2p(0.5,y,0.1), color=YELLOW, radius=0.08) for y in [-9,-7,-4.5,-2,0.5,3,5.5,8]])
        self.play(LaggedStart(*[Create(z) for z in zeros], lag_ratio=0.1)); self.wait(1)
        zero_label = Text("非平凡零点（猜想都在临界线上）", font_size=24, color=YELLOW).to_edge(DOWN)
        self.add_fixed_in_frame_mobjects(zero_label); self.play(Write(zero_label))
        final_text = Text("黎曼猜想：数学皇冠上的明珠", font_size=36, color=GOLD).to_edge(DOWN)
        self.add_fixed_in_frame_mobjects(final_text); self.play(Write(final_text))
        self.wait(3)
        self.play(*[FadeOut(m) for m in self.mobjects])
'''

    def _generate_html_fragments(self, output_dir: Path) -> list[str]:
        html_dir = output_dir / "html"; html_dir.mkdir(exist_ok=True)
        paths = []

        html_seg01 = '''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>质数的秘密 - 黎曼猜想科普</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0a0a2e;color:#fff;font-family:'Microsoft YaHei',sans-serif;width:1920px;height:1080px;display:flex;align-items:center;justify-content:center}
.container{text-align:center}.title{font-size:48px;color:#ffd700;margin-bottom:40px;animation:fadeIn 2s ease}
.number-line-container{position:relative;width:80%;height:200px;border-bottom:2px solid #4da6ff}
.prime-dot{position:absolute;width:12px;height:12px;background:#ffd700;border-radius:50%;bottom:-6px;box-shadow:0 0 10px rgba(255,215,0,.6);animation:dotAppear .5s ease forwards;opacity:0}
.formula{font-size:36px;color:#4da6ff;margin-top:40px;animation:fadeIn 2s ease 1s both}
.explanation{font-size:24px;color:#ccc;margin-top:20px;animation:fadeIn 2s ease 1.5s both}
@keyframes fadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
@keyframes dotAppear{from{opacity:0;transform:scale(0)}to{opacity:1;transform:scale(1)}}</style></head>
<body><div class="container"><div class="title">质数的秘密</div>
<div class="number-line-container" id="numberLine"></div>
<div class="formula">π(x) ~ x / ln(x)</div>
<div class="explanation">质数看似随机，但密度的下降规律可以被精确预测</div></div>
<script>const primes=[2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97];
const line=document.getElementById('numberLine');
primes.forEach((p,i)=>{const dot=document.createElement('div');dot.className='prime-dot';dot.style.left=(p/100*100)+'%';dot.style.animationDelay=(i*.08)+'s';line.appendChild(dot)});
for(let i=0;i<=100;i+=10){const t=document.createElement('div');t.style.cssText=`position:absolute;left:${i}%;bottom:-10px;width:1px;height:10px;background:#4da6ff80`;line.appendChild(t)}</script></body></html>'''
        p1 = html_dir / "seg01_prime_distribution.html"
        p1.write_text(html_seg01, encoding="utf-8"); paths.append(str(p1))

        html_seg02 = '''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>黎曼 ζ 函数</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0a0a2e;color:#fff;font-family:'Microsoft YaHei',sans-serif;width:1920px;height:1080px;display:flex;align-items:center;justify-content:center}
.container{text-align:center}.title{font-size:48px;color:#ffd700;margin-bottom:30px;animation:fadeIn 1.5s ease}
.formula-block{font-size:42px;color:#fff;margin:30px 0;padding:30px;border:1px solid #4da6ff40;border-radius:12px;background:rgba(77,166,255,.05);animation:fadeIn 2s ease .5s both}
.critical-line{margin-top:40px;animation:fadeIn 2s ease 1.5s both}
.critical-line .eq{font-size:36px;color:#f33}.critical-line .desc{font-size:24px;color:#fcc;margin-top:10px}
.final{font-size:32px;color:#ffd700;margin-top:50px;animation:fadeIn 3s ease 2.5s both}
@keyframes fadeIn{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}</style></head>
<body><div class="container"><div class="title">黎曼 ζ 函数</div>
<div class="formula-block">ζ(s) = Σ 1/n<sup>s</sup> &nbsp; (Re(s) > 1)</div>
<div class="critical-line"><div class="eq">Re(s) = 1/2</div><div class="desc">临界线 —— 所有非平凡零点都在这里</div></div>
<div class="final">黎曼猜想：数学皇冠上的明珠</div></div></body></html>'''
        p2 = html_dir / "seg02_zeta_function.html"
        p2.write_text(html_seg02, encoding="utf-8"); paths.append(str(p2))
        return paths

    def _generate_narration_text(self) -> str:
        lines = ["=" * 60, f"《{self.payload['title']}》— 完整解说词", "=" * 60, ""]
        for seg in NARRATION_SCRIPT["segments"]:
            lines.append(f"【{seg['segment_id']}】{seg['title']}（{seg['estimated_seconds']}秒）")
            lines.append("-" * 40)
            lines.append(seg["narration"]); lines.append("")
        return "\n".join(lines)

    def run(self) -> dict:
        print("=" * 60)
        print(f"  ManiMind 科普视频生成管线")
        print(f"  项目: {self.payload['title']}")
        print(f"  LLM 模式: {'在线' if self.llm_client else '离线（嵌入式知识库）'}")
        print("=" * 60)
        results = {}
        results["plan"] = self.phase_plan()
        results["explorer"] = self.phase_explorer()
        results["planner"] = self.phase_planner()
        results["coordinator"] = self.phase_coordinator()
        results["assets"] = self.phase_generate_assets()
        print("\n" + "=" * 60)
        print(f"  管线执行完毕! 产出目录: {results['assets']['output_dir']}")
        print("=" * 60)
        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ManiMind 科普视频生成管线")
    parser.add_argument("--manifest", type=Path, default=PROJECT_ROOT/"configs"/"pipeline.example.json")
    parser.add_argument("--session-id", type=str, default="video-session")
    args = parser.parse_args()
    if not args.manifest.exists():
        print(f"错误: 清单文件不存在: {args.manifest}"); sys.exit(1)
    VideoPipeline(args.manifest, args.session_id).run()


if __name__ == "__main__":
    main()

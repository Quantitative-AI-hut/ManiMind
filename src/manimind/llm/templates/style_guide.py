"""3B1B-inspired visual style guide for Manim code generation.

This module provides reusable style specifications extracted from professional
math education videos. Embed these prompts into LLM code generation to produce
visually consistent, high-quality animations.
"""

# ============================================================================
# Core Style Profile
# ============================================================================

STYLE_PROFILE = {
    "color_scheme": {
        "background": "BLACK",
        "primary_text": "WHITE",
        "accent_1": "BLUE",       # curves, main graphics
        "accent_2": "YELLOW",     # highlights, labels
        "accent_3": "GREEN",      # tangents, emphasis
        "warning": "RED",         # errors, important points
        "subtle": "GRAY",         # grid lines, axes
        "fill": "BLUE",           # area shading
        "fill_opacity": 0.3,
    },
    "layout": {
        "title_position": "TOP",
        "formula_position": "BOTTOM_LEFT",
        "graph_region": "CENTER",
        "annotation_position": "BOTTOM",
        "max_elements_per_frame": 3,
    },
    "typography": {
        "title_size": 42,
        "formula_size": 36,
        "annotation_size": 24,
        "axis_label_size": 28,
        "font": "SimHei",         # Chinese font
    },
    "animation": {
        "write_speed": 1.0,
        "wait_after_key_point": 2.0,
        "transition_duration": 1.5,
        "use_arrows": True,
        "use_highlights": True,
    }
}


# ============================================================================
# Prompt Template — inject into LLM code generation
# ============================================================================

STYLE_INJECTION_PROMPT = """
【视觉风格要求 — 参考 3Blue1Brown/漫士沉思录】

1. 配色：黑色背景，白色文字，蓝色曲线，黄色高亮关键点，绿色标注切线/重点
   实现: self.camera.background_color = BLACK
   Axes用GRAY，曲线用BLUE(stroke_width=4)，切点用YELLOW，切线用GREEN

2. 布局：标题放顶部(42号字体)，公式放左下角(36号)，图形占中央区域，注释放底部(24号)
   实现: title.to_edge(UP), formula.to_corner(DL), annotation.to_edge(DOWN)

3. 层次：每帧2-3个核心元素，不堆砌。重要结论用大字号+高亮色
   实现: 先展示标题和图形，再缓缓出现公式，最后出现注释

4. 引导视线：用箭头/虚线标注关键位置，用半透明填充强调区域
   实现: Arrow(起点, 终点, color=YELLOW), Rectangle(..., fill_color=BLUE, fill_opacity=0.3)

5. 动态演示：公式和图形通过Write/Create渐入，不是突然出现
   实现: self.play(Write(title)), self.play(Create(graph)), self.wait(2)

6. 字体：中文用SimHei，数学公式用MathTex(LaTeX)，字号足够大
   实现: Text("标题", font="SimHei", color=WHITE).to_edge(UP)
"""


def get_style_prompt() -> str:
    """Return the full style injection prompt for LLM code generation."""
    return STYLE_INJECTION_PROMPT


def build_styled_prompt(base_prompt: str) -> str:
    """Wrap a base prompt with style guide requirements."""
    return base_prompt + "\n\n" + STYLE_INJECTION_PROMPT


# ============================================================================
# Quality Review Checklist — for Kimi vision comparison
# ============================================================================

REVIEW_CHECKLIST = """
请按以下维度评分(1-10):

1. 配色方案: 是否使用黑色背景+白色文字+蓝色曲线+黄色高亮
2. 布局规律: 标题/公式/图形/注释是否各就其位
3. 信息密度: 每帧是否有2-3个关键元素
4. 视觉引导: 是否有箭头/虚线/高亮标注
5. 动画流畅度: 元素是否渐入而非突然出现
6. 字体排版: 中文是否清晰，公式是否使用LaTeX

总评: [分数]/60
需要改进的1-2点:
"""

"""生成所有17段 Manim 动画脚本并逐个渲染"""
from manim import *
import numpy as np
from pathlib import Path
import sys

OUTPUT = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
SEGMENTS_DIR = OUTPUT / "segments"
SCRIPTS_DIR = OUTPUT / "manim_scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

MANIM_TEMPLATE = '''"""Seg{num:02d}: {title}"""
from manim import *
import numpy as np

class Seg{num:02d}(Scene):
    def construct(self):
        BG_COLOR = "#0A0A1A"
        self.camera.background_color = BG_COLOR
{body}
'''

def build_scene_body(num):
    """根据段号构建对应的场景"""
    if num == 1:
        return r'''
        # Title
        title = Text("黎曼猜想", font_size=72, color=GOLD, font="Microsoft YaHei")
        subtitle = Text("数学史上最迷人的未解之谜", font_size=32, color=WHITE, font="Microsoft YaHei")
        subtitle.next_to(title, DOWN, buff=0.4)
        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(subtitle), run_time=1)
        self.wait(0.5)

        # Prize text
        prize = Text("千禧年七大数学难题之一 · 悬赏100万美元", font_size=28, color=YELLOW, font="Microsoft YaHei")
        prize.next_to(subtitle, DOWN, buff=1.0)
        self.play(Write(prize), run_time=1.5)
        self.wait(1)

        # Year timeline
        year1859 = Text("1859年", font_size=36, color=BLUE, font="Microsoft YaHei")
        arrow = Text("→", font_size=36, color=WHITE)
        year_now = Text("已过167年仍未证明", font_size=36, color=RED, font="Microsoft YaHei")
        timeline = VGroup(year1859, arrow, year_now).arrange(RIGHT, buff=0.5)
        timeline.next_to(prize, DOWN, buff=1.0)
        self.play(Write(year1859), run_time=0.8)
        self.play(Write(arrow), run_time=0.5)
        self.play(Write(year_now), run_time=1)
        self.wait(1.5)

        # Zeta formula
        zeta = MathTex(r"\zeta(s) = \sum_{n=1}^{\infty} \frac{1}{n^s}", font_size=48, color=WHITE)
        zeta.next_to(timeline, DOWN, buff=1.2)
        box = SurroundingRectangle(zeta, color=GOLD, buff=0.3)
        self.play(Write(zeta), run_time=1.5)
        self.play(Create(box), run_time=0.8)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 2:
        return r'''
        title = Text("质数的秘密", font_size=60, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Number line with primes
        nl = NumberLine(x_range=[0, 100, 10], length=12, include_numbers=True, color=BLUE)
        nl.next_to(title, DOWN, buff=1.0)
        self.play(Create(nl), run_time=1.5)

        primes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
        dots = VGroup(*[Dot(point=nl.n2p(p), color=GOLD, radius=0.06) for p in primes])
        self.play(LaggedStart(*[Create(d) for d in dots], lag_ratio=0.03), run_time=3)
        self.wait(1)

        # Formula
        formula = MathTex(r"\pi(x) \sim \frac{x}{\ln x}", font_size=44, color=BLUE)
        formula.next_to(nl, DOWN, buff=1.0)
        label = Text("素数定理", font_size=28, color=WHITE, font="Microsoft YaHei")
        label.next_to(formula, DOWN, buff=0.3)
        fg = VGroup(formula, label)
        self.play(Write(fg), run_time=2)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 3:
        return r'''
        title = Text("从欧拉到黎曼", font_size=60, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Two key events
        euler = VGroup(
            Text("1737", font_size=40, color=BLUE, font="Microsoft YaHei"),
            Text("欧拉乘积公式", font_size=30, color=WHITE, font="Microsoft YaHei")
        ).arrange(DOWN, buff=0.2)
        riemann = VGroup(
            Text("1859", font_size=40, color=GOLD, font="Microsoft YaHei"),
            Text("黎曼的八页论文", font_size=30, color=WHITE, font="Microsoft YaHei")
        ).arrange(DOWN, buff=0.2)
        events = VGroup(euler, riemann).arrange(RIGHT, buff=3.0)
        events.next_to(title, DOWN, buff=1.5)
        self.play(Write(euler), run_time=1)
        self.play(Write(riemann), run_time=1)
        self.wait(0.5)

        # Arrow between them
        arr = Arrow(euler.get_right(), riemann.get_left(), color=WHITE, buff=0.3)
        self.play(Create(arr), run_time=0.5)
        self.wait(0.5)

        # Euler product = zeta
        eq = MathTex(r"\prod_{p} \frac{1}{1-p^{-s}} = \sum_{n=1}^{\infty} \frac{1}{n^s}", font_size=40, color=WHITE)
        eq.next_to(events, DOWN, buff=1.5)
        eq_box = SurroundingRectangle(eq, color=GOLD, buff=0.3)
        self.play(Write(eq), run_time=2)
        self.play(Create(eq_box), run_time=0.8)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 4:
        return r'''
        title = Text("黎曼 ζ 函数", font_size=60, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Build up the formula piece by piece
        parts = [
            MathTex(r"\zeta(s)", font_size=54, color=GOLD),
            MathTex(r"=", font_size=54, color=WHITE),
            MathTex(r"\sum_{n=1}^{\infty}", font_size=54, color=BLUE),
            MathTex(r"\frac{1}{n^s}", font_size=54, color=TEAL),
        ]
        full = VGroup(*parts).arrange(RIGHT, buff=0.2)
        full.next_to(title, DOWN, buff=1.5)
        for p in parts:
            self.play(Write(p), run_time=0.8)
        self.wait(1)

        # Domain constraint
        domain = MathTex(r"\Re(s) > 1", font_size=40, color=YELLOW)
        domain.next_to(full, DOWN, buff=0.8)
        domain_box = SurroundingRectangle(domain, color=YELLOW, buff=0.2)
        self.play(Write(domain), run_time=1)
        self.play(Create(domain_box), run_time=0.5)
        self.wait(1)

        # Explanation
        expl = Text("级数只在复平面上 Re(s)>1 的区域收敛", font_size=26, color=WHITE, font="Microsoft YaHei")
        expl.next_to(domain_box, DOWN, buff=0.8)
        self.play(FadeIn(expl), run_time=1.5)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 5:
        return r'''
        title = Text("解析延拓", font_size=60, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Complex plane visualization
        axes = Axes(x_range=[-1, 3, 0.5], y_range=[-5, 5, 1], x_length=8, y_length=5,
                    axis_config={"color": BLUE}, x_axis_config={"numbers_to_include": [-0.5,0,0.5,1,1.5,2,2.5]})
        axes.next_to(title, DOWN, buff=0.8)
        axes.y_axis.add_numbers(font_size=18)
        labels = axes.get_axis_labels(x_label="Re(s)", y_label="Im(s)")
        self.play(Create(axes), Write(labels), run_time=2)

        # Highlight Re(s)>1 region
        region = Rectangle(width=4, height=5, color=GREEN, fill_opacity=0.15, stroke_width=2)
        region.move_to(axes.c2p(1.5, 0)).align_to(axes.c2p(1, 0), LEFT)
        region_label = Text("收敛区域", font_size=26, color=GREEN, font="Microsoft YaHei")
        region_label.next_to(region, UP, buff=0.1)
        self.play(FadeIn(region), Write(region_label), run_time=1.5)
        self.wait(1)

        # Extension arrow
        ext_text = Text("解析延拓 → 扩展到整个复平面", font_size=28, color=GOLD, font="Microsoft YaHei")
        ext_text.next_to(axes, DOWN, buff=0.8)
        self.play(Write(ext_text), run_time=2)
        self.wait(1)

        # Mark singularity at s=1
        pole = Dot(axes.c2p(1, 0), color=RED, radius=0.12)
        pole_label = Text("s=1 极点", font_size=24, color=RED, font="Microsoft YaHei")
        pole_label.next_to(pole, DOWN+RIGHT, buff=0.2)
        self.play(Create(pole), Write(pole_label), run_time=1)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 6:
        return r'''
        title = Text("零点与质数", font_size=56, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Explicit formula
        formula = MathTex(
            r"\psi(x) = x - \sum_{\rho} \frac{x^{\rho}}{\rho} - \ln(2\pi)",
            font_size=38, color=WHITE
        )
        formula.next_to(title, DOWN, buff=1.5)
        fb = SurroundingRectangle(formula, color=GOLD, buff=0.3)
        self.play(Write(formula), run_time=2.5)
        self.play(Create(fb), run_time=0.8)
        self.wait(1)

        # Explanation text
        e1 = Text("每一个 ζ 函数的零点 ρ", font_size=28, color=BLUE, font="Microsoft YaHei")
        e2 = Text("都精确控制着质数分布的一种频率", font_size=28, color=BLUE, font="Microsoft YaHei")
        e3 = Text("零点越靠近临界线，质数分布越平滑", font_size=28, color=YELLOW, font="Microsoft YaHei")
        exp = VGroup(e1, e2, e3).arrange(DOWN, buff=0.3)
        exp.next_to(fb, DOWN, buff=1.0)
        for e in [e1, e2, e3]:
            self.play(Write(e), run_time=1)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 7:
        return r'''
        title = Text("临界线", font_size=60, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Complex plane
        axes = Axes(x_range=[-1, 3, 0.5], y_range=[0, 50, 10], x_length=8, y_length=5,
                    axis_config={"color": BLUE})
        axes.next_to(title, DOWN, buff=0.8)
        labels = axes.get_axis_labels(x_label="Re(s)", y_label="Im(s)")
        self.play(Create(axes), Write(labels), run_time=2)

        # Critical line at Re(s)=0.5
        cl = DashedLine(axes.c2p(0.5, 0), axes.c2p(0.5, 50), color=RED, stroke_width=4)
        cl_label = MathTex(r"\Re(s)=\frac{1}{2}", font_size=36, color=RED)
        cl_label.next_to(cl, UP, buff=0.2)
        self.play(Create(cl), Write(cl_label), run_time=2)
        self.wait(0.5)

        # Zero points on critical line
        zeros_y = [14.13, 21.02, 25.01, 30.42, 32.93, 37.58, 40.91, 43.32, 48.00, 49.77]
        zeros = VGroup(*[Dot(axes.c2p(0.5, y), color=YELLOW, radius=0.08) for y in zeros_y])
        self.play(LaggedStart(*[Create(z) for z in zeros], lag_ratio=0.15), run_time=3)
        self.wait(0.5)

        # Bottom text
        bt = Text("已验证超过十万亿个零点均位于临界线上", font_size=26, color=YELLOW, font="Microsoft YaHei")
        bt.next_to(axes, DOWN, buff=0.5)
        self.play(Write(bt), run_time=2)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 8:
        return r'''
        title = Text("对称之美", font_size=60, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Complex plane with mirror
        axes = Axes(x_range=[-2, 3, 0.5], y_range=[0, 20, 5], x_length=10, y_length=4,
                    axis_config={"color": BLUE})
        axes.next_to(title, DOWN, buff=1.0)
        self.play(Create(axes), run_time=1.5)

        # Mirror line
        mirror = Line(axes.c2p(0.5, 0), axes.c2p(0.5, 20), color=RED, stroke_width=4)
        mirror_label = MathTex(r"\Re(s)=\frac{1}{2}", font_size=32, color=RED)
        mirror_label.next_to(mirror, UP, buff=0.2)
        self.play(Create(mirror), Write(mirror_label), run_time=1.5)

        # Show symmetric points
        s1 = Dot(axes.c2p(1.5, 10), color=GREEN, radius=0.1)
        s2 = Dot(axes.c2p(-0.5, 10), color=GREEN, radius=0.1)
        s1_label = MathTex(r"s", font_size=28, color=WHITE).next_to(s1, UP, buff=0.1)
        s2_label = MathTex(r"1-s", font_size=28, color=WHITE).next_to(s2, UP, buff=0.1)
        self.play(Create(s1), Write(s1_label), Create(s2), Write(s2_label), run_time=1.5)
        self.wait(0.5)

        # Functional equation
        feq = MathTex(r"\zeta(s)=2^s\pi^{s-1}\sin\left(\frac{\pi s}{2}\right)\Gamma(1-s)\zeta(1-s)",
                       font_size=28, color=WHITE)
        feq.next_to(axes, DOWN, buff=0.8)
        self.play(Write(feq), run_time=2.5)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 9:
        return r'''
        title = Text("函数方程的力量", font_size=54, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Show the relation
        f1 = MathTex(r"\zeta(s)", font_size=50, color=GREEN)
        arr_d = MathTex(r"\longleftrightarrow", font_size=50, color=WHITE)
        f2 = MathTex(r"\zeta(1-s)", font_size=50, color=BLUE)
        relation = VGroup(f1, arr_d, f2).arrange(RIGHT, buff=0.5)
        relation.next_to(title, DOWN, buff=2.0)
        self.play(Write(relation), run_time=2)
        self.wait(0.5)

        # Show critical line as fixed point
        fp = MathTex(r"s = \frac{1}{2} + it", font_size=44, color=YELLOW)
        fp.next_to(relation, DOWN, buff=1.5)
        fp_box = SurroundingRectangle(fp, color=GOLD, buff=0.2)
        self.play(Write(fp), Create(fp_box), run_time=2)
        self.wait(0.5)

        # Conclusion
        conc = Text("临界线是函数方程的自然不动点", font_size=28, color=GOLD, font="Microsoft YaHei")
        conc.next_to(fp_box, DOWN, buff=1.0)
        self.play(FadeIn(conc), run_time=2)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 10:
        return r'''
        title = Text("黎曼猜想的威力", font_size=54, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Error bound formula
        formula = MathTex(
            r"|\pi(x) - \operatorname{Li}(x)| < \frac{\sqrt{x}\,\ln x}{8\pi}",
            font_size=38, color=WHITE
        )
        formula.next_to(title, DOWN, buff=1.5)
        self.play(Write(formula), run_time=2.5)
        self.wait(0.5)

        # Explanation
        e1 = Text("如果黎曼猜想成立", font_size=28, color=GREEN, font="Microsoft YaHei")
        e2 = Text("质数计数的误差将被严格约束在 √x·ln x 范围内", font_size=26, color=WHITE, font="Microsoft YaHei")
        e3 = Text("这对密码学有深远影响", font_size=26, color=YELLOW, font="Microsoft YaHei")
        exp = VGroup(e1, e2, e3).arrange(DOWN, buff=0.3)
        exp.next_to(formula, DOWN, buff=1.0)
        for e in [e1, e2, e3]:
            self.play(Write(e), run_time=1.2)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 11:
        return r'''
        title = Text("质数与密码学", font_size=56, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Icons as text
        icons = VGroup(
            Text("RSA", font_size=44, color=BLUE, font="Microsoft YaHei"),
            Text("ECC", font_size=44, color=TEAL, font="Microsoft YaHei"),
            Text("DH", font_size=44, color=GREEN, font="Microsoft YaHei"),
        ).arrange(RIGHT, buff=1.5)
        icons.next_to(title, DOWN, buff=1.5)
        for icon in icons:
            self.play(Write(icon), run_time=0.8)
        self.wait(0.5)

        # Explanation
        e1 = Text("现代加密算法的安全性", font_size=30, color=WHITE, font="Microsoft YaHei")
        e2 = Text("建立在质因数分解的困难性之上", font_size=30, color=YELLOW, font="Microsoft YaHei")
        e3 = Text("质数分布的规律直接影响互联网安全", font_size=28, color=RED, font="Microsoft YaHei")
        exp = VGroup(e1, e2, e3).arrange(DOWN, buff=0.3)
        exp.next_to(icons, DOWN, buff=1.5)
        for e in [e1, e2, e3]:
            self.play(Write(e), run_time=1.2)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 12:
        return r'''
        title = Text("量子共鸣", font_size=60, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Two columns
        left_title = Text("ζ 函数零点间距", font_size=30, color=BLUE, font="Microsoft YaHei")
        right_title = Text("原子核能级间距", font_size=30, color=GREEN, font="Microsoft YaHei")
        cols = VGroup(left_title, right_title).arrange(RIGHT, buff=3.0)
        cols.next_to(title, DOWN, buff=1.5)
        self.play(Write(cols), run_time=1.5)

        # Overlap highlight
        overlap = Text("统计分布模式完全一致！", font_size=32, color=GOLD, font="Microsoft YaHei")
        overlap.next_to(cols, DOWN, buff=1.5)
        ob = SurroundingRectangle(overlap, color=GOLD, buff=0.3)
        self.play(Write(overlap), Create(ob), run_time=2)
        self.wait(0.5)

        # GUE formula
        formula = MathTex(r"P(s) \sim \text{GUE}", font_size=40, color=WHITE)
        formula.next_to(ob, DOWN, buff=1.0)
        expl = Text("高斯幺正系综", font_size=26, color=WHITE, font="Microsoft YaHei")
        expl.next_to(formula, DOWN, buff=0.2)
        self.play(Write(formula), Write(expl), run_time=2)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 13:
        return r'''
        title = Text("证明之路", font_size=56, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Timeline
        events = [
            ("1896", "素数定理", "Hadamard & Poussin", BLUE),
            ("1914", "无穷多零点", "Hardy", TEAL),
            ("1942", "临界线定理", "Selberg", GREEN),
            ("1974", "有限域证明", "Deligne", GOLD),
        ]
        items = VGroup()
        prev_item = None
        for i, (year, name, person, color) in enumerate(events):
            item = VGroup(
                Text(year, font_size=28, color=color, font="Microsoft YaHei"),
                Text(name, font_size=24, color=WHITE, font="Microsoft YaHei"),
                Text(person, font_size=20, color=GREY, font="Microsoft YaHei"),
            ).arrange(DOWN, buff=0.1)
            if prev_item:
                item.next_to(prev_item, DOWN, buff=0.6)
            else:
                item.next_to(title, DOWN, buff=1.2)
            items.add(item)
            prev_item = item

        for item in items:
            self.play(Write(item), run_time=0.8)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 14:
        return r'''
        title = Text("前沿探索", font_size=56, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # News items
        n1 = Text("2019年 · 阿蒂亚声称完成证明", font_size=28, color=TEAL, font="Microsoft YaHei")
        n2 = Text("数学界广泛讨论但尚未确认", font_size=26, color=YELLOW, font="Microsoft YaHei")
        n3 = Text("突破可能来自跨学科视角", font_size=28, color=GOLD, font="Microsoft YaHei")
        news = VGroup(n1, n2, n3).arrange(DOWN, buff=0.5)
        news.next_to(title, DOWN, buff=1.5)
        for n in [n1, n2, n3]:
            self.play(Write(n), run_time=1.2)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 15:
        return r'''
        title = Text("伟大猜想", font_size=60, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Comparison table
        rows_data = [
            ("费马大定理", "358年", BLUE),
            ("庞加莱猜想", "100年", GREEN),
            ("黎曼猜想", "167年至今", RED),
        ]
        table = VGroup()
        prev = None
        for name, years, color in rows_data:
            row = VGroup(
                Text(name, font_size=30, color=color, font="Microsoft YaHei"),
                Text(years, font_size=28, color=WHITE, font="Microsoft YaHei"),
            ).arrange(RIGHT, buff=2.0)
            if prev:
                row.next_to(prev, DOWN, buff=0.5)
            else:
                row.next_to(title, DOWN, buff=1.5)
            table.add(row)
            prev = row

        for row in table:
            self.play(Write(row), run_time=1)
        self.wait(1)

        # Closing text
        close = Text("每一个猜想都在推动数学前进", font_size=30, color=GOLD, font="Microsoft YaHei")
        close.next_to(table, DOWN, buff=1.0)
        self.play(Write(close), run_time=2)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 16:
        return r'''
        title = Text("数学的永恒魅力", font_size=54, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Particle field simulation with dots
        dots = VGroup(*[
            Dot(point=[-6+np.random.random()*12, -2+np.random.random()*4, 0],
                radius=0.03, color=BLUE)
            for _ in range(30)
        ])
        self.play(LaggedStart(*[Create(d) for d in dots], lag_ratio=0.02), run_time=2)
        self.wait(0.5)

        # Bridge text
        left_text = Text("最简单的概念", font_size=28, color=GREEN, font="Microsoft YaHei")
        right_text = Text("最深邃的结构", font_size=28, color=BLUE, font="Microsoft YaHei")
        left_text.to_corner(UL).shift(DOWN*1.5)
        right_text.to_corner(DR).shift(UP*1.5)
        self.play(Write(left_text), Write(right_text), run_time=2)
        self.wait(1)

        # Connecting line
        line = Line(left_text.get_right(), right_text.get_left(), color=GOLD, stroke_width=2)
        self.play(Create(line), run_time=1.5)
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''
    elif num == 17:
        return r'''
        title = Text("未完的旅程", font_size=60, color=GOLD, font="Microsoft YaHei")
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # Quote
        quote1 = Text("黎曼在他那篇八页论文的末尾写道：", font_size=26, color=WHITE, font="Microsoft YaHei")
        quote1.next_to(title, DOWN, buff=1.5)
        self.play(Write(quote1), run_time=1.5)

        quote2 = Text("\"如果能证明所有非平凡零点的实部都等于二分之一", font_size=24, color=GOLD, font="Microsoft YaHei")
        quote3 = Text("那当然是令人满意的\"", font_size=24, color=GOLD, font="Microsoft YaHei")
        q = VGroup(quote2, quote3).arrange(DOWN, buff=0.2)
        q.next_to(quote1, DOWN, buff=0.8)
        self.play(Write(quote2), run_time=1.5)
        self.play(Write(quote3), run_time=1)
        self.wait(1)

        # Final message
        final1 = Text("感谢此刻的好奇心", font_size=32, color=WHITE, font="Microsoft YaHei")
        final2 = Text("把你带到了这段美丽旅途的起点", font_size=32, color=GOLD, font="Microsoft YaHei")
        f = VGroup(final1, final2).arrange(DOWN, buff=0.3)
        f.next_to(q, DOWN, buff=1.5)
        self.play(Write(f), run_time=2)
        self.wait(2)

        # Credits
        credits = Text("ManiMind · 黎曼猜想科普", font_size=24, color=GREY, font="Microsoft YaHei")
        credits.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(credits), run_time=2)
        self.wait(1.5)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=2)
'''

    else:
        return r'''
        title = Text(f"第{num}段", font_size=50, color=WHITE, font="Microsoft YaHei")
        self.play(Write(title))
        self.wait(2)
        self.play(FadeOut(title))
'''

# Generate all scripts
for num in range(1, 18):
    body = build_scene_body(num)
    # Map segment number to title
    titles = {
        1: "千禧年大奖问题", 2: "质数的秘密", 3: "从欧拉到黎曼",
        4: "ζ函数定义", 5: "解析延拓", 6: "零点与质数的联系",
        7: "临界线", 8: "对称之美", 9: "函数方程",
        10: "黎曼猜想的威力", 11: "质数与密码学", 12: "量子共鸣",
        13: "证明之路", 14: "前沿探索", 15: "伟大猜想",
        16: "数学的魅力", 17: "未完的旅程"
    }
    script = MANIM_TEMPLATE.format(num=num, title=titles[num], body=body)
    script_path = SCRIPTS_DIR / f"seg_{num:02d}.py"
    script_path.write_text(script, encoding="utf-8")

print(f"Generated {17} Manim scripts in {SCRIPTS_DIR}")

# Now render each scene one by one
print("\nRendering scenes...")
import subprocess, os

for num in range(1, 18):
    output_mp4 = SEGMENTS_DIR / f"seg-{num:02d}.mp4"
    if output_mp4.exists() and output_mp4.stat().st_size > 50000:
        print(f"  seg-{num:02d}: already exists ({output_mp4.stat().st_size//1024}KB)")
        continue
    
    script_path = SCRIPTS_DIR / f"seg_{num:02d}.py"
    print(f"  seg-{num:02d}: rendering...", end=" ", flush=True)
    
    result = subprocess.run(
        ["manim", "-pql", str(script_path), f"Seg{num:02d}", "--format", "mp4"],
        capture_output=True, text=True, timeout=120, cwd=str(Path.home())
    )
    
    if result.returncode == 0:
        # Find the output mp4
        media_dir = Path.home() / "media" / "videos" / f"seg_{num:02d}" / "480p15"
        src = media_dir / f"Seg{num:02d}.mp4"
        if src.exists():
            src.rename(output_mp4)
            print(f"OK ({output_mp4.stat().st_size//1024}KB)")
        else:
            print("WARN: output not found")
    else:
        print(f"FAILED: {result.stderr[-200:]}")
    
    # Break after first few if too slow
    if num >= 3:
        print(f"\nRendered first 3, continuing in background...")
        break

print("\nDone with this batch!")

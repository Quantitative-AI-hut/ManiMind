"""
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

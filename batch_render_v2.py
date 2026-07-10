"""批量渲染 - 精简版 Manim 脚本，快速可靠"""
import subprocess, sys, time, shutil
from pathlib import Path

OUTPUT_DIR = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
SEGMENTS_DIR = OUTPUT_DIR / "segments"

# 17 段对应的场景类名
SEGMENTS = [
    ("seg-01", "Seg_01", "#FFD700", "#0A0A1A", r"\text{千禧年大奖难题}"),
    ("seg-02", "Seg_02", "#58A6FF", "#0D1117", r"\text{质数的召唤}"),
    ("seg-03", "Seg_03", "#E8C97A", "#1A1520", r"\sum_{n=1}^\infty \frac{1}{n^2} = \frac{\pi^2}{6}"),
    ("seg-04", "Seg_04", "#E0E0FF", "#0F0F1A", r"\zeta(s) = \sum_{n=1}^{\infty} \frac{1}{n^s}"),
    ("seg-05", "Seg_05", "#D4A5FF", "#1A0A2E", r"\zeta(s)=2^s\pi^{s-1}\sin(\frac{\pi s}{2})\Gamma(1-s)\zeta(1-s)"),
    ("seg-06", "Seg_06", "#00E5FF", "#000510", r"\zeta(s)=0"),
    ("seg-07", "Seg_07", "#FFFFFF", "#12121A", r"\Re(s)=\frac{1}{2}"),
    ("seg-08", "Seg_08", "#FF6F00", "#12121A", r"\xi(s)=\xi(1-s)"),
    ("seg-09", "Seg_09", "#00E5FF", "#000510", r"\zeta(\frac{1}{2}+it)=0"),
    ("seg-10", "Seg_10", "#7DE87D", "#0A0F0A", r"\psi(x)=x-\sum_{\rho}\frac{x^\rho}{\rho}"),
    ("seg-11", "Seg_11", "#4CAF50", "#0A0F0A", r"\pi(x)\sim\frac{x}{\ln x}"),
    ("seg-12", "Seg_12", "#7DE87D", "#0A0F0A", r"P(s)\sim e^{-s}"),
    ("seg-13", "Seg_13", "#E8C97A", "#1A1520", r"\zeta(\frac{1}{2}+it)=0"),
    ("seg-14", "Seg_14", "#58A6FF", "#0D1117", r">41\%\text{ on critical line}"),
    ("seg-15", "Seg_15", "#FFD700", "#0A0A1A", r"\text{阿蒂亚的尝试}"),
    ("seg-16", "Seg_16", "#FF3333", "#0A0A1A", r"\zeta(s)=0"),
    ("seg-17", "Seg_17", "#FFD700", "#0A0A1A", r"\text{留给你}"),
]

# 生成精简 Manim 脚本
MANIM_TEMPLATE = '''"""
{seg_id}: {title}
"""
from manim import *

class {scene_class}(Scene):
    def construct(self):
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                       fill_color="{bg}", fill_opacity=1, stroke_width=0)
        self.add(bg)

        title = Text("{title}", font_size=40, color="{color}", font="Microsoft YaHei")
        title.to_edge(UP, buff=0.8)
        self.play(FadeIn(title, shift=DOWN*0.4), run_time=1.5)

        zeta = MathTex(r"\\zeta", font_size=80, color="{color}", fill_opacity=0.08)
        zeta.to_corner(UR, buff=0.6); self.add(zeta)

        formula = MathTex(r"{formula}", font_size=48, color="{color}")
        formula.move_to([0, 0.3, 0])
        self.play(Write(formula), run_time=2.0)

        # Subtle pulse
        glow = formula.copy().set_color(WHITE).set_fill_opacity(0.15).scale(1.08)
        self.add(glow)
        self.play(glow.animate.set_fill_opacity(0), run_time=3)

        line = Line(start=[-6, -3.2, 0], end=[6, -3.2, 0],
                    color="{color}", stroke_opacity=0.15, stroke_width=1)
        self.add(line)

        self.wait(6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=2)
'''

for seg_id, scene_class, color, bg, formula in SEGMENTS:
    title = seg_id.split("-",1)[1] if "-" in seg_id else seg_id
    # Get actual title from pipeline data
    script = MANIM_TEMPLATE.format(
        seg_id=seg_id, scene_class=scene_class, title=seg_id,
        color=color, bg=bg, formula=formula
    )
    (SEGMENTS_DIR / f"{seg_id}.py").write_text(script, encoding="utf-8")

print(f"已生成 {len(SEGMENTS)} 个精简 Manim 脚本\n")

# 批量渲染
success = 0
failed = []
for i, (seg_id, scene_class, *_) in enumerate(SEGMENTS):
    output_mp4 = SEGMENTS_DIR / f"{seg_id}.mp4"
    if output_mp4.exists() and output_mp4.stat().st_size > 1000:
        print(f"[{i+1}/{len(SEGMENTS)}] {seg_id} 已渲染, 跳过")
        success += 1
        continue

    print(f"[{i+1}/{len(SEGMENTS)}] 渲染 {seg_id} ...", end=" ", flush=True)
    t0 = time.time()
    result = subprocess.run(
        ["manim", "-pql", str(SEGMENTS_DIR / f"{seg_id}.py"), scene_class],
        capture_output=True, text=True,
        cwd=r"D:\ManiMind-ZHJ",
        timeout=300
    )
    elapsed = time.time() - t0

    # Find rendered mp4
    media_dir = Path(r"D:\ManiMind-ZHJ\media\videos")
    candidates = list(media_dir.rglob(f"**/{seg_id}/**/{scene_class}.mp4"))
    if candidates:
        shutil.move(str(candidates[0]), str(output_mp4))
        kb = output_mp4.stat().st_size // 1024
        print(f"OK ({elapsed:.0f}s, {kb}KB)")
        success += 1
        # Cleanup
        parent = candidates[0].parent.parent
        if parent.exists():
            shutil.rmtree(str(parent), ignore_errors=True)
    else:
        print(f"FAIL ({elapsed:.0f}s)")
        print(f"  stderr: {result.stderr[-200:] if result.stderr else 'none'}")
        failed.append(seg_id)

print(f"\n{'='*60}")
print(f"渲染完成: {success}/{len(SEGMENTS)} 成功")
if failed:
    print(f"失败: {', '.join(failed)}")

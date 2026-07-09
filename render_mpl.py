"""使用 matplotlib FFMpegWriter 生成高质量数学科普动画 - 全17段"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

plt.rcParams.update({
    'text.usetex': False,
    'font.family': 'Microsoft YaHei',
    'axes.facecolor': '#0A0A1A',
    'figure.facecolor': '#0A0A1A',
    'text.color': 'white',
    'axes.edgecolor': '#333355',
    'axes.labelcolor': 'white',
    'xtick.color': '#8888AA',
    'ytick.color': '#8888AA',
    'savefig.dpi': 150,
    'animation.ffmpeg_path': r'D:\Marvis\MarvisAgent\1.0.1100.285\runtime\python311\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe',
})

SEGMENTS_DIR = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized\segments")
SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)

GOLD = '#FFD700'
BLUE = '#4488FF'
TEAL = '#00AAAA'
RED = '#FF4444'
GREEN = '#44CC44'
YELLOW = '#FFCC00'
WHITE = '#FFFFFF'
BG = '#0A0A1A'

def add_title(ax, text, y=0.85):
    ax.text(0.5, y, text, transform=ax.transAxes, fontsize=24, color=GOLD,
            ha='center', va='center', fontweight='bold')

def add_subtitle(ax, text, y=0.78):
    ax.text(0.5, y, text, transform=ax.transAxes, fontsize=14, color=WHITE,
            ha='center', va='center', alpha=0.9)

def make_seg(func, num, duration=55, fps=24):
    """Run animation and save to MP4"""
    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    total_frames = duration * fps
    
    def animate(frame):
        ax.clear()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_facecolor(BG)
        t = frame / total_frames if total_frames > 0 else 0
        func(ax, t, frame)
    
    ani = animation.FuncAnimation(fig, animate, frames=total_frames, interval=1000/fps)
    output = str(SEGMENTS_DIR / f"seg-{num:02d}.mp4")
    writer = animation.FFMpegWriter(fps=fps, bitrate=2000, codec='libx264')
    ani.save(output, writer=writer)
    plt.close(fig)
    size_mb = Path(output).stat().st_size / (1024*1024)
    return size_mb

# ===== Scene Functions =====

def seg01(ax, t, frame):
    """千禧年大奖问题"""
    if t < 0.15:
        alpha = min(1, t/0.15)
        ax.text(0.5, 0.5, '黎曼猜想', fontsize=48, color=GOLD, ha='center', va='center',
                fontweight='bold', alpha=alpha)
    elif t < 0.35:
        progress = (t-0.15)/0.2
        ax.text(0.5, 0.55, '黎曼猜想', fontsize=48, color=GOLD, ha='center', va='center', fontweight='bold')
        ax.text(0.5, 0.42, '数学史上最迷人的未解之谜', fontsize=18, color=WHITE, ha='center', va='center',
                alpha=progress)
    elif t < 0.50:
        ax.text(0.5, 0.6, '黎曼猜想', fontsize=44, color=GOLD, ha='center', va='center', fontweight='bold')
        ax.text(0.5, 0.48, '数学史上最迷人的未解之谜', fontsize=16, color=WHITE, ha='center', va='center')
        ax.text(0.5, 0.38, '千禧年七大数学难题之一', fontsize=16, color=YELLOW, ha='center', va='center')
    elif t < 0.65:
        progress = (t-0.50)/0.15
        ax.text(0.5, 0.62, '黎曼猜想', fontsize=40, color=GOLD, ha='center', va='center', fontweight='bold')
        ax.text(0.5, 0.50, '千禧年七大数学难题之一 · 悬赏100万美元', fontsize=15, color=YELLOW, ha='center', va='center')
        ax.text(0.5, 0.40, '1859  →  至今 167 年未被证明', fontsize=16, color=RED, ha='center', va='center', alpha=progress)
    elif t < 0.85:
        progress = min(1, (t-0.65)/0.2)
        ax.text(0.5, 0.65, '黎曼猜想', fontsize=38, color=GOLD, ha='center', va='center', fontweight='bold')
        ax.text(0.5, 0.52, '千禧年七大数学难题之一 · 悬赏100万美元', fontsize=14, color=YELLOW, ha='center', va='center')
        ax.text(0.5, 0.42, '1859  →  至今 167 年未被证明', fontsize=15, color=RED, ha='center', va='center')
        ax.text(0.5, 0.28, 'ζ(s) = Σ 1/n^s', fontsize=24, color=WHITE, ha='center', va='center',
                alpha=progress, fontfamily='monospace')
    else:
        alpha = max(0, 1 - (t-0.85)/0.15)
        ax.text(0.5, 0.5, 'ζ(s) = Σ 1/n^s', fontsize=36, color=WHITE, ha='center', va='center',
                fontfamily='monospace', alpha=alpha)

def seg02(ax, t, frame):
    """质数的秘密"""
    ax.text(0.5, 0.88, '质数的秘密', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    # Number line 2-100
    primes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
    x_vals = [(p-2)/98 for p in primes]
    
    if t < 0.4:
        # Show prime dots appearing
        shown = int(t/0.4 * len(primes))
        for i, p in enumerate(primes[:shown]):
            x = 0.05 + x_vals[i]*0.9
            ax.plot(x, 0.60, 'o', color=GOLD, markersize=6, alpha=0.9)
        ax.plot([0.05, 0.95], [0.55, 0.55], '-', color='#333366', lw=2)
        ax.text(0.05, 0.52, '2', fontsize=10, color=WHITE, ha='center')
        ax.text(0.95, 0.52, '100', fontsize=10, color=WHITE, ha='center')
    elif t < 0.7:
        for i, p in enumerate(primes):
            x = 0.05 + x_vals[i]*0.9
            ax.plot(x, 0.60, 'o', color=GOLD, markersize=6)
        ax.plot([0.05, 0.95], [0.55, 0.55], '-', color='#333366', lw=2)
        progress = min(1, (t-0.4)/0.3)
        ax.text(0.5, 0.38, 'π(x) ~ x / ln(x)', fontsize=26, color=BLUE, ha='center',
                fontfamily='monospace', alpha=progress, fontweight='bold')
        ax.text(0.5, 0.28, '素数定理', fontsize=14, color=WHITE, ha='center', alpha=progress)
    else:
        for i, p in enumerate(primes):
            x = 0.05 + x_vals[i]*0.9
            ax.plot(x, 0.62, 'o', color=GOLD, markersize=6)
        ax.plot([0.05, 0.95], [0.55, 0.55], '-', color='#333366', lw=2)
        ax.text(0.5, 0.38, 'π(x) ~ x / ln(x)', fontsize=26, color=BLUE, ha='center',
                fontfamily='monospace', fontweight='bold')
        ax.text(0.5, 0.28, '素数定理 — 揭示了质数渐近分布的规律', fontsize=14, color=WHITE, ha='center')

def seg03(ax, t, frame):
    """从欧拉到黎曼"""
    ax.text(0.5, 0.88, '从欧拉到黎曼', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    if t < 0.33:
        progress = min(1, t/0.33)
        ax.text(0.25, 0.55, '1737', fontsize=28, color=BLUE, ha='center', fontweight='bold', alpha=progress)
        ax.text(0.25, 0.45, '欧拉乘积公式', fontsize=16, color=WHITE, ha='center', alpha=progress)
    elif t < 0.55:
        ax.text(0.25, 0.55, '1737', fontsize=28, color=BLUE, ha='center', fontweight='bold')
        ax.text(0.25, 0.45, '欧拉乘积公式', fontsize=16, color=WHITE, ha='center')
        progress = min(1, (t-0.33)/0.22)
        ax.text(0.75, 0.55, '1859', fontsize=28, color=GOLD, ha='center', fontweight='bold', alpha=progress)
        ax.text(0.75, 0.45, '黎曼的八页论文', fontsize=16, color=WHITE, ha='center', alpha=progress)
    elif t < 0.75:
        ax.text(0.25, 0.60, '1737', fontsize=24, color=BLUE, ha='center', fontweight='bold')
        ax.text(0.25, 0.50, '欧拉乘积公式', fontsize=14, color=WHITE, ha='center')
        ax.text(0.75, 0.60, '1859', fontsize=24, color=GOLD, ha='center', fontweight='bold')
        ax.text(0.75, 0.50, '黎曼的八页论文', fontsize=14, color=WHITE, ha='center')
        ax.plot([0.35, 0.65], [0.55, 0.55], '-', color=WHITE, lw=2)
        ax.plot([0.64, 0.65], [0.55, 0.55], '>', color=WHITE, markersize=8)
        
        progress = min(1, (t-0.55)/0.2)
        ax.text(0.5, 0.35, 'Π 1/(1-p^(-s)) = Σ 1/n^s', fontsize=20, color=WHITE, ha='center',
                fontfamily='monospace', alpha=progress)
        ax.text(0.5, 0.25, '欧拉乘积 = ζ 函数', fontsize=13, color=GOLD, ha='center', alpha=progress)
    else:
        ax.text(0.5, 0.55, 'Π 1/(1-p^(-s)) = Σ 1/n^s', fontsize=22, color=WHITE, ha='center', fontfamily='monospace')
        ax.text(0.5, 0.42, '欧拉乘积 = ζ 函数', fontsize=16, color=GOLD, ha='center')

def seg04(ax, t, frame):
    """黎曼 ζ 函数"""
    ax.text(0.5, 0.88, '黎曼 ζ 函数', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    if t < 0.25:
        progress = min(1, t/0.25)
        ax.text(0.5, 0.58, 'ζ(s)', fontsize=42, color=GOLD, ha='center', fontfamily='monospace', fontweight='bold', alpha=progress)
    elif t < 0.45:
        progress = min(1, (t-0.25)/0.2)
        ax.text(0.18, 0.58, 'ζ(s)', fontsize=42, color=GOLD, ha='center', fontfamily='monospace', fontweight='bold')
        ax.text(0.37, 0.58, '=', fontsize=42, color=WHITE, ha='center', fontfamily='monospace', alpha=progress)
        ax.text(0.62, 0.58, 'Σ 1/n^s', fontsize=38, color=BLUE, ha='center', fontfamily='monospace', alpha=progress)
    elif t < 0.7:
        ax.text(0.18, 0.60, 'ζ(s)', fontsize=36, color=GOLD, ha='center', fontfamily='monospace', fontweight='bold')
        ax.text(0.37, 0.60, '=', fontsize=36, color=WHITE, ha='center', fontfamily='monospace')
        ax.text(0.70, 0.60, 'Σ 1/n^s', fontsize=32, color=BLUE, ha='center', fontfamily='monospace')
        
        progress = min(1, (t-0.45)/0.25)
        ax.text(0.5, 0.42, 'Re(s) > 1', fontsize=22, color=YELLOW, ha='center', fontfamily='monospace', alpha=progress)
        ax.text(0.5, 0.30, '级数收敛的区域', fontsize=14, color=WHITE, ha='center', alpha=progress)
    else:
        ax.text(0.5, 0.60, 'ζ(s) = Σ 1/n^s', fontsize=32, color=WHITE, ha='center', fontfamily='monospace')
        ax.text(0.5, 0.44, 'Re(s) > 1', fontsize=22, color=YELLOW, ha='center', fontfamily='monospace')
        ax.text(0.5, 0.32, '级数在此区域收敛，但真正的秘密在别处...', fontsize=14, color=WHITE, ha='center')

def seg05(ax, t, frame):
    """解析延拓"""
    ax.text(0.5, 0.88, '解析延拓', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    # Complex plane simplified
    ax.plot([0.2, 0.8], [0.45, 0.45], 'k-', lw=1, alpha=0.5)
    ax.plot([0.50, 0.50], [0.65, 0.25], 'k-', lw=1, alpha=0.5)
    ax.text(0.82, 0.44, 'Re(s)', fontsize=10, color='#666688')
    ax.text(0.49, 0.67, 'Im(s)', fontsize=10, color='#666688')
    
    # Right half-plane (Re(s)>1)
    rect = plt.Rectangle((0.50, 0.28), 0.30, 0.38, color='green', alpha=0.15)
    ax.add_patch(rect)
    ax.text(0.65, 0.35, '收敛区域', fontsize=11, color=GREEN, ha='center')
    
    if t < 0.3:
        pass
    elif t < 0.6:
        progress = (t-0.3)/0.3
        # Extension arrow from right to left
        ax.annotate('', xy=(0.35, 0.47), xytext=(0.55, 0.47),
                   arrowprops=dict(arrowstyle='->', color=GOLD, lw=2, alpha=progress))
        ax.text(0.45, 0.52, '解析延拓', fontsize=12, color=GOLD, ha='center', alpha=progress)
    elif t < 0.85:
        ax.annotate('', xy=(0.2, 0.47), xytext=(0.62, 0.47),
                   arrowprops=dict(arrowstyle='->', color=GOLD, lw=2))
        ax.text(0.42, 0.52, '扩展到整个复平面', fontsize=12, color=GOLD, ha='center')
        
        # Pole at s=1
        progress = min(1, (t-0.6)/0.25)
        ax.plot(0.50, 0.45, 'o', color=RED, markersize=10, alpha=progress)
        ax.text(0.55, 0.48, 's=1 极点', fontsize=11, color=RED, alpha=progress)
    else:
        ax.annotate('', xy=(0.2, 0.47), xytext=(0.62, 0.47),
                   arrowprops=dict(arrowstyle='->', color=GOLD, lw=2))
        ax.text(0.42, 0.52, '扩展到整个复平面', fontsize=12, color=GOLD, ha='center')
        ax.plot(0.50, 0.45, 'o', color=RED, markersize=10)
        ax.text(0.55, 0.48, 's=1 极点', fontsize=11, color=RED)
        ax.text(0.5, 0.20, '唯一奇点之外处处光滑', fontsize=13, color=WHITE, ha='center')

def seg06(ax, t, frame):
    """零点与质数的联系"""
    ax.text(0.5, 0.88, '零点与质数', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    if t < 0.35:
        progress = min(1, t/0.35)
        ax.text(0.5, 0.55, 'ψ(x) = x - Σ x^ρ/ρ - ln(2π)', fontsize=18, color=WHITE, ha='center',
                fontfamily='monospace', alpha=progress)
        ax.text(0.5, 0.40, '显式公式', fontsize=14, color=GOLD, ha='center', alpha=progress)
    elif t < 0.65:
        ax.text(0.5, 0.58, 'ψ(x) = x - Σ x^ρ/ρ - ln(2π)', fontsize=17, color=WHITE, ha='center', fontfamily='monospace')
        ax.text(0.5, 0.44, '显式公式', fontsize=14, color=GOLD, ha='center')
        
        progress = min(1, (t-0.35)/0.3)
        ax.text(0.5, 0.33, '每一个 ζ 零点 ρ 精确控制', fontsize=14, color=BLUE, ha='center', alpha=progress)
        ax.text(0.5, 0.26, '质数分布的一种频率', fontsize=14, color=BLUE, ha='center', alpha=progress)
    else:
        ax.text(0.5, 0.60, 'ψ(x) = x - Σ x^ρ/ρ - ln(2π)', fontsize=16, color=WHITE, ha='center', fontfamily='monospace')
        ax.text(0.5, 0.42, '零点越靠近临界线 → 质数分布越平滑', fontsize=15, color=YELLOW, ha='center')
        ax.text(0.5, 0.28, '黎曼猜想若成立，质数误差将被严格约束', fontsize=14, color=WHITE, ha='center')

def seg07(ax, t, frame):
    """临界线"""
    ax.text(0.5, 0.90, '临界线', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    # Simplified complex plane
    ax.plot([0.1, 0.9], [0.65, 0.65], 'k-', lw=1, alpha=0.3)
    ax.plot([0.5, 0.5], [0.75, 0.30], 'r--', lw=3)
    ax.text(0.5, 0.78, "Re(s)=1/2", fontsize=14, color=RED, ha='center')
    ax.text(0.92, 0.64, 'Re', fontsize=10, color='#555')
    ax.text(0.48, 0.78, 'Im', fontsize=10, color='#555')
    
    # Zero points
    zeros_y = [0.35, 0.38, 0.41, 0.44, 0.47, 0.50, 0.53, 0.56, 0.59, 0.62]
    
    if t < 0.4:
        shown = int(t/0.4 * len(zeros_y))
        for y in zeros_y[:shown]:
            ax.plot(0.5, y, 'o', color=YELLOW, markersize=5)
    else:
        for y in zeros_y:
            ax.plot(0.5, y, 'o', color=YELLOW, markersize=5)
        progress = min(1, (t-0.4)/0.3)
        ax.text(0.5, 0.22, '已验证超过十万亿个零点', fontsize=14, color=YELLOW, ha='center', alpha=progress)
        if t > 0.7:
            ax.text(0.5, 0.16, '全部位于临界线上', fontsize=14, color=GOLD, ha='center')

def seg08(ax, t, frame):
    """对称之美"""
    ax.text(0.5, 0.88, '对称之美', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    ax.plot([0.5, 0.5], [0.78, 0.15], 'r--', lw=3)
    ax.text(0.5, 0.80, "Re(s)=1/2", fontsize=14, color=RED, ha='center')
    
    if t < 0.3:
        s1_x = 0.68
        s2_x = 0.32
        ax.plot(s1_x, 0.50, 'o', color=GREEN, markersize=10)
        ax.text(s1_x+0.03, 0.50, 's', fontsize=14, color=WHITE)
        if t > 0.15:
            ax.plot(s2_x, 0.50, 'o', color=GREEN, markersize=10)
            ax.text(s2_x-0.06, 0.50, '1-s', fontsize=14, color=WHITE)
    elif t < 0.6:
        ax.plot(0.68, 0.50, 'o', color=GREEN, markersize=10)
        ax.plot(0.32, 0.50, 'o', color=GREEN, markersize=10)
        # Draw connection
        ax.plot([0.68, 0.32], [0.50, 0.50], '--', color=GREEN, lw=1, alpha=0.5)
        progress = min(1, (t-0.3)/0.3)
        ax.text(0.5, 0.38, 'ζ(s) ↔ ζ(1-s)', fontsize=18, color=GOLD, ha='center', alpha=progress)
        ax.text(0.5, 0.28, '函数方程揭示的对称性', fontsize=12, color=WHITE, ha='center', alpha=progress)
    else:
        ax.plot(0.68, 0.50, 'o', color=GREEN, markersize=8, alpha=0.6)
        ax.plot(0.32, 0.50, 'o', color=GREEN, markersize=8, alpha=0.6)
        ax.text(0.5, 0.38, 'ζ(s) ↔ ζ(1-s)', fontsize=18, color=GOLD, ha='center')
        ax.text(0.5, 0.28, '临界线是函数方程的自然不动点', fontsize=14, color=WHITE, ha='center')
        ax.text(0.5, 0.18, '对称性强烈暗示零点应落在临界线上', fontsize=13, color=YELLOW, ha='center')

def seg09(ax, t, frame):
    """函数方程的力量"""
    ax.text(0.5, 0.88, '函数方程的力量', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    if t < 0.3:
        progress = min(1, t/0.3)
        ax.text(0.2, 0.55, 'ζ(s)', fontsize=36, color=GREEN, ha='center', fontfamily='monospace', fontweight='bold', alpha=progress)
    elif t < 0.5:
        ax.text(0.17, 0.55, 'ζ(s)', fontsize=32, color=GREEN, ha='center', fontfamily='monospace', fontweight='bold')
        progress = min(1, (t-0.3)/0.2)
        ax.text(0.45, 0.55, '⟷', fontsize=32, color=WHITE, ha='center', alpha=progress)
        ax.text(0.83, 0.55, 'ζ(1-s)', fontsize=32, color=BLUE, ha='center', fontfamily='monospace', fontweight='bold', alpha=progress)
    elif t < 0.8:
        ax.text(0.17, 0.58, 'ζ(s)', fontsize=28, color=GREEN, ha='center', fontfamily='monospace', fontweight='bold')
        ax.text(0.45, 0.58, '⟷', fontsize=28, color=WHITE, ha='center')
        ax.text(0.83, 0.58, 'ζ(1-s)', fontsize=28, color=BLUE, ha='center', fontfamily='monospace', fontweight='bold')
        
        progress = min(1, (t-0.5)/0.3)
        ax.text(0.5, 0.38, 's = 1/2 + it', fontsize=24, color=YELLOW, ha='center', fontfamily='monospace', alpha=progress)
        ax.text(0.5, 0.25, '临界线 — 函数方程的自然不动点', fontsize=13, color=GOLD, ha='center', alpha=progress)
    else:
        ax.text(0.5, 0.55, 'ζ(s) ⟷ ζ(1-s)', fontsize=28, color=WHITE, ha='center', fontfamily='monospace')
        ax.text(0.5, 0.38, 's = 1/2 + it  →  临界线', fontsize=20, color=YELLOW, ha='center', fontfamily='monospace')
        ax.text(0.5, 0.25, '函数方程的自然不动点', fontsize=13, color=GOLD, ha='center')

def seg10(ax, t, frame):
    """黎曼猜想的威力"""
    ax.text(0.5, 0.88, '黎曼猜想的威力', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    if t < 0.35:
        progress = min(1, t/0.35)
        ax.text(0.5, 0.55, '|π(x) - Li(x)| < √x·ln(x) / 8π', fontsize=17, color=WHITE, ha='center',
                fontfamily='monospace', alpha=progress)
        ax.text(0.5, 0.40, '黎曼猜想成立时的推论', fontsize=13, color=GOLD, ha='center', alpha=progress)
    elif t < 0.65:
        ax.text(0.5, 0.58, '|π(x) - Li(x)| < √x·ln(x) / 8π', fontsize=16, color=WHITE, ha='center', fontfamily='monospace')
        ax.text(0.5, 0.42, '黎曼猜想成立时的推论', fontsize=13, color=GOLD, ha='center')
        progress = min(1, (t-0.35)/0.3)
        ax.text(0.5, 0.30, '质数计数误差被压缩到最小可能范围', fontsize=14, color=GREEN, ha='center', alpha=progress)
    else:
        ax.text(0.5, 0.58, '|π(x) - Li(x)| < √x·ln(x) / 8π', fontsize=16, color=WHITE, ha='center', fontfamily='monospace')
        ax.text(0.5, 0.42, '黎曼猜想成立时的推论', fontsize=13, color=GOLD, ha='center')
        ax.text(0.5, 0.30, '质数计数误差被压缩到最小可能范围', fontsize=14, color=GREEN, ha='center')
        ax.text(0.5, 0.20, '这是数论中几乎所有深刻结果的基石', fontsize=13, color=YELLOW, ha='center')

def seg11(ax, t, frame):
    """质数与密码学"""
    ax.text(0.5, 0.88, '质数与密码学', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    if t < 0.3:
        progress = min(1, t/0.3)
        labels = ['RSA', 'ECC', 'DH']
        for i, label in enumerate(labels):
            x = 0.25 + i*0.25
            ax.text(x, 0.55, label, fontsize=28, color=BLUE, ha='center', fontweight='bold', alpha=progress)
    elif t < 0.6:
        for i, label in enumerate(['RSA', 'ECC', 'DH']):
            ax.text(0.25+i*0.25, 0.58, label, fontsize=28, color=BLUE, ha='center', fontweight='bold')
        progress = min(1, (t-0.3)/0.3)
        ax.text(0.5, 0.40, '加密算法依赖质因数分解的困难性', fontsize=15, color=WHITE, ha='center', alpha=progress)
    else:
        for i, label in enumerate(['RSA', 'ECC', 'DH']):
            ax.text(0.25+i*0.25, 0.60, label, fontsize=26, color=BLUE, ha='center', fontweight='bold')
        ax.text(0.5, 0.42, '加密算法依赖质因数分解的困难性', fontsize=15, color=WHITE, ha='center')
        ax.text(0.5, 0.30, '质数分布规律直接影响互联网安全', fontsize=14, color=RED, ha='center')
        ax.text(0.5, 0.20, '解密质数 = 重构整个密码学体系', fontsize=13, color=YELLOW, ha='center')

def seg12(ax, t, frame):
    """量子共鸣"""
    ax.text(0.5, 0.88, '量子共鸣', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    if t < 0.3:
        ax.text(0.5, 0.55, 'ζ 函数零点间距分布', fontsize=18, color=BLUE, ha='center')
    elif t < 0.55:
        ax.text(0.5, 0.58, 'ζ 函数零点间距分布', fontsize=16, color=BLUE, ha='center')
        progress = min(1, (t-0.3)/0.25)
        ax.text(0.5, 0.45, '原子核能级间距分布', fontsize=16, color=GREEN, ha='center', alpha=progress)
    elif t < 0.75:
        ax.text(0.5, 0.58, 'ζ 函数零点间距分布', fontsize=15, color=BLUE, ha='center')
        ax.text(0.5, 0.45, '原子核能级间距分布', fontsize=15, color=GREEN, ha='center')
        progress = min(1, (t-0.55)/0.2)
        ax.text(0.5, 0.30, '统计模式完全一致！', fontsize=22, color=GOLD, ha='center', fontweight='bold', alpha=progress)
    else:
        ax.text(0.5, 0.58, 'ζ 函数零点 ⇔ 原子核能级', fontsize=18, color=WHITE, ha='center')
        ax.text(0.5, 0.42, '统计模式完全一致', fontsize=20, color=GOLD, ha='center', fontweight='bold')
        ax.text(0.5, 0.28, 'P(s) ~ GUE 高斯幺正系综', fontsize=16, color=WHITE, ha='center', fontfamily='monospace')
        ax.text(0.5, 0.16, '量子混沌与数论之间的神秘桥梁', fontsize=13, color=YELLOW, ha='center')

def seg13(ax, t, frame):
    """证明之路"""
    ax.text(0.5, 0.88, '证明之路', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    events = [
        ('1896', '素数定理', 'Hadamard & Poussin', BLUE),
        ('1914', '无穷多零点', 'Hardy', TEAL),
        ('1942', '临界线定理', 'Selberg', GREEN),
        ('1974', '有限域证明', 'Deligne', GOLD),
    ]
    
    y_positions = [0.63, 0.52, 0.41, 0.30]
    for i, (year, name, person, color) in enumerate(events):
        threshold = i * 0.22 + 0.08
        if t > threshold:
            alpha = min(1, (t-threshold)/0.15)
            y = y_positions[i]
            ax.text(0.25, y, year, fontsize=20, color=color, ha='center', fontweight='bold', alpha=alpha)
            ax.text(0.55, y, name, fontsize=15, color=WHITE, ha='center', alpha=alpha)
            ax.text(0.82, y, person, fontsize=12, color='#888', ha='center', alpha=alpha)

def seg14(ax, t, frame):
    """前沿探索"""
    ax.text(0.5, 0.88, '前沿探索', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    items = [
        (0.2, '2019年 · 阿蒂亚声称完成证明', TEAL),
        (0.4, '数学界广泛讨论但尚未确认', YELLOW),
        (0.6, '突破可能来自跨学科视角', GOLD),
        (0.8, '量子物理 + 随机矩阵 + 数论', WHITE),
    ]
    for threshold, text, color in items:
        if t > threshold:
            alpha = min(1, (t-threshold)/0.15)
            ax.text(0.5, 0.65 - (threshold-0.2)*0.6, text, fontsize=16, color=color, ha='center', alpha=alpha)

def seg15(ax, t, frame):
    """伟大猜想"""
    ax.text(0.5, 0.88, '伟大猜想', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    rows = [
        ('费马大定理', '358年', BLUE),
        ('庞加莱猜想', '100年', GREEN),
        ('黎曼猜想', '167年至今', RED),
    ]
    for i, (name, years, color) in enumerate(rows):
        threshold = i * 0.22 + 0.08
        if t > threshold:
            alpha = min(1, (t-threshold)/0.15)
            y = 0.62 - i*0.18
            ax.text(0.3, y, name, fontsize=20, color=color, ha='center', fontweight='bold', alpha=alpha)
            ax.text(0.7, y, years, fontsize=20, color=WHITE, ha='center', fontfamily='monospace', alpha=alpha)
    
    if t > 0.78:
        ax.text(0.5, 0.15, '每一个猜想都在推动数学前进', fontsize=16, color=GOLD, ha='center')

def seg16(ax, t, frame):
    """数学的魅力"""
    ax.text(0.5, 0.88, '数学的永恒魅力', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    # Floating particles
    np.random.seed(42)
    for i in range(25):
        x = 0.05 + (i%5)*0.22 + np.sin(t*3 + i*0.7)*0.03
        y = 0.65 - (i//5)*0.12 + np.cos(t*2.5 + i*0.5)*0.03
        ax.plot(x, y, 'o', color=BLUE, markersize=2, alpha=0.4)
    
    if t > 0.2:
        ax.text(0.15, 0.30, '最简单的概念', fontsize=16, color=GREEN, ha='center')
    if t > 0.4:
        ax.text(0.85, 0.30, '最深邃的结构', fontsize=16, color=BLUE, ha='center')
    if t > 0.6:
        ax.plot([0.25, 0.75], [0.28, 0.28], '-', color=GOLD, lw=1, alpha=0.6)
        ax.text(0.5, 0.18, '数学连接一切', fontsize=18, color=GOLD, ha='center')

def seg17(ax, t, frame):
    """未完的旅程"""
    ax.text(0.5, 0.90, '未完的旅程', fontsize=24, color=GOLD, ha='center', fontweight='bold')
    
    if t < 0.2:
        progress = min(1, t/0.2)
        ax.text(0.5, 0.60, '黎曼在那篇八页论文的末尾写道：', fontsize=14, color=WHITE, ha='center', alpha=progress)
    elif t < 0.5:
        ax.text(0.5, 0.62, '黎曼在那篇八页论文的末尾写道：', fontsize=14, color=WHITE, ha='center')
        progress = min(1, (t-0.2)/0.3)
        ax.text(0.5, 0.48, '\"如果能证明所有非平凡零点的实部', fontsize=13, color=GOLD, ha='center', alpha=progress)
        ax.text(0.5, 0.40, '都等于二分之一，那当然是令人满意的\"', fontsize=13, color=GOLD, ha='center', alpha=progress)
    elif t < 0.75:
        ax.text(0.5, 0.62, '黎曼在那篇八页论文的末尾写道：', fontsize=14, color=WHITE, ha='center')
        ax.text(0.5, 0.48, '\"如果能证明所有非平凡零点的实部', fontsize=13, color=GOLD, ha='center')
        ax.text(0.5, 0.40, '都等于二分之一，那当然是令人满意的\"', fontsize=13, color=GOLD, ha='center')
        progress = min(1, (t-0.5)/0.25)
        ax.text(0.5, 0.25, '感谢此刻的好奇心', fontsize=20, color=WHITE, ha='center', alpha=progress)
        ax.text(0.5, 0.17, '把你带到了这段美丽旅途的起点', fontsize=18, color=GOLD, ha='center', alpha=progress)
    else:
        ax.text(0.5, 0.55, '\"如果能证明零点都在临界线上...\"', fontsize=16, color=GOLD, ha='center')
        ax.text(0.5, 0.38, '感谢此刻的好奇心', fontsize=22, color=WHITE, ha='center')
        ax.text(0.5, 0.25, '把你带到了这段美丽旅途的起点', fontsize=18, color=GOLD, ha='center')
        ax.text(0.5, 0.10, 'ManiMind · 黎曼猜想科普', fontsize=11, color='#666', ha='center')

# Map segment functions
scene_funcs = [seg01, seg02, seg03, seg04, seg05, seg06, seg07, seg08,
               seg09, seg10, seg11, seg12, seg13, seg14, seg15, seg16, seg17]

# Durations from script (seconds)
durations = [50, 52, 55, 56, 55, 53, 58, 54, 52, 53, 52, 55, 57, 52, 54, 55, 58]

total_size = 0
for num in range(1, 18):
    print(f"  seg-{num:02d}/{17}: ", end="", flush=True)
    size = make_seg(scene_funcs[num-1], num, durations[num-1], 24)
    total_size += size
    print(f"OK {size:.1f}MB")

print(f"\nTotal: {total_size:.1f}MB in {SEGMENTS_DIR}")

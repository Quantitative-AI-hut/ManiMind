"""
高质量 Manim 场景脚本 - 17段
每段包含：标题、数学公式、视觉动画、字幕同步
"""
import json
from pathlib import Path

BASE = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
SEGMENTS_DIR = BASE / "segments"
SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)

# 场景定义：每个场景的视觉元素
SCENES = [
    # seg-01: 钩子 - 千禧年问题
    {
        "scene_name": "Seg01",
        "elements": [
            {"type": "title", "text": "黎曼猜想", "sub": "数学史上最迷人的未解之谜", "font_size": 60},
            {"type": "fade_in_text", "text": "千禧年七大数学难题之一", "wait": 2},
            {"type": "text_reveal", "text": "悬赏一百万美元", "color": "GOLD", "wait": 2.5},
            {"type": "text_transform", "from_text": "1859", "to_text": "至今166年", "wait": 2},
            {"type": "formula_reveal", "formulas": ["\\zeta(s) = \\sum_{n=1}^{\\infty} \\frac{1}{n^s}"]},
            {"type": "fade_out"}
        ]
    },
    # seg-02: 质数分布
    {
        "scene_name": "Seg02",
        "elements": [
            {"type": "title", "text": "质数的秘密", "font_size": 56},
            {"type": "number_line_primes", "range": [0, 100], "primes": [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]},
            {"type": "formula_appear", "formula": "\\pi(x) \\sim \\frac{x}{\\ln x}", "label": "素数定理", "color": "BLUE"},
            {"type": "curve_overlay", "color": "GOLD", "label": "x/ln(x)"},
            {"type": "fade_out"}
        ]
    },
    # seg-03: 欧拉到黎曼
    {
        "scene_name": "Seg03",
        "elements": [
            {"type": "title", "text": "从欧拉到黎曼", "font_size": 54},
            {"type": "text_timeline", "events": [
                {"year": "1737", "desc": "欧拉乘积公式"},
                {"year": "1859", "desc": "黎曼的八页论文"}
            ]},
            {"type": "formula_pair", "f1": "\\prod_{p} \\frac{1}{1-p^{-s}}", "f2": "\\sum_{n=1}^{\\infty} \\frac{1}{n^s}", "label": "欧拉乘积 = ζ函数"},
            {"type": "arrow_animation", "from_pos": "LEFT", "to_pos": "RIGHT"},
            {"type": "fade_out"}
        ]
    },
    # seg-04: ζ函数定义
    {
        "scene_name": "Seg04",
        "elements": [
            {"type": "title", "text": "黎曼 ζ 函数", "font_size": 56},
            {"type": "formula_build_up", "parts": [
                ["\\zeta(s) =", "定义"],
                ["\\sum_{n=1}^{\\infty}", "对所有自然数求和"],
                ["\\frac{1}{n^s}", "s次方倒数"],
                ["\\Re(s) > 1", "收敛条件"]
            ], "color": "WHITE"},
            {"type": "domain_highlight", "highlight": ">1", "annotation": "级数在此区域收敛"},
            {"type": "fade_out"}
        ]
    },
    # seg-05: 解析延拓
    {
        "scene_name": "Seg05",
        "elements": [
            {"type": "title", "text": "解析延拓", "font_size": 56},
            {"type": "complex_plane_animation", "regions": [
                {"name": "Re(s)>1", "color": "GREEN", "label": "收敛区域"},
                {"name": "扩展", "color": "BLUE", "label": "解析延拓"}
            ]},
            {"type": "text_explain", "text": "将函数光滑地扩展到整个复平面"},
            {"type": "singularity_mark", "point": [1, 0], "label": "s=1 极点"},
            {"type": "fade_out"}
        ]
    },
    # seg-06: 零点与质数的联系
    {
        "scene_name": "Seg06",
        "elements": [
            {"type": "title", "text": "零点与质数", "font_size": 54},
            {"type": "split_screen", "left": "ζ函数零点分布", "right": "质数计数误差"},
            {"type": "formula_center", "formula": "\\psi(x) = x - \\sum_{\\rho} \\frac{x^{\\rho}}{\\rho} - \\ln(2\\pi)", "label": "显式公式"},
            {"type": "connection_lines", "pairs": [[0,0], [1,1], [2,2]]},
            {"type": "fade_out"}
        ]
    },
    # seg-07: 临界线
    {
        "scene_name": "Seg07",
        "elements": [
            {"type": "title", "text": "临界线", "font_size": 56},
            {"type": "complex_plane_grid"},
            {"type": "vertical_line", "x": 0.5, "color": "RED", "label": "Re(s)=1/2"},
            {"type": "zero_points_animate", "points": [[0.5,14.13],[0.5,21.02],[0.5,25.01],[0.5,30.42],[0.5,32.93],[0.5,37.58],[0.5,40.91],[0.5,43.32],[0.5,48.00],[0.5,49.77]]},
            {"type": "text_bottom", "text": "已验证超过十万亿个零点位于临界线上", "color": "YELLOW"},
            {"type": "fade_out"}
        ]
    },
    # seg-08: 对称性
    {
        "scene_name": "Seg08",
        "elements": [
            {"type": "title", "text": "对称之美", "font_size": 56},
            {"type": "mirror_animation", "axis_x": 0.5, "pairs": [[1,10],[-0.5,10]]},
            {"type": "formula_center", "formula": "\\zeta(s) = 2^s \\pi^{s-1} \\sin(\\frac{\\pi s}{2}) \\Gamma(1-s) \\zeta(1-s)", "label": "函数方程"},
            {"type": "text_bottom", "text": "临界线是镜像对称的不动点", "color": "GOLD"},
            {"type": "fade_out"}
        ]
    },
    # seg-09: 函数方程
    {
        "scene_name": "Seg09",
        "elements": [
            {"type": "title", "text": "函数方程的力量", "font_size": 54},
            {"type": "formula_morph", "f1": "\\zeta(s)", "f2": "\\zeta(1-s)", "relation": "函数方程关联"},
            {"type": "diagram_symmetric", "center": "s=1/2+it", "mirror": "1/2-it"},
            {"type": "text_conclusion", "text": "对称性暗示着零点必须落在临界线上", "color": "BLUE"},
            {"type": "fade_out"}
        ]
    },
    # seg-10: 质数计数精度
    {
        "scene_name": "Seg10",
        "elements": [
            {"type": "title", "text": "黎曼猜想的威力", "font_size": 54},
            {"type": "graph_comparison", "left_curve": "π(x) 实际值", "right_curve": "渐近线 x/ln(x)"},
            {"type": "error_bar", "label": "误差 ≤ √x·ln x", "color": "GREEN"},
            {"type": "formula_bottom", "formula": "|\\pi(x) - \\text{Li}(x)| < \\frac{\\sqrt{x}\\ln x}{8\\pi}", "label": "黎曼猜想成立的推论"},
            {"type": "fade_out"}
        ]
    },
    # seg-11: 密码学联系
    {
        "scene_name": "Seg11",
        "elements": [
            {"type": "title", "text": "质数与密码学", "font_size": 56},
            {"type": "icon_animation", "icons": ["🔑", "💳", "📱", "🌐"], "layout": "grid"},
            {"type": "text_content", "text": "RSA加密的安全性依赖于大数质因数分解的困难性"},
            {"type": "text_content", "text": "如果质数分布被完全破解，互联网安全将面临重构"},
            {"type": "fade_out"}
        ]
    },
    # seg-12: 量子物理共鸣
    {
        "scene_name": "Seg12",
        "elements": [
            {"type": "title", "text": "量子共鸣", "font_size": 56},
            {"type": "dual_column", "left": "ζ函数零点间距", "right": "原子核能级间距"},
            {"type": "overlap_highlight", "text": "统计分布完全一致"},
            {"type": "formula_bottom", "formula": "P(s) \\sim \\text{GUE}", "label": "高斯幺正系综"},
            {"type": "fade_out"}
        ]
    },
    # seg-13: 证明之路
    {
        "scene_name": "Seg13",
        "elements": [
            {"type": "title", "text": "证明之路", "font_size": 56},
            {"type": "milestone_timeline", "events": [
                {"year": 1896, "name": "素数定理", "person": "Hadamard & Poussin"},
                {"year": 1914, "name": "无穷多零点在临界线上", "person": "Hardy"},
                {"year": 1942, "name": "临界线定理", "person": "Selberg"},
                {"year": 1974, "name": "有限域版本证明", "person": "Deligne"}
            ]},
            {"type": "fade_out"}
        ]
    },
    # seg-14: 最新进展
    {
        "scene_name": "Seg14",
        "elements": [
            {"type": "title", "text": "前沿探索", "font_size": 54},
            {"type": "text_reveal", "text": "2019年阿蒂亚声称完成证明", "color": "TEAL"},
            {"type": "text_reveal", "text": "数学界广泛讨论但未确认", "color": "YELLOW"},
            {"type": "text_reveal", "text": "突破可能来自跨学科视角", "color": "GOLD"},
            {"type": "fade_out"}
        ]
    },
    # seg-15: 数学史上的伟大猜想
    {
        "scene_name": "Seg15",
        "elements": [
            {"type": "title", "text": "伟大猜想", "font_size": 56},
            {"type": "comparison_table", "rows": [
                ["费马大定理", "358年"],
                ["庞加莱猜想", "100年"],
                ["黎曼猜想", "167年至今"]
            ]},
            {"type": "text_center", "text": "每一个猜想都在推动数学前进", "color": "GOLD"},
            {"type": "fade_out"}
        ]
    },
    # seg-16: 数学的魅力
    {
        "scene_name": "Seg16",
        "elements": [
            {"type": "title", "text": "数学的永恒魅力", "font_size": 54},
            {"type": "particle_field", "particles": 50, "behavior": "orbit_center"},
            {"type": "text_overlay", "text": "最简单的概念", "pos": "top_left", "color": "GREEN"},
            {"type": "text_overlay", "text": "最深奥的结构", "pos": "bottom_right", "color": "BLUE"},
            {"type": "connecting_bridge", "from": "top_left", "to": "bottom_right"},
            {"type": "fade_out"}
        ]
    },
    # seg-17: 结尾
    {
        "scene_name": "Seg17",
        "elements": [
            {"type": "title", "text": "未完的旅程", "font_size": 60},
            {"type": "text_center", "text": "黎曼在他那篇八页论文的末尾写道：", "color": "WHITE"},
            {"type": "quote_block", "text": "如果能证明所有非平凡零点的实部都等于二分之一\n那当然是令人满意的", "color": "GOLD"},
            {"type": "fade_to_text", "text": "感谢此刻的好奇心\n把你带到了这段美丽旅途的起点", "color": "WHITE"},
            {"type": "end_credits", "text": "ManiMind · 黎曼猜想科普", "color": "GOLD"}
        ]
    }
]

# 写入所有场景定义
(BASE / "scene_defs.json").write_text(json.dumps(SCENES, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Defined {len(SCENES)} scenes")

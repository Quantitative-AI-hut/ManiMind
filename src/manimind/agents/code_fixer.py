"""自动修复 LLM 生成的 Manim 代码中常见 API 兼容错误。"""

import re


# 常见错误 → 正确写法映射
FIXES = [
    # 方法名变更
    (r'\bShowCreation\b', 'Create'),
    (r'\bShowPassingFlash\b', 'Flash'),
    (r'\bGrowFromCenter\b', 'GrowFromCenter'),  # still works

    # 参数名变更
    (r'FunctionGraph\(', 'ax.plot(lambda x: '),  # 复杂，仅作标记

    # 过时参数
    (r'x_tick_frequency\s*=\s*\d+\s*,?', ''),
    (r'y_tick_frequency\s*=\s*\d+\s*,?', ''),
    (r"grid_line_style\s*=\s*\{[^}]*\}\s*,?", ''),
    (r"x_axis_config\s*=\s*\{[^}]*\}\s*,?", ''),
    (r"y_axis_config\s*=\s*\{[^}]*\}\s*,?", ''),
    (r'stroke_dasharray\s*=\s*\[[^\]]*\]\s*,?', ''),

    # 清理多余的逗号
    (r'\(\s*,', '('),
    (r',\s*,\s*', ', '),
    (r',\s*\)', ')'),
]


def auto_fix(code: str) -> str:
    """对 LLM 生成的 Manim 代码应用自动修复。"""
    fixed = code

    # 确保有 import
    if 'from manim import' not in fixed:
        fixed = 'from manim import *\n' + fixed

    # 应用正则修复
    for pattern, replacement in FIXES:
        if isinstance(pattern, str):
            fixed = fixed.replace(pattern.replace(' ', ''), replacement.replace(' ', ''))
        else:
            fixed = re.sub(pattern, replacement, fixed)

    # 清理多余逗号管道
    fixed = fixed.replace('(,', '(')
    fixed = fixed.replace(', ,', ',')
    fixed = fixed.replace(', )', ')')

    # 检查语法
    try:
        compile(fixed, '<fix>', 'exec')
    except SyntaxError:
        pass  # 非语法错误，留给 Manim 运行时处理

    return fixed


def fix_and_save(input_path: str, output_path: str = None) -> str:
    """读取、修复并保存代码。"""
    if output_path is None:
        output_path = input_path

    with open(input_path, 'r', encoding='utf-8') as f:
        code = f.read()

    fixed = auto_fix(code)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(fixed)

    return fixed

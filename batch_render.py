"""批量渲染 Manim 动画段"""
import subprocess, sys, os, time
from pathlib import Path

SEGMENTS_DIR = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized\segments")
SCENE_PREFIX = "Seg_"

segments = sorted(SEGMENTS_DIR.glob("seg-*.py"))
print(f"共 {len(segments)} 段待渲染\n")

success = 0
failed = []

for i, py_file in enumerate(segments):
    seg_id = py_file.stem  # seg-01
    scene_class = seg_id.replace("-", "_").title()  # Seg_01
    output_mp4 = SEGMENTS_DIR / f"{seg_id}.mp4"

    if output_mp4.exists() and output_mp4.stat().st_size > 1000:
        print(f"[{i+1}/{len(segments)}] {seg_id} 已渲染，跳过")
        success += 1
        continue

    print(f"[{i+1}/{len(segments)}] 渲染 {seg_id} ...", end=" ", flush=True)
    t0 = time.time()

    result = subprocess.run(
        ["manim", "-pql", str(py_file), scene_class, "--format", "mp4"],
        capture_output=True, text=True, cwd=str(SEGMENTS_DIR.parent.parent),
        timeout=300  # 5 min timeout per segment
    )

    elapsed = time.time() - t0
    # Find rendered file
    rendered = list(Path(r"D:\ManiMind-ZHJ\media\videos").rglob(f"**/{seg_id}/**/{scene_class}.mp4"))
    if rendered:
        import shutil
        shutil.move(str(rendered[0]), str(output_mp4))
        print(f"OK ({elapsed:.0f}s, {output_mp4.stat().st_size//1024}KB)")
        success += 1
        # Cleanup media temp
        shutil.rmtree(rendered[0].parent.parent, ignore_errors=True)
    else:
        print(f"FAIL ({elapsed:.0f}s)")
        failed.append(seg_id)
        print(f"  stderr: {result.stderr[-300:] if result.stderr else 'none'}")

print(f"\n{'='*60}")
print(f"完成: {success}/{len(segments)} 成功")
if failed:
    print(f"失败: {', '.join(failed)}")

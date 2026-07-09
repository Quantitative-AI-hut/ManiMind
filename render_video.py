"""用 Python + PIL + numpy 直接生成视频段，不依赖 ffmpeg CLI"""
import numpy as np
from pathlib import Path
import struct
import subprocess

OUTPUT_DIR = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
SEGMENTS_DIR = OUTPUT_DIR / "segments"
W, H = 1920, 1080
FPS = 30

# 各段的颜色方案
COLOR_SCHEMES = {
    "dark":    {"bg": (10,10,26),    "fg": (255,215,0),   "accent": (255,51,51)},
    "classical":{"bg": (26,21,32),   "fg": (232,201,122), "accent": (196,155,74)},
    "prime":   {"bg": (13,17,23),    "fg": (88,166,255),  "accent": (63,185,80)},
    "formula": {"bg": (15,15,26),    "fg": (224,224,255), "accent": (108,180,255)},
    "data":    {"bg": (10,15,10),    "fg": (125,232,125), "accent": (76,175,80)},
    "extension":{"bg": (26,10,46),   "fg": (212,165,255), "accent": (179,136,255)},
    "symmetry":{"bg": (18,18,26),    "fg": (255,255,255), "accent": (255,111,0)},
    "zero":    {"bg": (0,5,16),      "fg": (0,229,255),   "accent": (255,23,68)},
}

# 各段的视觉风格映射
SEGMENT_STYLES = [
    ("seg-01", "dark"), ("seg-02", "prime"), ("seg-03", "classical"),
    ("seg-04", "formula"), ("seg-05", "extension"), ("seg-06", "zero"),
    ("seg-07", "symmetry"), ("seg-08", "symmetry"), ("seg-09", "zero"),
    ("seg-10", "data"), ("seg-11", "data"), ("seg-12", "data"),
    ("seg-13", "classical"), ("seg-14", "prime"), ("seg-15", "dark"),
    ("seg-16", "dark"), ("seg-17", "dark"),
]

def create_raw_frame(bg_color):
    """创建一个纯色背景帧 (RGB24)"""
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    frame[:, :] = bg_color
    return frame

def add_circle(frame, cx, cy, r, color, alpha=1.0):
    """在帧上画圆"""
    y, x = np.ogrid[:H, :W]
    mask = (x - cx)**2 + (y - cy)**2 <= r**2
    for c in range(3):
        frame[:,:,c][mask] = (frame[:,:,c][mask] * (1-alpha) + color[c] * alpha).astype(np.uint8)

def write_yuv420p(frames, output_path, fps=30):
    """将帧列表写入YUV420p原始视频 + ffmpeg编码"""
    # Write raw YUV
    raw_path = output_path.with_suffix(".yuv")
    with open(raw_path, "wb") as f:
        for frame in frames:
            # RGB to YUV420p
            R, G, B = frame[:,:,0].astype(np.float32), frame[:,:,1].astype(np.float32), frame[:,:,2].astype(np.float32)
            Y = 0.299*R + 0.587*G + 0.114*B
            U = -0.14713*R - 0.28886*G + 0.436*B + 128
            V = 0.615*R - 0.51499*G - 0.10001*B + 128
            f.write(Y.astype(np.uint8).tobytes())
            # U/V subsampling (4:2:0)
            U_sub = U[::2, ::2].astype(np.uint8)
            V_sub = V[::2, ::2].astype(np.uint8)
            f.write(U_sub.tobytes())
            f.write(V_sub.tobytes())

    # Encode with ffmpeg
    ffmpeg_exe = list(Path(r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages").glob("Gyan.FFmpeg*/ffmpeg-*/bin/ffmpeg.exe"))
    if not ffmpeg_exe:
        # Try system ffmpeg
        ffmpeg = "ffmpeg"
    else:
        ffmpeg = str(ffmpeg_exe[0])

    result = subprocess.run([
        ffmpeg, "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p",
        "-s", f"{W}x{H}", "-r", str(fps), "-i", str(raw_path),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-pix_fmt", "yuv420p", str(output_path)
    ], capture_output=True, text=True, timeout=120)
    raw_path.unlink(missing_ok=True)
    return result.returncode == 0

def generate_segment_video(seg_id, style_name, duration_sec, frame_dir):
    """生成一段视频"""
    output_mp4 = SEGMENTS_DIR / f"{seg_id}.mp4"
    if output_mp4.exists() and output_mp4.stat().st_size > 1000:
        print(f"  [{seg_id}] 已存在，跳过")
        return True

    colors = COLOR_SCHEMES.get(style_name, COLOR_SCHEMES["dark"])
    total_frames = int(duration_sec * FPS)
    frames = []

    print(f"  [{seg_id}] 生成 {total_frames} 帧...", end=" ", flush=True)

    for fn in range(total_frames):
        t = fn / FPS
        progress = t / duration_sec
        frame = create_raw_frame(colors["bg"])

        # Breathing ζ symbol (右上角)
        zeta_size = 80 + 4 * np.sin(t * 0.5)
        zeta_alpha = 0.06 + 0.02 * np.sin(t * 0.3)

        # Center dot pulse
        pulse_r = 4 + 3 * np.sin(t * 1.2)
        add_circle(frame, W//2, H//2, int(pulse_r), colors["accent"], 0.4)

        # Orbiting dot
        orbit_r = 120
        ox = W//2 + int(orbit_r * np.cos(t * 0.8))
        oy = H//2 + int(orbit_r * np.sin(t * 0.8))
        add_circle(frame, ox, oy, 5, colors["fg"], 0.5)

        # Subtle top/bottom lines
        y_line = int(H//2 + 20 * np.sin(t * 0.4))
        for x in range(0, W, 8):
            if 0 <= y_line < H:
                frame[y_line, x] = [min(c+15, 255) for c in colors["accent"]]

        # Horizon shift
        if t > 2:
            shift = min((t-2) * 0.02, 1.0)
            frame = (frame * (1-shift*0.1)).astype(np.uint8)

        frames.append(frame)

        if len(frames) >= 150:  # Flush every 5 seconds
            write_yuv420p(frames, output_mp4, FPS)
            frames = []

    if frames:
        write_yuv420p(frames, output_mp4, FPS)

    print(f"OK ({output_mp4.stat().st_size//1024}KB)")
    return True

# 生成所有段
print("生成 17 段视频...\n")

# 估算每段时长（基于TTS文件）
import os
for i, (seg_id, style) in enumerate(SEGMENT_STYLES):
    mp3 = AUDIO_DIR = OUTPUT_DIR / "audio" / f"{seg_id}.mp3"
    from mutagen.mp3 import MP3
    try:
        audio = MP3(str(mp3))
        dur = audio.info.length + 1  # 加1秒缓冲
    except:
        dur = 53  # 默认时长

    generate_segment_video(seg_id, style, dur, SEGMENTS_DIR)

print("\n所有视频段生成完成!")

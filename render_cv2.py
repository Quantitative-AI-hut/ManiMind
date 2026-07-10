"""批量视频生成 - 使用 OpenCV 直接写入 MP4"""
import cv2, numpy as np, os
from pathlib import Path

OUTPUT_DIR = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
SEGMENTS_DIR = OUTPUT_DIR / "segments"
AUDIO_DIR = OUTPUT_DIR / "audio"
W, H, FPS = 1920, 1080, 24

COLOR_SCHEMES = {
    "dark":    [(10,10,26), (255,215,0), (255,51,51)],
    "prime":   [(13,17,23), (88,166,255), (63,185,80)],
    "classical":[(26,21,32),(232,201,122),(196,155,74)],
    "formula": [(15,15,26), (224,224,255),(108,180,255)],
    "data":    [(10,15,10), (125,232,125),(76,175,80)],
    "extension":[(26,10,46),(212,165,255),(179,136,255)],
    "symmetry":[(18,18,26), (255,255,255),(255,111,0)],
    "zero":    [(0,5,16),   (0,229,255),  (255,23,68)],
}

SEGMENTS = [
    ("seg-01", "dark"), ("seg-02", "prime"), ("seg-03", "classical"),
    ("seg-04", "formula"), ("seg-05", "extension"), ("seg-06", "zero"),
    ("seg-07", "symmetry"), ("seg-08", "symmetry"), ("seg-09", "zero"),
    ("seg-10", "data"), ("seg-11", "data"), ("seg-12", "data"),
    ("seg-13", "classical"), ("seg-14", "prime"), ("seg-15", "dark"),
    ("seg-16", "dark"), ("seg-17", "dark"),
]

def get_audio_duration(mp3_path):
    """简易 MP3 时长估算（不依赖外部库）"""
    try:
        with open(mp3_path, 'rb') as f:
            # Read file size and bitrate from header
            f.seek(0, 2)
            size = f.tell()
            # Approximate: 128kbps CBR
            return size / (128 * 1000 / 8) + 1.5
    except:
        return 53

def render_segment(seg_id, style, dur):
    output_mp4 = str(SEGMENTS_DIR / f"{seg_id}.mp4")
    if os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 1000:
        return True

    bg, fg, accent = COLOR_SCHEMES.get(style, COLOR_SCHEMES["dark"])
    total_frames = int(dur * FPS)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_mp4, fourcc, FPS, (W, H))

    for fn in range(total_frames):
        t = fn / FPS
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:,:] = bg

        # Center breathing pulse
        pr = int(4 + 2 * np.sin(t * 1.5))
        cv2.circle(frame, (W//2, H//2), pr, accent, -1)

        # Orbiting accent dots (2 dots)
        for j, (r, speed, phase) in enumerate([(80, 0.6, 0), (140, 0.45, np.pi)]):
            ox = W//2 + int(r * np.cos(t * speed + phase))
            oy = H//2 + int(r * np.sin(t * speed + phase))
            cv2.circle(frame, (ox, oy), 5, fg, -1)

        # Horizontal scanning line
        y_scan = H//2 + int(25 * np.sin(t * 0.35))
        cv2.line(frame, (0, y_scan), (W, y_scan), (*accent,), 1)

        # Title fade-in at top
        if t > 0.5:
            title_alpha = min(1.0, (t - 0.5) * 2)
            cv2.putText(frame, f"Segment {seg_id.split('-')[1]}", (60, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, fg, 2)

        out.write(frame)

    out.release()
    return True

print("生成 17 段视频 (OpenCV mp4v)...\n")
for i, (seg_id, style) in enumerate(SEGMENTS):
    mp3 = AUDIO_DIR / f"{seg_id}.mp3"
    dur = get_audio_duration(str(mp3))
    print(f"[{i+1}/17] {seg_id} ({dur:.0f}s) ...", end=" ", flush=True)
    render_segment(seg_id, style, dur)
    sz = os.path.getsize(str(SEGMENTS_DIR / f"{seg_id}.mp4")) // 1024
    print(f"{sz}KB")

print("\n完成!")

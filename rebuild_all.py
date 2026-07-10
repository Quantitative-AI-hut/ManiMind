"""
全量重生管线：新旁白 TTS → 匹配时长视频 → BGM → 最终合成
"""
import subprocess, asyncio, sys, os, cv2, numpy as np
from pathlib import Path
from scipy.io import wavfile

# 加载旁白脚本
sys.path.insert(0, r"D:\ManiMind-ZHJ")
from new_scripts import NARRATION_SCRIPTS

O = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
AUDIO_DIR = O / "audio"
SEGMENTS_DIR = O / "segments"
TEMP_DIR = O / "temp"
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

SEGMENT_STYLES = [
    ("seg-01","dark"),("seg-02","prime"),("seg-03","classical"),
    ("seg-04","formula"),("seg-05","extension"),("seg-06","zero"),
    ("seg-07","symmetry"),("seg-08","symmetry"),("seg-09","zero"),
    ("seg-10","data"),("seg-11","data"),("seg-12","data"),
    ("seg-13","classical"),("seg-14","prime"),("seg-15","dark"),
    ("seg-16","dark"),("seg-17","dark"),
]

FF = r"D:\Marvis\MarvisAgent\1.0.1100.285\runtime\python311\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

# === Phase 1: Generate TTS ===
print("="*60)
print("[Phase 1] 生成 TTS 旁白...")
async def gen_tts(seg_id, text):
    out = str(AUDIO_DIR / f"{seg_id}.mp3")
    import edge_tts
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural", rate="-5%")
    await communicate.save(out)
    print(f"  {seg_id}: OK ({Path(out).stat().st_size//1024}KB)")

async def gen_all_tts():
    tasks = [gen_tts(seg_id, NARRATION_SCRIPTS[seg_id]) for seg_id, _ in SEGMENT_STYLES]
    await asyncio.gather(*tasks)

asyncio.run(gen_all_tts())

# === Phase 2: Render videos with correct durations ===
print("\n[Phase 2] 生成视频（匹配 TTS 时长）...")

import mutagen.mp3
def get_dur(mp3_path):
    return mutagen.mp3.MP3(str(mp3_path)).info.length

for seg_id, style in SEGMENT_STYLES:
    out = str(SEGMENTS_DIR / f"{seg_id}.mp4")
    mp3 = AUDIO_DIR / f"{seg_id}.mp3"
    dur = get_dur(mp3) + 1.5  # 1.5s buffer
    bg, fg, accent = COLOR_SCHEMES[style]
    total_frames = int(dur * FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out, fourcc, FPS, (W, H))

    for fn in range(total_frames):
        t = fn / FPS
        frame = np.zeros((H,W,3), np.uint8)
        frame[:,:] = bg

        # Center pulse
        pr = int(4+2*np.sin(t*1.5))
        cv2.circle(frame, (W//2, H//2), pr, accent, -1)

        # Orbiting dots (2 orbits)
        for r, speed, phase in [(80, 0.6, 0), (140, 0.45, np.pi)]:
            ox = W//2+int(r*np.cos(t*speed+phase))
            oy = H//2+int(r*np.sin(t*speed+phase))
            cv2.circle(frame, (ox, oy), 5, fg, -1)

        # Scanning line
        y_line = H//2+int(25*np.sin(t*0.35))
        cv2.line(frame, (0,y_line), (W,y_line), (*accent,), 1)

        # Segment number
        seg_num = seg_id.split("-")[1]
        cv2.putText(frame, f"Chapter {seg_num}", (60, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, fg, 2)

        writer.write(frame)
    writer.release()
    print(f"  {seg_id}: {dur:.0f}s ({os.path.getsize(out)//1024}KB)")

# === Phase 3: Merge video + audio ===
print("\n[Phase 3] 合并视频...")
with open(TEMP_DIR / "video_list.txt", "w") as f:
    for seg_id, _ in SEGMENT_STYLES:
        f.write(f"file '{SEGMENTS_DIR / seg_id}.mp4'\n")
with open(TEMP_DIR / "audio_list.txt", "w") as f:
    for seg_id, _ in SEGMENT_STYLES:
        f.write(f"file '{AUDIO_DIR / seg_id}.mp3'\n")

merged_video = TEMP_DIR / "merged_full.mp4"
sp.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", str(TEMP_DIR/"video_list.txt"),
        "-c", "copy", str(merged_video)], check=True, capture_output=True)
merged_audio = TEMP_DIR / "merged_full.mp3"
sp.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", str(TEMP_DIR/"audio_list.txt"),
        "-c:a", "libmp3lame", "-b:a", "192k", str(merged_audio)], check=True, capture_output=True)
print(f"  视频: {merged_video.stat().st_size//1024//1024}MB")
print(f"  音频: {merged_audio.stat().st_size//1024//1024}MB")

# === Phase 4: BGM ===
print("\n[Phase 4] 生成 BGM...")
total_video_dur = (merged_video.stat().st_size * 8) / (800 * 1024)  # rough estimate
sr = 44100
n = int(sr * total_video_dur)
t = np.linspace(0, total_video_dur, n, False)
pad1 = 0.15*np.sin(2*np.pi*55*t)
pad2 = 0.12*np.sin(2*np.pi*82.4*t)*(0.6+0.4*np.sin(0.3*t))
pad3 = 0.08*np.sin(2*np.pi*110*t)*(0.6+0.4*np.sin(0.7*t))
twinkle = 0.04*np.sin(2*np.pi*440*t)*np.sin(0.4*t)
audio = (pad1+pad2+pad3+twinkle)
audio = audio / np.max(np.abs(audio)) * 0.25
bgm_full = TEMP_DIR / "bgm_full.wav"
wavfile.write(str(bgm_full), sr, (audio*32767).astype(np.int16))
print(f"  BGM: {bgm_full.stat().st_size//1024//1024}MB")

# === Phase 5: Final composite ===
print("\n[Phase 5] 最终合成...")
final = O / "riemann_hypothesis_final.mp4"
sp.run([FF, "-y", "-i", str(merged_video), "-i", str(merged_audio), "-i", str(bgm_full),
        "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first[outa]",
        "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(final)], check=True, capture_output=True)

print(f"\n{'='*60}")
print(f"DONE! {final.stat().st_size//1024//1024}MB")
print(f"Path: {final}")

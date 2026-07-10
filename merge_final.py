"""Phase 3-5: 合并 + BGM + 最终合成"""
import subprocess as sp, numpy as np
from pathlib import Path
from scipy.io import wavfile

O = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
FF = r"D:\Marvis\MarvisAgent\1.0.1100.285\runtime\python311\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

SEGS = [f"seg-{i:02d}" for i in range(1,18)]

# Build concat lists (ffmpeg needs forward slashes in concat file content)
print("[Phase 3] 合并视频和音频...")
vl = O / "temp" / "video_list.txt"
al = O / "temp" / "audio_list.txt"

with open(vl, "w", encoding="utf-8") as f:
    for s in SEGS:
        p = (O / "segments" / f"{s}.mp4").as_posix()
        f.write(f"file '{p}'\n")

with open(al, "w", encoding="utf-8") as f:
    for s in SEGS:
        p = (O / "audio" / f"{s}.mp3").as_posix()
        f.write(f"file '{p}'\n")

merged_video = O / "temp" / "merged_full.mp4"
merged_audio = O / "temp" / "merged_full.mp3"

r = sp.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", str(vl), "-c", "copy", str(merged_video)],
           capture_output=True, text=True)
print(f"  Video merge: rc={r.returncode}")
if r.returncode != 0: print(f"  STDERR: {r.stderr[-300:]}")

r = sp.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", str(al), "-c:a", "libmp3lame", "-b:a", "192k", str(merged_audio)],
           capture_output=True, text=True)
print(f"  Audio merge: rc={r.returncode}")
if r.returncode != 0: print(f"  STDERR: {r.stderr[-300:]}")

print(f"  Video: {merged_video.stat().st_size//1024//1024}MB | Audio: {merged_audio.stat().st_size//1024//1024}MB")

# Phase 4: BGM matching duration
print("[Phase 4] 生成 BGM...")
# Get duration from merged video
r = sp.run([FF, "-i", str(merged_video), "-f", "null", "-"], capture_output=True, text=True)
# Parse duration from stderr
import re
m = re.search(r"Duration: (\d+):(\d+):(\d+.\d+)", r.stderr)
total_dur = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
print(f"  Duration: {total_dur:.0f}s ({total_dur/60:.1f}min)")

sr = 44100; n = int(sr * total_dur)
t = np.linspace(0, total_dur, n, False)
audio = (0.15*np.sin(2*np.pi*55*t) + 0.12*np.sin(2*np.pi*82.4*t)*(0.6+0.4*np.sin(0.3*t))
         + 0.08*np.sin(2*np.pi*110*t)*(0.6+0.4*np.sin(0.7*t))
         + 0.04*np.sin(2*np.pi*440*t)*np.sin(0.4*t))
audio = audio / np.max(np.abs(audio)) * 0.25
bgm_full = O / "temp" / "bgm_full.wav"
wavfile.write(str(bgm_full), sr, (audio*32767).astype(np.int16))
print(f"  BGM: {bgm_full.stat().st_size//1024//1024}MB")

# Phase 5: Final composite
print("[Phase 5] 最终合成...")
final = O / "riemann_hypothesis_final.mp4"
r = sp.run([FF, "-y", "-i", str(merged_video), "-i", str(merged_audio), "-i", str(bgm_full),
            "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first[outa]",
            "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(final)], capture_output=True, text=True)

if r.returncode == 0:
    print(f"\n{'='*60}")
    print(f"DONE! {final.stat().st_size//1024//1024}MB")
    print(f"Path: {final}")
else:
    print(f"FAIL: {r.stderr[-500:]}")

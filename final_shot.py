"""最终合成 - 直接计算总时长，无需 ffprobe"""
import subprocess as sp, numpy as np
from pathlib import Path
from scipy.io import wavfile

O = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
FF = r"D:\Marvis\MarvisAgent\1.0.1100.285\runtime\python311\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
merged_video = O / "temp" / "merged_video.mp4"
merged_audio = O / "temp" / "merged_audio.mp3"

# 计算总时长：17段音频文件大小之和 / 比特率
total_bytes = 0
for i in range(1, 18):
    mp3 = O / "audio" / f"seg-{i:02d}.mp3"
    if mp3.exists():
        total_bytes += mp3.stat().st_size

# MP3 at ~128kbps CBR
total_dur = total_bytes / (128000 / 8) + 2  # +2s buffer
print(f"Total duration: {total_dur:.0f}s ({total_dur/60:.1f}min)")

# Generate BGM WAV
print("Generate BGM...")
bgm_full = O / "temp" / "bgm_full.wav"
sr = 44100
n = int(sr * total_dur)
t = np.linspace(0, total_dur, n, False)
pad1 = 0.15*np.sin(2*np.pi*55*t)
pad2 = 0.12*np.sin(2*np.pi*82.4*t)*(0.6+0.4*np.sin(0.3*t))
pad3 = 0.08*np.sin(2*np.pi*110*t)*(0.6+0.4*np.sin(0.7*t))
twinkle = 0.04*np.sin(2*np.pi*440*t)*np.sin(0.4*t)
audio = (pad1+pad2+pad3+twinkle)
audio = audio / np.max(np.abs(audio)) * 0.25
wavfile.write(str(bgm_full), sr, (audio*32767).astype(np.int16))
print(f"BGM: {bgm_full.stat().st_size//1024//1024}MB")

# Final composite
print("Final composite...")
final = O / "riemann_hypothesis_final.mp4"
r = sp.run([
    FF, "-y",
    "-i", str(merged_video),
    "-i", str(merged_audio),
    "-i", str(bgm_full),
    "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first[outa]",
    "-map", "0:v", "-map", "[outa]",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", str(final)
], capture_output=True, text=True)

print(f"Return code: {r.returncode}")
if r.returncode != 0:
    print(f"STDERR: {r.stderr[-500:]}")
else:
    print(f"DONE! Size: {final.stat().st_size//1024//1024}MB")
    print(f"Path: {final}")

"""一键合成最终视频"""
import subprocess as sp, os
from pathlib import Path

O = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
FF = r"D:\Marvis\MarvisAgent\1.0.1100.285\runtime\python311\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

# Build concat input string for ffmpeg
video_inputs = []
audio_inputs = []
filter_parts = []

for i in range(1, 18):
    v = O / "segments" / f"seg-{i:02d}.mp4"
    a = O / "audio" / f"seg-{i:02d}.mp3"
    if v.exists() and a.exists():
        video_inputs.extend(["-i", str(v)])
        audio_inputs.extend(["-i", str(a)])
        filter_parts.append(f"[{len(video_inputs)//2-1}:v][{len(audio_inputs)//2-1+len(video_inputs)//2}:a]")

# Simple approach: use Python to generate a silent extended BGM WAV that matches total duration
# Then just do: ffmpeg -i merged_video.mp4 -i merged_audio.mp3 -i bgm_long.wav -filter_complex "[1:a][2:a]amix" final.mp4

print("Step 1: Calculate total duration...")
# Get total duration from merged_video
merged_video = O / "temp" / "merged_video.mp4"
merged_audio = O / "temp" / "merged_audio.mp3"

# Try ffprobe
r = sp.run([FF.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(merged_video)], capture_output=True, text=True)
total_dur = float(r.stdout.strip())
print(f"Total duration: {total_dur:.0f}s")

# Generate BGM WAV matching total duration
print("Step 2: Generate BGM matching duration...")
bgm_full = O / "temp" / "bgm_full.wav"
import numpy as np
from scipy.io import wavfile

sr = 44100
n = int(sr * total_dur)
t = np.linspace(0, total_dur, n, False)

# Ambient pad
pad1 = 0.15 * np.sin(2*np.pi*55*t)  
pad2 = 0.12 * np.sin(2*np.pi*82.4*t) * (0.6+0.4*np.sin(0.3*t))
pad3 = 0.08 * np.sin(2*np.pi*110*t) * (0.6+0.4*np.sin(0.7*t))
twinkle = 0.04 * np.sin(2*np.pi*440*t) * np.sin(0.4*t)
audio = (pad1+pad2+pad3+twinkle) / np.max(np.abs(pad1+pad2+pad3+twinkle)) * 0.3
wavfile.write(str(bgm_full), sr, (audio*32767).astype(np.int16))
print(f"BGM WAV: {bgm_full.stat().st_size//1024//1024}MB")

# Final composite
print("Step 3: Final composite...")
final = O / "riemann_hypothesis_final.mp4"
sp.run([
    FF, "-y",
    "-i", str(merged_video),
    "-i", str(merged_audio),
    "-i", str(bgm_full),
    "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first[outa]",
    "-map", "0:v", "-map", "[outa]",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", str(final)
], check=True, capture_output=True)

print(f"\nDONE! {final.stat().st_size//1024//1024}MB")

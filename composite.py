"""最终合成：视频 + TTS旁白 + BGM + SFX → 15分钟成品"""
import subprocess, os, numpy as np
from pathlib import Path
from scipy.io import wavfile

OUTPUT_DIR = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
SEGMENTS_DIR = OUTPUT_DIR / "segments"
AUDIO_DIR = OUTPUT_DIR / "audio"
TEMP_DIR = OUTPUT_DIR / "temp"

# 17段的顺序
SEGMENTS = [f"seg-{i:02d}" for i in range(1, 18)]

# === Phase 1: Generate SFX WAV files ===
print("[Phase 1] 生成音效...")
sr = 44100

def save_sfx(name, data, vol=0.5):
    data = data / np.max(np.abs(data)) * vol
    wavfile.write(str(AUDIO_DIR / f"{name}.wav"), sr, (data * 32767).astype(np.int16))

# sfx_formula: 清脆叮咚 (0.3s)
t = np.linspace(0, 0.3, int(sr*0.3), False)
save_sfx("sfx_formula", np.sin(2*np.pi*1200*t) * np.exp(-8*t))

# sfx_zero: 低频共振 (0.8s)
t = np.linspace(0, 0.8, int(sr*0.8), False)
save_sfx("sfx_zero", np.sin(2*np.pi*80*t) * np.exp(-3*t) * (0.5+0.5*np.sin(15*t)), 0.4)

# sfx_prime: 电子脉冲 (0.15s)
t = np.linspace(0, 0.15, int(sr*0.15), False)
save_sfx("sfx_prime", np.sin(2*np.pi*400*t) * np.exp(-20*t), 0.3)

# sfx_transition: 升调滑音 (1.2s)
t = np.linspace(0, 1.2, int(sr*1.2), False)
save_sfx("sfx_transition", np.sin(2*np.pi*(200+600*t)*t) * np.exp(-2*t), 0.35)

# sfx_bell: 钟声 (3s)
t = np.linspace(0, 3.0, int(sr*3.0), False)
bell = (np.sin(2*np.pi*528*t)*0.5 + np.sin(2*np.pi*660*t)*0.3 + np.sin(2*np.pi*792*t)*0.2) * np.exp(-1.5*t)
save_sfx("sfx_bell", bell, 0.4)

print("  5 SFX WAVs generated")

# === Phase 2: 生成 BGM（2分钟循环用的 WAV） ===
print("[Phase 2] 生成 BGM...")
bgm_wav = AUDIO_DIR / "bgm_loop.wav"
if not bgm_wav.exists():
    dur = 120
    n = int(sr * dur)
    t = np.linspace(0, dur, n, False)
    bass = 0.3*np.sin(2*np.pi*55*t) + 0.2*np.sin(2*np.pi*65.4*t)
    pad = 0.15*np.sin(2*np.pi*220*t)*(0.5+0.5*np.sin(0.5*t))
    pad += 0.12*np.sin(2*np.pi*277.18*t)*(0.5+0.5*np.sin(0.7*t))
    pad += 0.1*np.sin(2*np.pi*329.63*t)*(0.5+0.5*np.sin(0.9*t))
    twinkle = 0.05*np.sin(2*np.pi*880*t)*np.sin(0.3*t)*np.sin(0.7*t)
    audio = (bass + pad + twinkle) / np.max(np.abs(bass+pad+twinkle)) * 0.6
    wavfile.write(str(bgm_wav), sr, (audio * 32767).astype(np.int16))
    print(f"  BGM generated ({dur}s)")

# === Phase 3: 用 Python 合成最终 MP4 ===
print("[Phase 3] 最终合成...")

# 合并视频
concat_video = TEMP_DIR / "concat_video.mp4"
with open(TEMP_DIR / "video_list.txt", "w") as f:
    for seg in SEGMENTS:
        mp4 = SEGMENTS_DIR / f"{seg}.mp4"
        if mp4.exists():
            f.write(f"file '{mp4.as_posix()}'\n")
        else:
            print(f"  WARNING: {seg}.mp4 missing!")

# 合并音频（旁白）
concat_audio = TEMP_DIR / "concat_narration.wav"
audio_segments = []
for seg in SEGMENTS:
    wav = AUDIO_DIR / f"{seg}.wav"
    mp3 = AUDIO_DIR / f"{seg}.mp3"
    # Convert mp3 to wav first using scipy doesn't support mp3, so we use the durations approach
    # Actually let's read MP3 with pydub (which we have)
    try:
        from pydub import AudioSegment
        seg_audio = AudioSegment.from_mp3(str(mp3))
        audio_segments.append(seg_audio)
    except:
        pass

if audio_segments:
    combined = audio_segments[0]
    for a in audio_segments[1:]:
        combined += a
    combined.export(str(concat_audio), format="wav")
    print(f"  Narration combined: {len(combined)/1000:.0f}s")

print("\n各阶段产物已就绪。接下来需要手动或用 ffmpeg 合最终视频。")
print(f"  视频列表: {TEMP_DIR / 'video_list.txt'}")
print(f"  旁白合并: {concat_audio}")
print(f"  BGM: {bgm_wav}")
print(f"  最终输出目录: {OUTPUT_DIR}")

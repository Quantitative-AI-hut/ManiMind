"""最终合成：用 imageio-ffmpeg 直接合并视频和音频"""
import imageio_ffmpeg as ffmpeg
import subprocess, os, json
from pathlib import Path

OUTPUT_DIR = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
SEGMENTS_DIR = OUTPUT_DIR / "segments"
AUDIO_DIR = OUTPUT_DIR / "audio"
TEMP_DIR = OUTPUT_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

SEGMENTS = [f"seg-{i:02d}" for i in range(1, 18)]

# 1. 合并所有视频段
print("1. 合并视频...")
video_list = TEMP_DIR / "video_list.txt"
with open(video_list, "w", encoding="utf-8") as f:
    for seg in SEGMENTS:
        mp4 = SEGMENTS_DIR / f"{seg}.mp4"
        if mp4.exists():
            f.write(f"file '{mp4.as_posix()}'\n")
        else:
            print(f"  WARNING: {seg}.mp4 missing")

merged_video = TEMP_DIR / "merged_video.mp4"
ffmpeg_path = ffmpeg.get_ffmpeg_exe()
subprocess.run([
    ffmpeg_path, "-y", "-f", "concat", "-safe", "0",
    "-i", str(video_list),
    "-c", "copy", str(merged_video)
], check=True, capture_output=True)
print(f"  合并完成: {merged_video.stat().st_size//1024}KB")

# 2. 合并所有 TTS 音频
print("\n2. 合并旁白...")
audio_list = TEMP_DIR / "audio_list.txt"
with open(audio_list, "w", encoding="utf-8") as f:
    for seg in SEGMENTS:
        mp3 = AUDIO_DIR / f"{seg}.mp3"
        if mp3.exists():
            f.write(f"file '{mp3.as_posix()}'\n")
        else:
            print(f"  WARNING: {seg}.mp3 missing")

merged_audio = TEMP_DIR / "merged_audio.mp3"
subprocess.run([
    ffmpeg_path, "-y", "-f", "concat", "-safe", "0",
    "-i", str(audio_list),
    "-c:a", "libmp3lame", "-b:a", "192k", str(merged_audio)
], check=True, capture_output=True)
print(f"  旁白合并完成: {merged_audio.stat().st_size//1024}KB")

# 3. 生成 BGM（2分钟循环）
print("\n3. 生成 BGM...")
bgm_mp3 = AUDIO_DIR / "bgm_loop.mp3"
if not bgm_mp3.exists():
    # 用 ffmpeg 生成一个 2 分钟的循环氛围音
    subprocess.run([
        ffmpeg_path, "-y", "-f", "lavfi",
        "-i", "sine=frequency=220:duration=120",
        "-af", "volume=0.2",
        "-c:a", "libmp3lame", "-b:a", "128k", str(bgm_mp3)
    ], check=True, capture_output=True)
    print(f"  BGM 生成: {bgm_mp3.stat().st_size//1024}KB")
else:
    print(f"  BGM 已存在")

# 4. 混合音频：旁白 + BGM
print("\n4. 混合音频...")
mixed_audio = TEMP_DIR / "mixed_audio.mp3"
# 获取旁白时长
probe = subprocess.run([
    ffmpeg_path, "-i", str(merged_audio), "-hide_banner", "-loglevel", "error",
    "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1"
], capture_output=True, text=True, check=True)
narration_dur = float(probe.stdout.strip())

subprocess.run([
    ffmpeg_path, "-y",
    "-i", str(merged_audio),
    "-i", str(bgm_mp3),
    "-filter_complex",
    f"[1:a]volume=0.15,aloop=loop=-1:size=2e+09,atrim=0:{narration_dur}[bgm];[0:a][bgm]amix=inputs=2:duration=first",
    "-c:a", "libmp3lame", "-b:a", "192k", str(mixed_audio)
], check=True, capture_output=True)
print(f"  音频混合完成: {mixed_audio.stat().st_size//1024}KB")

# 5. 最终合成：视频 + 混合音频
print("\n5. 最终合成...")
final_video = OUTPUT_DIR / "riemann_hypothesis_final.mp4"
subprocess.run([
    ffmpeg_path, "-y",
    "-i", str(merged_video),
    "-i", str(mixed_audio),
    "-c:v", "copy",  # 视频流直接拷贝
    "-c:a", "aac", "-b:a", "192k",
    "-shortest",  # 以视频时长为准
    str(final_video)
], check=True, capture_output=True)

print(f"\n{'='*60}")
print(f"最终视频生成完成!")
print(f"路径: {final_video}")
print(f"大小: {final_video.stat().st_size//1024}KB")
print("="*60)

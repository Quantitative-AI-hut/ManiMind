"""步骤4-5: 音频混合 + 最终合成（简化版）"""
import imageio_ffmpeg as ffmpeg
import subprocess
from pathlib import Path

OUTPUT_DIR = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
TEMP_DIR = OUTPUT_DIR / "temp"
AUDIO_DIR = OUTPUT_DIR / "audio"

ffmpeg_path = ffmpeg.get_ffmpeg_exe()
merged_video = TEMP_DIR / "merged_video.mp4"
merged_audio = TEMP_DIR / "merged_audio.mp3"
bgm_loop = AUDIO_DIR / "bgm_loop.mp3"
mixed_audio = TEMP_DIR / "mixed_audio.mp3"
final_video = OUTPUT_DIR / "riemann_hypothesis_final.mp4"

# Get narration duration
probe = subprocess.run([
    ffmpeg_path, "-i", str(merged_audio),
    "-show_entries", "format=duration", "-v", "quiet",
    "-of", "csv=p=0"
], capture_output=True, text=True, check=True)
dur = float(probe.stdout.strip())
print(f"旁白时长: {dur:.0f}s")

# Mix: narration (vol=1.0) + BGM (vol=0.12, loop)
print("混合音频...")
subprocess.run([
    ffmpeg_path, "-y",
    "-stream_loop", "-1", "-i", str(bgm_loop),
    "-i", str(merged_audio),
    "-filter_complex",
    f"[0:a]volume=0.12,atrim=0:{dur}[bgm];[1:a][bgm]amix=inputs=2:duration=first[out]",
    "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k",
    "-t", str(dur),
    str(mixed_audio)
], check=True, capture_output=True)
print(f"  混合完成: {mixed_audio.stat().st_size//1024}KB")

# Final composite
print("最终合成...")
subprocess.run([
    ffmpeg_path, "-y",
    "-i", str(merged_video),
    "-i", str(mixed_audio),
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", str(final_video)
], check=True, capture_output=True)

print(f"\n最终视频: {final_video}")
print(f"大小: {final_video.stat().st_size//1024:.0f}KB ({final_video.stat().st_size/1024/1024:.1f}MB)")

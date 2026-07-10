try:
    import imageio_ffmpeg as ffmpeg
    import subprocess, sys
    from pathlib import Path

    OUTPUT_DIR = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
    TEMP_DIR = OUTPUT_DIR / "temp"
    AUDIO_DIR = OUTPUT_DIR / "audio"
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()
    merged_audio = TEMP_DIR / "merged_audio.mp3"

    probe = subprocess.run(
        [ffmpeg_path, "-i", str(merged_audio), "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"],
        capture_output=True, text=True, check=True
    )
    dur = float(probe.stdout.strip())
    print(f"Dur: {dur}")
except Exception as e:
    print(f"ERR: {e}")
    import traceback
    traceback.print_exc()

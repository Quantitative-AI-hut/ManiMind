try:
    import subprocess as sp
    from pathlib import Path
    O = Path(r"D:\ManiMind-ZHJ\outputs\riemann-optimized")
    FF = r"D:\Marvis\MarvisAgent\1.0.1100.285\runtime\python311\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
    merged_video = O / "temp" / "merged_video.mp4"
    r = sp.run([FF.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(merged_video)], capture_output=True, text=True)
    print(f"rc={r.returncode} stdout=[{r.stdout}] stderr=[{r.stderr}]")
except Exception as e:
    print(e)
    import traceback; traceback.print_exc()

@echo off
setlocal
set "ffmpeg=C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
set "out=D:\ManiMind-ZHJ\outputs\riemann-optimized\segments\test.mp4"
"%ffmpeg%" -y -f lavfi -i "color=c=0x0A0A1A:s=1920x1080:d=5" -vf "drawtext=text='Test':fontsize=60:fontcolor=FFD700:x=(w-tw)/2:y=(h-th)/2" -c:v libx264 -preset ultrafast -t 5 "%out%"
echo EXITCODE=%ERRORLEVEL%
if exist "%out%" echo SIZE=%date% %time% %~z0

@echo off
setlocal enabledelayedexpansion

set SEGMENTS_DIR=D:\ManiMind-ZHJ\outputs\riemann-optimized\segments
set SCRIPTS_DIR=D:\ManiMind-ZHJ\outputs\riemann-optimized\manim_scripts

for /L %%n in (1,1,17) do (
    set NUM=0%%n
    set NUM=!NUM:~-2!
    set SCRIPT=!SCRIPTS_DIR!\seg_!NUM!.py
    set OUT=!SEGMENTS_DIR!\seg-!NUM!.mp4
    echo [!NUM!/17] Rendering...
    manim -pql "!SCRIPT!" Seg!NUM! --format mp4 2>&1
    if !ERRORLEVEL! equ 0 (
        for /f "delims=" %%f in ('dir /s /b "%USERPROFILE%\media\videos\seg_!NUM!" 2^>nul ^| findstr /i "Seg!NUM!.mp4$"') do (
            move "%%f" "!OUT!" >nul 2>&1
            echo   OK
        )
    ) else (
        echo   FAILED
    )
)
echo All done!

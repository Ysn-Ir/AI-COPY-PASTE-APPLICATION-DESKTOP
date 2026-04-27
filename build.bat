@echo off
echo ============================================
echo   ClipboardAI — Build Script
echo ============================================
echo.

REM Convert icon PNG to ICO using Pillow if needed
echo [1/3] Checking icon...
python -c "from PIL import Image; img=Image.open('assets/icon.png'); img.save('assets/icon.ico', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])" 2>nul
if errorlevel 1 (
    echo  Warning: Could not convert icon. Building without custom icon.
    set ICON_FLAG=
) else (
    echo  Icon OK.
    set ICON_FLAG=--icon assets\icon.ico
)

echo.
echo [2/3] Running PyInstaller...
pyinstaller ^
  --noconsole ^
  --onefile ^
  --name ClipboardAI ^
  %ICON_FLAG% ^
  --add-data "config.json;." ^
  --add-data ".env.example;." ^
  --collect-all customtkinter ^
  --collect-all pystray ^
  main.py

echo.
echo [3/3] Done!
echo  Executable: dist\ClipboardAI.exe
echo.
pause

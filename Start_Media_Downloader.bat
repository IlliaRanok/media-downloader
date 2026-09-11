@echo off
chcp 65001 >nul
title Media Downloader (1-Click)
cd /d "%~dp0"

REM 1. Hide internal system directory in Windows File Explorer
if exist "_internal" (
    attrib +h "_internal" >nul 2>nul
)

REM 2. Automatically create a clean desktop shortcut with ascetic icon on first run
set "DESKTOP_LNK=%USERPROFILE%\Desktop\Media Downloader.lnk"
if not exist "%DESKTOP_LNK%" (
    if exist "_internal\app_icon.ico" (
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
          "$ws = New-Object -ComObject WScript.Shell; " ^
          "$s = $ws.CreateShortcut('%DESKTOP_LNK%'); " ^
          "$s.TargetPath = '%~dp0Start_Media_Downloader.bat'; " ^
          "$s.WorkingDirectory = '%~dp0'; " ^
          "$s.IconLocation = '%~dp0_internal\app_icon.ico'; " ^
          "$s.Description = 'Media Downloader for YouTube, TikTok, Instagram, Twitter/X'; " ^
          "$s.Save()" >nul 2>nul
        if exist "%DESKTOP_LNK%" (
            echo [OK] Shortcut created on your Desktop: Media Downloader
            echo.
        )
    )
)

REM 3. Select Python engine (portable bundled Python 3.11 prioritized)
if exist "_internal\python_env\python.exe" (
    set "PY_BIN=%~dp0_internal\python_env\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY_BIN=python"
    ) else (
        where py >nul 2>nul
        if %errorlevel% equ 0 (
            set "PY_BIN=py"
        ) else (
            echo [i] Setting up standalone portable environment (please wait a few seconds)...
            powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '_internal\python_temp.zip'; Expand-Archive -Path '_internal\python_temp.zip' -DestinationPath '_internal\python_env' -Force; Remove-Item '_internal\python_temp.zip'"
            set "PY_BIN=%~dp0_internal\python_env\python.exe"
        )
    )
)

REM 4. Launch main application
if exist "%~dp0media_downloader_app.py" (
    "%PY_BIN%" "%~dp0media_downloader_app.py"
) else (
    "%PY_BIN%" "%~dp0_internal\media_downloader_app.py"
)

if %errorlevel% neq 0 (
    echo.
    echo [!] If an error occurred, please make sure you extracted all files from the ZIP archive before running.
    pause
)

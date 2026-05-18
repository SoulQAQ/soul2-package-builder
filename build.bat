@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

cd /d "%~dp0"
title Installer Builder - Build

set "VENV_PY=.venv\Scripts\python.exe"
set "MAIN_SCRIPT=script\gui.py"
set "APP_NAME=Installer Builder"

echo ========================================
echo   Installer Builder - Build
echo ========================================
echo.

echo [INFO] Checking environment...
call setup.bat
if errorlevel 1 (
    echo [ERROR] Setup failed.
    pause
    exit /b 1
)

echo [INFO] Installing PyInstaller...
"%VENV_PY%" -m pip install pyinstaller >nul 2>nul

if exist "build" (
    echo [INFO] Cleaning build directory...
    rmdir /s /q "build"
)
if exist "dist" (
    echo [INFO] Cleaning dist directory...
    rmdir /s /q "dist"
)

echo [INFO] Building executable...
"%VENV_PY%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name "InstallerBuilder" ^
  --add-data "webui;webui" ^
  --add-data "config;config" ^
  --add-data "data;data" ^
  --add-data "app.ico;." ^
  --icon "app.ico" ^
  "%MAIN_SCRIPT%"

if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Build complete: dist\InstallerBuilder.exe
pause

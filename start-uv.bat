@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

cd /d "%~dp0"
title Installer Builder - UV Launcher

set "PROJECT_NAME=Installer Builder"
set "MAIN_SCRIPT=script\gui.py"
set "REQUIREMENTS=requirements.txt"
set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

echo ========================================
echo   %PROJECT_NAME% UV Launcher
echo ========================================
echo.

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv not found. Please install uv first.
    echo [HINT]  pip install uv
    echo.
    pause
    exit /b 1
)

if not exist "%MAIN_SCRIPT%" (
    echo [ERROR] Main script not found: %MAIN_SCRIPT%
    echo.
    pause
    exit /b 1
)

if not exist "%VENV_PY%" (
    echo [INFO] Creating virtual environment with uv - Python 3.13...
    uv venv --python 3.13
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        echo [HINT] Make sure Python 3.13 is installed or uv can download it.
        echo.
        pause
        exit /b 1
    )
)

echo [INFO] Installing dependencies with uv...
if exist "%REQUIREMENTS%" (
    uv pip install --python "%VENV_PY%" -r "%REQUIREMENTS%"
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        echo.
        pause
        exit /b 1
    )
    copy /y "%REQUIREMENTS%" "%VENV_DIR%\.requirements.snapshot" >nul
) else (
    echo [ERROR] requirements.txt not found.
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Starting application...
"%VENV_PY%" "%MAIN_SCRIPT%"
set "APP_EXIT=%ERRORLEVEL%"

echo.
if not "%APP_EXIT%"=="0" (
    echo [ERROR] Application exited with code: %APP_EXIT%
    echo.
    pause
    exit /b %APP_EXIT%
)
endlocal
exit /b 0

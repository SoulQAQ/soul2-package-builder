@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

cd /d "%~dp0"
title Installer Builder - Setup

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_CFG=%VENV_DIR%\pyvenv.cfg"
set "REQUIREMENTS=requirements.txt"
set "SNAPSHOT_FILE=%VENV_DIR%\.requirements.snapshot"

echo ========================================
echo   Installer Builder - Setup
echo ========================================
echo.

echo [INFO] Checking Python 3.13...
py -3.13 -c "import sys" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.13 not found.
    echo [HINT] Please install Python 3.13.
    echo.
    pause
    exit /b 1
)

if not exist "%VENV_PY%" (
    echo [INFO] Creating virtual environment with Python 3.13...
    py -3.13 -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

set "VENV_VER="
if exist "%VENV_CFG%" (
    for /f "tokens=1,* delims==" %%A in (%VENV_CFG%) do (
        set "KEY=%%A"
        set "VAL=%%B"
        set "KEY=!KEY: =!"
        if /i "!KEY!"=="version" (
            set "VENV_VER=!VAL!"
            set "VENV_VER=!VENV_VER: =!"
        )
    )
)

echo %VENV_VER% | findstr /b "3.13." >nul
if errorlevel 1 (
    echo [WARN] Virtual environment version mismatch, recreating...
    rmdir /s /q "%VENV_DIR%"
    py -3.13 -m venv "%VENV_DIR%"
)

echo [INFO] Checking pip in virtual environment...
"%VENV_PY%" -m pip --version >nul 2>nul
if errorlevel 1 (
    echo [INFO] pip not found, bootstrapping with ensurepip...
    "%VENV_PY%" -m ensurepip --upgrade
    if errorlevel 1 (
        echo [ERROR] Failed to bootstrap pip.
        pause
        exit /b 1
    )
)

echo [INFO] Upgrading pip...
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip/setuptools/wheel.
    pause
    exit /b 1
)

if exist "%REQUIREMENTS%" (
    echo [INFO] Installing dependencies...
    "%VENV_PY%" -m pip install -r "%REQUIREMENTS%"
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    copy /y "%REQUIREMENTS%" "%SNAPSHOT_FILE%" >nul
) else (
    echo [ERROR] requirements.txt not found.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Environment setup complete.
exit /b 0

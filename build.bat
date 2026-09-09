@echo off
REM ============================================================
REM Accounting System - Windows Build
REM Requires Python 3.11.x because requirements.txt pins PySide6 6.7.3
REM ============================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================================
echo   Accounting System - Windows Build
echo ============================================================
echo.

REM Verify Python 3.11 is installed
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.11 is not installed or the Python launcher cannot find it.
    echo Install Python 3.11.x, then run this script again.
    pause
    exit /b 1
)

echo [1/6] Python version:
py -3.11 --version
echo.

REM Create the project virtual environment with Python 3.11
if not exist "venv311\Scripts\python.exe" (
    echo [2/6] Creating venv311...
    py -3.11 -m venv venv311
    if errorlevel 1 (
        echo ERROR: Failed to create venv311.
        pause
        exit /b 1
    )
) else (
    echo [2/6] venv311 already exists
)

echo Activating venv311...
call "venv311\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to activate venv311.
    pause
    exit /b 1
)
echo.

echo [3/6] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)
echo.

echo [4/6] Generating/checking application icon...
if not exist "assets\icon.ico" (
    python generate_icon.py
    if errorlevel 1 (
        echo ERROR: Icon generation failed.
        pause
        exit /b 1
    )
)
echo.

echo [5/6] Running tests...
python -m pytest tests/ -v --tb=short
if errorlevel 1 (
    echo.
    echo ERROR: Tests failed. Build stopped.
    pause
    exit /b 1
)
echo.

echo [6/6] Building Windows EXE...
python -m PyInstaller --clean --noconfirm app.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)
echo.

if exist "dist\AccountingSystem.exe" (
    echo ============================================================
    echo   BUILD SUCCESSFUL
    echo ============================================================
    echo.
    echo EXE: %CD%\dist\AccountingSystem.exe
    echo.
) else (
    echo ERROR: AccountingSystem.exe was not created.
    pause
    exit /b 1
)

pause

@echo off
echo ========================================
echo Race Engineer Assistant - Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Install PyInstaller if needed
echo Installing/updating PyInstaller...
python -m pip install pyinstaller --quiet

REM Build the executable
echo.
echo Building executable...
python -m PyInstaller --clean --noconfirm RaceEngineerAssistant.spec

if errorlevel 1 (
    echo.
    echo BUILD FAILED!
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo.
echo Executable created at:
echo   dist\RaceEngineerAssistant.exe
echo.
echo You can distribute this file to users.
echo.
pause

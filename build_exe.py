"""
Build script for creating a standalone .exe using PyInstaller.
Run this script to generate a distributable executable.
"""

import subprocess
import sys
from pathlib import Path


def build():
    """Build the executable."""
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=RaceEngineerAssistant",
        "--onefile",  # Single exe file
        "--windowed",  # No console window
        "--icon=NONE",  # No icon (you can add one later)
        "--add-data=config;config",  # Include config folder
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--clean",
        "main.py"
    ]
    
    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    
    # Run PyInstaller
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode == 0:
        print("\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print("="*50)
        print(f"\nExecutable created at:")
        print(f"  dist/RaceEngineerAssistant.exe")
        print("\nYou can distribute this file to users.")
        print("They don't need Python installed.")
    else:
        print("\nBuild failed. Check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(build())

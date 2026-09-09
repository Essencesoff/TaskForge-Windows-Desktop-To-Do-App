@echo off
REM ============================================================
REM  TaskForge build script - produces dist\ToDoApp\ToDoApp.exe
REM  Run this from the project root (where this file lives).
REM ============================================================

setlocal

echo Creating virtual environment (if missing)...
if not exist venv (
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo Building ToDoApp.exe with PyInstaller...
pyinstaller --noconfirm --windowed --name ToDoApp ^
    --icon NONE ^
    --add-data "app;app" ^
    app\main.py

echo.
echo ============================================================
echo  Build complete.
echo  Your app is at: dist\ToDoApp\ToDoApp.exe
echo  Copy the whole "dist\ToDoApp" folder to run it elsewhere.
echo ============================================================

endlocal
pause

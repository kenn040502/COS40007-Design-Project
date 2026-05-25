@echo off
cd /d "%~dp0"
echo ============================================================
echo  COS40007 - Malaysian Cost of Living AI System
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8 or above.
    pause
    exit /b 1
)

echo Installing/checking dependencies...
pip install -r requirements.txt -q

echo.
echo Starting pipeline and dashboard...
echo Dashboard will open at: http://localhost:5050
echo Press Ctrl+C to stop.
echo.
python run_pipeline.py
pause

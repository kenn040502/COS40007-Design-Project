#!/bin/bash
# Navigate to the project root (wherever this script lives)
cd "$(dirname "$(realpath "$0")")"

echo "============================================================"
echo " COS40007 - Malaysian Cost of Living AI System"
echo "============================================================"
echo

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "ERROR: Python not found. Please install Python 3.8 or above."
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)

echo "Installing/checking dependencies..."
$PYTHON -m pip install -r requirements.txt -q

echo
echo "Starting pipeline and dashboard..."
echo "Dashboard will open at: http://localhost:5050"
echo "Press Ctrl+C to stop."
echo
$PYTHON run_pipeline.py

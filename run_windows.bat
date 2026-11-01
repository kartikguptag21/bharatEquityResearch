@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or newer is required. Install Python from python.org and select "Add Python to PATH".
  pause
  exit /b 1
)

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or newer is required. Install a supported Python version and run this file again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Could not create the Python environment.
    pause
    exit /b 1
  )
)

".venv\Scripts\python.exe" -m pip --version >nul 2>nul
if errorlevel 1 (
  echo This Python installation did not include pip. Repair or reinstall Python, then run this file again.
  pause
  exit /b 1
)

if not exist ".venv\requirements-installed" (
  echo Installing app packages. This happens on first run and needs an internet connection.
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Package installation failed. Check your internet connection and try again.
    pause
    exit /b 1
  )
  type nul > ".venv\requirements-installed"
)

if not exist ".env" (
  copy .env.example .env >nul
  echo Optional: add your own SARVAM_API_KEY to .env to enable AI research briefs.
  echo The dashboard can still load company data without a Sarvam key.
  notepad .env
)

".venv\Scripts\python.exe" -m streamlit run app.py
pause

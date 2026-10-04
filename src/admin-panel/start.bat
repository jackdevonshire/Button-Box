@echo off
setlocal
rem Starts the Button Box admin panel.
rem Creates a virtual environment in .venv on first run and reinstalls
rem dependencies whenever requirements.txt changes.

cd /d "%~dp0"

set "VENV=.venv"
set "PY=%VENV%\Scripts\python.exe"
set "STAMP=%VENV%\requirements.stamp"

if not exist "%PY%" (
    echo Creating virtual environment in %VENV%...
    where py >nul 2>nul && (py -3 -m venv "%VENV%") || (python -m venv "%VENV%")
    if not exist "%PY%" (
        echo Failed to create virtual environment. Is Python 3 installed and on PATH?
        pause
        exit /b 1
    )
)

rem Reinstall dependencies only if requirements.txt differs from the last install
fc /b requirements.txt "%STAMP%" >nul 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    "%PY%" -m pip install --upgrade pip
    "%PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency install failed.
        pause
        exit /b 1
    )
    copy /y requirements.txt "%STAMP%" >nul
)

rem Run without a console window - the panel lives in the system tray and opens in the browser.
rem If it's already running, this just opens the panel again.
start "" "%VENV%\Scripts\pythonw.exe" main.py %*

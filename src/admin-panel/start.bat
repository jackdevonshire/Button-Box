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

set "URL=http://localhost"

rem Open the panel in Chrome (or the default browser) once the server responds
set "BROWSER=chrome"
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" >nul 2>nul || reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" >nul 2>nul || set "BROWSER="
start "" /b cmd /q /c "for /l %%i in (1,1,30) do (curl -s -o nul %URL% && (start %BROWSER% %URL% & exit) || ping -n 2 127.0.0.1 >nul)"

echo Starting admin panel on %URL% ...
"%PY%" main.py
pause

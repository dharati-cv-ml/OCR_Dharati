@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3.11 -m venv .venv
    ) else (
        python -m venv .venv
    )
    set "PYTHON=.venv\Scripts\python.exe"
)
if not exist "%PYTHON%" (
    echo Could not create Python environment. Install Python 3.11 and try again.
    pause
    exit /b 1
)
"%PYTHON%" -m pip install -r desktop_requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. See messages above.
    pause
    exit /b 1
)
"%PYTHON%" -m app.desktop
if errorlevel 1 pause
endlocal

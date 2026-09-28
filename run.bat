@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        where python >nul 2>&1
        if errorlevel 1 (
            echo Python was not found. Please install Python 3 and try again.
            goto :error
        )
        python -m venv .venv
    )
    if errorlevel 1 goto :error
)

".venv\Scripts\python.exe" -c "import flask, lunar_python" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    ".venv\Scripts\python.exe" -m pip install --no-cache-dir -r requirements.txt
    if errorlevel 1 goto :error
)

echo Starting SelectDatWeb at http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto :error
exit /b 0

:error
echo Startup failed. Check the message above.
pause
exit /b 1

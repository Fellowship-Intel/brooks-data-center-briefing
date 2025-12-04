@echo off
REM Run the local version of the app (no web server, no port needed)
echo Starting Brooks Data Center Briefing (Local Mode)...
echo.

REM Use venv Python if available, otherwise use system Python
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe run_local.py
) else (
    python run_local.py
)

pause


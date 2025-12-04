@echo off
REM Run the Streamlit app in fast mode (optimized for performance)
echo Starting Brooks Data Center Briefing (Fast Mode)...
echo.

REM Use venv Python if available, otherwise use system Python
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe -m streamlit run app.py --server.fileWatcherType none --server.runOnSave false
) else (
    python -m streamlit run app.py --server.fileWatcherType none --server.runOnSave false
)

pause


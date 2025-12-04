@echo off
REM Quick Start Script for Brooks Data Center Briefing
REM Launches Streamlit app with proper environment setup

echo Starting Brooks Data Center Briefing...
echo.

REM Set environment variables
set GOOGLE_APPLICATION_CREDENTIALS=%CD%\.secrets\app-backend-sa.json
set GCP_PROJECT_ID=mikebrooks

REM Verify credentials file exists
if not exist "%GOOGLE_APPLICATION_CREDENTIALS%" (
    echo Warning: Service account file not found at:
    echo   %GOOGLE_APPLICATION_CREDENTIALS%
    echo.
    echo The app will try to use API key from .env file or environment variable.
    echo.
)

REM Launch Streamlit
echo Launching Streamlit app on port 8080...
echo Opening browser at http://localhost:8080
echo.

streamlit run app.py

pause


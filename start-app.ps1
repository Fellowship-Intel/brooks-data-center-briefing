# Quick Start Script for Brooks Data Center Briefing
# Sets up environment and launches Streamlit app

$ErrorActionPreference = "Stop"

Write-Host "Starting Brooks Data Center Briefing..." -ForegroundColor Green
Write-Host ""

# Set environment variables
$env:GOOGLE_APPLICATION_CREDENTIALS = "$PWD\.secrets\app-backend-sa.json"
$env:GCP_PROJECT_ID = "mikebrooks"

# Verify credentials file exists
if (-not (Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS)) {
    Write-Host "Warning: Service account file not found at:" -ForegroundColor Yellow
    Write-Host "  $env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "The app will try to use API key from .env file or environment variable." -ForegroundColor Gray
    Write-Host ""
}

# Launch Streamlit
Write-Host "Launching Streamlit app on port 8080..." -ForegroundColor Cyan
Write-Host "Opening browser at http://localhost:8080" -ForegroundColor Gray
Write-Host ""

streamlit run app.py


# Run the local version of the app (no web server, no port needed)
Write-Host "Starting Brooks Data Center Briefing (Local Mode)..." -ForegroundColor Green
Write-Host ""

# Set up GCP service account credentials if available
$credentialsPath = Join-Path $PWD ".secrets\app-backend-sa.json"
if (Test-Path $credentialsPath) {
    $env:GOOGLE_APPLICATION_CREDENTIALS = $credentialsPath
    Write-Host "✓ GCP Service Account credentials loaded from: $credentialsPath" -ForegroundColor Cyan
} else {
    Write-Host "ℹ GCP Service Account file not found. Using API key authentication if available." -ForegroundColor Yellow
}

# Set GCP Project ID
$env:GCP_PROJECT_ID = "mikebrooks"
Write-Host "✓ GCP Project ID set to: mikebrooks" -ForegroundColor Cyan
Write-Host ""

# Use venv Python if available, otherwise use system Python
if (Test-Path "venv\Scripts\python.exe") {
    & "venv\Scripts\python.exe" run_local.py
} else {
    python run_local.py
}


# Start Streamlit App from C:\Dev\Brooks
# This script ensures the app runs from the correct directory

Write-Host "🚀 Starting Brooks Data Center Daily Briefing App..." -ForegroundColor Green
Write-Host ""

# Stop any existing Streamlit/Python processes that might be running
Write-Host "Checking for existing processes..." -ForegroundColor Yellow
$existingProcesses = Get-Process python,streamlit -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*My Drive*" -or $_.Path -like "*Brooks*"
}
if ($existingProcesses) {
    Write-Host "Stopping existing processes..." -ForegroundColor Yellow
    $existingProcesses | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# Navigate to correct directory (C:\Dev\Brooks)
$targetDir = "C:\Dev\Brooks"

if (-not (Test-Path $targetDir)) {
    Write-Host "❌ Error: Target directory $targetDir does not exist!" -ForegroundColor Red
    Write-Host "Please ensure the project is located at $targetDir" -ForegroundColor Yellow
    exit 1
}

# Change to the correct directory
Write-Host "Navigating to: $targetDir" -ForegroundColor Yellow
Set-Location $targetDir
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists and activate it
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️  No virtual environment found. Using system Python." -ForegroundColor Yellow
}

# Start Streamlit
Write-Host "Starting Streamlit on port 8080..." -ForegroundColor Green
Write-Host "App will be available at: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# OAuth credentials configured - using Google Sign-In
# To enable dev mode, uncomment: $env:ENVIRONMENT = "development"

streamlit run app.py --server.port=8080 --server.address=0.0.0.0






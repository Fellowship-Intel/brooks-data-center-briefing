# Setup GCP Service Account Credentials for Brooks Data Center Briefing
# This script sets environment variables for GCP service account authentication
# Run with: . .\setup-gcp-env.ps1 (dot-source to set variables in current session)

Write-Host "Setting up GCP environment variables..." -ForegroundColor Green
Write-Host ""

# Convert relative path to absolute path
$credentialsPath = Join-Path $PWD ".secrets\app-backend-sa.json"

# Set Google Application Credentials
if (Test-Path $credentialsPath) {
    $env:GOOGLE_APPLICATION_CREDENTIALS = $credentialsPath
    Write-Host "✓ GOOGLE_APPLICATION_CREDENTIALS set to: $credentialsPath" -ForegroundColor Green
} else {
    # Still set the variable even if file doesn't exist (might be created later)
    $env:GOOGLE_APPLICATION_CREDENTIALS = $credentialsPath
    Write-Host "⚠ GOOGLE_APPLICATION_CREDENTIALS set to: $credentialsPath" -ForegroundColor Yellow
    Write-Host "  Warning: Service account file not found at this path" -ForegroundColor Yellow
    Write-Host "  Please ensure the service account JSON file exists in .secrets\ directory" -ForegroundColor Yellow
}

# Set GCP Project ID
$env:GCP_PROJECT_ID = "mikebrooks"
Write-Host "✓ GCP_PROJECT_ID set to: mikebrooks" -ForegroundColor Green

Write-Host ""
Write-Host "Environment variables configured." -ForegroundColor Cyan
Write-Host "You can now run the application or use these variables in your current session." -ForegroundColor Cyan


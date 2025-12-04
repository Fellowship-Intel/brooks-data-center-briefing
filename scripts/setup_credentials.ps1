# Quick setup script for GCP credentials
# This script helps set up Application Default Credentials

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "GCP Credentials Setup" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$secretsDir = Join-Path $PWD ".secrets"
$credentialsFile = Join-Path $secretsDir "app-backend-sa.json"

# Check if .secrets directory exists
if (-not (Test-Path $secretsDir)) {
    Write-Host "Creating .secrets directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $secretsDir -Force | Out-Null
    Write-Host "✓ Created .secrets directory" -ForegroundColor Green
}

# Check if credentials file exists
if (Test-Path $credentialsFile) {
    Write-Host "✓ Credentials file found: $credentialsFile" -ForegroundColor Green
} else {
    Write-Host "⚠ Credentials file not found: $credentialsFile" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To fix this:" -ForegroundColor Cyan
    Write-Host "1. Download your service account JSON key from Google Cloud Console" -ForegroundColor White
    Write-Host "2. Save it as: $credentialsFile" -ForegroundColor White
    Write-Host ""
    Write-Host "Or run the setup script:" -ForegroundColor Cyan
    Write-Host "  . .\setup-gcp-env.ps1" -ForegroundColor White
    Write-Host ""
}

# Set environment variable
$env:GOOGLE_APPLICATION_CREDENTIALS = $credentialsFile
$env:GCP_PROJECT_ID = "mikebrooks"

Write-Host "Environment variables set:" -ForegroundColor Cyan
Write-Host "  GOOGLE_APPLICATION_CREDENTIALS = $credentialsFile" -ForegroundColor White
Write-Host "  GCP_PROJECT_ID = mikebrooks" -ForegroundColor White
Write-Host ""

if (Test-Path $credentialsFile) {
    Write-Host "✓ Setup complete! You can now run the application." -ForegroundColor Green
} else {
    Write-Host "⚠ Please add your service account JSON file to continue." -ForegroundColor Yellow
}


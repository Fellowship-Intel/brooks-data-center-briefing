# Setup script to enable required Google Cloud APIs (PowerShell)
# Run this once before deploying services

$ErrorActionPreference = "Stop"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "mikebrooks" }

Write-Host "🔧 Setting up GCP project: ${PROJECT_ID}" -ForegroundColor Green
Write-Host ""

# Set the project
Write-Host "📋 Setting GCP project..." -ForegroundColor Cyan
gcloud config set project ${PROJECT_ID}

# Authenticate (if not already done)
Write-Host ""
Write-Host "🔐 Checking authentication..." -ForegroundColor Cyan
$activeAccounts = gcloud auth list --filter=status:ACTIVE --format="value(account)"
if (-not $activeAccounts) {
    Write-Host "⚠️  Not authenticated. Please run:" -ForegroundColor Yellow
    Write-Host "   gcloud auth login" -ForegroundColor Yellow
    Write-Host "   gcloud auth application-default login" -ForegroundColor Yellow
    exit 1
}

# Enable required APIs
Write-Host ""
Write-Host "🚀 Enabling required APIs..." -ForegroundColor Cyan
gcloud services enable `
  run.googleapis.com `
  artifactregistry.googleapis.com `
  firestore.googleapis.com `
  storage.googleapis.com `
  secretmanager.googleapis.com `
  cloudbuild.googleapis.com

Write-Host ""
Write-Host "✅ All APIs enabled successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Deploy UI service: .\scripts\deploy_ui.ps1" -ForegroundColor Yellow
Write-Host "   2. Deploy API service: .\scripts\deploy_api.ps1" -ForegroundColor Yellow


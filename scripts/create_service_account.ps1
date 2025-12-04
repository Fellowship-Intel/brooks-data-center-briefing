# Create the App Backend Service Account for the Michael Brooks report service (PowerShell version)
# Prerequisites:
# - gcloud CLI installed and authenticated
# - GCP project "mikebrooks" set up

$ErrorActionPreference = "Stop"

$PROJECT_ID = "mikebrooks"
$SERVICE_ACCOUNT_NAME = "app-backend-sa"
$DISPLAY_NAME = "App Backend Service Account"

Write-Host "🔧 Creating service account: ${SERVICE_ACCOUNT_NAME}" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Set the project
Write-Host "📋 Setting GCP project to ${PROJECT_ID}..." -ForegroundColor Yellow
gcloud config set project ${PROJECT_ID}

Write-Host ""
Write-Host "🚀 Creating service account..." -ForegroundColor Green
Write-Host ""

# Create the service account
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} `
  --display-name="${DISPLAY_NAME}" `
  --project=${PROJECT_ID}

Write-Host ""
Write-Host "✅ Service account created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📧 Service account email: ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Grant necessary IAM roles to the service account" -ForegroundColor Yellow
Write-Host "   2. Create and download a service account key (if needed for local development)" -ForegroundColor Yellow
Write-Host "   3. Store the key securely in .secrets/app-backend-sa.json" -ForegroundColor Yellow


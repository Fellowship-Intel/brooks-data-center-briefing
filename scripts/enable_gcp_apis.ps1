# Enable required GCP APIs for the Michael Brooks report service (PowerShell version)
# Prerequisites:
# - gcloud CLI installed and authenticated
# - GCP project "mikebrooks" set up

$ErrorActionPreference = "Stop"

$PROJECT_ID = "mikebrooks"

Write-Host "🔧 Enabling required GCP APIs for project: ${PROJECT_ID}" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Set the project
Write-Host "📋 Setting GCP project to ${PROJECT_ID}..." -ForegroundColor Yellow
gcloud config set project ${PROJECT_ID}

Write-Host ""
Write-Host "🚀 Enabling APIs..." -ForegroundColor Green
Write-Host ""

# Enable Cloud Run API
Write-Host "1️⃣  Enabling Cloud Run API..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com

# Enable Firestore API
Write-Host "2️⃣  Enabling Firestore API..." -ForegroundColor Yellow
gcloud services enable firestore.googleapis.com

# Enable Cloud Storage API
Write-Host "3️⃣  Enabling Cloud Storage API..." -ForegroundColor Yellow
gcloud services enable storage.googleapis.com

# Enable Secret Manager API
Write-Host "4️⃣  Enabling Secret Manager API..." -ForegroundColor Yellow
gcloud services enable secretmanager.googleapis.com

# Enable Cloud Build API
Write-Host "5️⃣  Enabling Cloud Build API..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com

# Enable Container Registry API
Write-Host "6️⃣  Enabling Container Registry API..." -ForegroundColor Yellow
gcloud services enable containerregistry.googleapis.com

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "✅ All required APIs enabled!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Note: API enablement may take a few minutes to propagate." -ForegroundColor Yellow
Write-Host "   You can check status with: gcloud services list --enabled" -ForegroundColor Yellow


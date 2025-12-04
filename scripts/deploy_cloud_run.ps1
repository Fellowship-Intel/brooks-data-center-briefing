# Deploy FastAPI app to Google Cloud Run (PowerShell version)
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Docker installed
# - GCP project "mikebrooks" set up
# - Cloud Run API enabled
# - Container Registry API enabled

$ErrorActionPreference = "Stop"

$PROJECT_ID = "mikebrooks"
$SERVICE_NAME = "michael-brooks-report-api"
$REGION = "us-central1"
$IMAGE_TAG = "gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

Write-Host "🚀 Building and deploying to Cloud Run..." -ForegroundColor Green
Write-Host "Project: ${PROJECT_ID}"
Write-Host "Service: ${SERVICE_NAME}"
Write-Host "Region: ${REGION}"
Write-Host ""

# Check if required environment variables are set
if (-not $env:REPORTS_BUCKET_NAME) {
    Write-Host "❌ REPORTS_BUCKET_NAME environment variable is not set" -ForegroundColor Red
    Write-Host "   Set it with: `$env:REPORTS_BUCKET_NAME='your-bucket-name'" -ForegroundColor Yellow
    exit 1
}

if (-not $env:GOOGLE_API_KEY) {
    Write-Host "⚠️  GOOGLE_API_KEY environment variable is not set" -ForegroundColor Yellow
    Write-Host "   You can set it during deployment or use Secret Manager" -ForegroundColor Yellow
    $response = Read-Host "Continue without GOOGLE_API_KEY? (y/n)"
    if ($response -ne "y" -and $response -ne "Y") {
        exit 1
    }
}

# Set the project
Write-Host "📋 Setting GCP project to ${PROJECT_ID}..." -ForegroundColor Cyan
gcloud config set project ${PROJECT_ID}

# Build and submit the image
Write-Host ""
Write-Host "🔨 Building Docker image..." -ForegroundColor Cyan
gcloud builds submit --tag ${IMAGE_TAG}

# Deploy to Cloud Run
Write-Host ""
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Cyan

$envVars = "GCP_PROJECT_ID=${PROJECT_ID},REPORTS_BUCKET_NAME=$env:REPORTS_BUCKET_NAME"

# Add GOOGLE_API_KEY if provided
if ($env:GOOGLE_API_KEY) {
    $envVars = "${envVars},GOOGLE_API_KEY=$env:GOOGLE_API_KEY"
}

gcloud run deploy ${SERVICE_NAME} `
  --image ${IMAGE_TAG} `
  --platform managed `
  --region ${REGION} `
  --allow-unauthenticated `
  --set-env-vars ${envVars}

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Service URL:" -ForegroundColor Cyan
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'
Write-Host ""
Write-Host "💡 Note: Make sure your service account has the necessary permissions:" -ForegroundColor Yellow
Write-Host "   - Cloud Run Invoker"
Write-Host "   - Firestore User"
Write-Host "   - Storage Object Admin"
Write-Host "   - Secret Manager Secret Accessor"


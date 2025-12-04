# Deploy FastAPI service to Google Cloud Run (PowerShell)
$ErrorActionPreference = "Stop"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "mikebrooks" }
$SERVICE_NAME = "brooks-briefing-api"
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$REPO = if ($env:REPO) { $env:REPO } else { "brooks-reports-repo" }
$IMAGE_API = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/brooks-api"

Write-Host "🚀 Building and deploying API service to Cloud Run..." -ForegroundColor Green
Write-Host "Project: ${PROJECT_ID}"
Write-Host "Service: ${SERVICE_NAME}"
Write-Host "Region: ${REGION}"
Write-Host "Repository: ${REPO}"
Write-Host ""

# Check if required environment variables are set
if (-not $env:REPORTS_BUCKET_NAME) {
    Write-Host "❌ REPORTS_BUCKET_NAME environment variable is not set" -ForegroundColor Red
    Write-Host "   Set it with: `$env:REPORTS_BUCKET_NAME='your-bucket-name'" -ForegroundColor Yellow
    exit 1
}

# Set the project
gcloud config set project ${PROJECT_ID}

# Build and submit the image (using Dockerfile.api)
Write-Host "🔨 Building Docker image..." -ForegroundColor Cyan
gcloud builds submit --tag "${IMAGE_API}" --file Dockerfile.api

# Deploy to Cloud Run
Write-Host ""
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Cyan

$envVars = "GCP_PROJECT_ID=${PROJECT_ID},REPORTS_BUCKET_NAME=$env:REPORTS_BUCKET_NAME"

# Add GOOGLE_API_KEY if provided
if ($env:GOOGLE_API_KEY) {
    $envVars = "${envVars},GOOGLE_API_KEY=$env:GOOGLE_API_KEY"
}

gcloud run deploy ${SERVICE_NAME} `
  --image="${IMAGE_API}" `
  --platform=managed `
  --region="${REGION}" `
  --allow-unauthenticated `
  --cpu=1 `
  --memory=1Gi `
  --port=8000 `
  --set-env-vars="${envVars}" `
  --command="uvicorn" `
  --args="app.main:app,--host,0.0.0.0,--port,8000"

Write-Host ""
Write-Host "✅ API service deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Service URL:" -ForegroundColor Cyan
$API_URL = gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'
Write-Host "${API_URL}"
Write-Host ""
Write-Host "💡 Update UI service with this API URL:" -ForegroundColor Yellow
$REPORTS_BUCKET = if ($env:REPORTS_BUCKET_NAME) { $env:REPORTS_BUCKET_NAME } else { "mikebrooks-reports" }
Write-Host "   gcloud run services update brooks-briefing-ui --region ${REGION} --set-env-vars=`"GCP_PROJECT_ID=${PROJECT_ID},REPORTS_BUCKET_NAME=${REPORTS_BUCKET},API_URL=${API_URL}`"" -ForegroundColor Cyan


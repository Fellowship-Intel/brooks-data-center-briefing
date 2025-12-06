# Deploy React frontend to Google Cloud Run (PowerShell)
$ErrorActionPreference = "Stop"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "mikebrooks" }
$SERVICE_NAME = "brooks-briefing-react"
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$REPO = if ($env:REPO) { $env:REPO } else { "brooks-reports-repo" }
$IMAGE_REACT = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/brooks-react"

Write-Host "🚀 Building and deploying React frontend to Cloud Run..." -ForegroundColor Green
Write-Host "Project: ${PROJECT_ID}"
Write-Host "Service: ${SERVICE_NAME}"
Write-Host "Region: ${REGION}"
Write-Host "Repository: ${REPO}"
Write-Host ""

# Set the project
gcloud config set project ${PROJECT_ID}

# Get API service URL if it exists
$API_URL = gcloud run services describe brooks-briefing-api-nodejs --region ${REGION} --format 'value(status.url)' 2>$null
if (-not $API_URL) {
    Write-Host "⚠️  Warning: API service not found. React app will use default API URL." -ForegroundColor Yellow
    $API_URL = "http://localhost:8000"
}

Write-Host "📡 API URL: ${API_URL}" -ForegroundColor Cyan
Write-Host ""

# Build and submit the image (using Dockerfile.react)
Write-Host "🔨 Building Docker image..." -ForegroundColor Cyan

# Build with API URL as build arg
gcloud builds submit --tag "${IMAGE_REACT}" `
  --file Dockerfile.react `
  --substitutions=_VITE_API_URL="${API_URL}"

# Deploy to Cloud Run
Write-Host ""
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Cyan

gcloud run deploy ${SERVICE_NAME} `
  --image="${IMAGE_REACT}" `
  --platform=managed `
  --region="${REGION}" `
  --allow-unauthenticated `
  --cpu=1 `
  --memory=512Mi `
  --port=80 `
  --min-instances=0 `
  --max-instances=10

Write-Host ""
Write-Host "✅ React frontend deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Service URL:" -ForegroundColor Cyan
$REACT_URL = gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'
Write-Host "${REACT_URL}"
Write-Host ""
Write-Host "💡 Update CORS in API service to allow this origin:" -ForegroundColor Yellow
Write-Host "   gcloud run services update brooks-briefing-api-nodejs --region ${REGION} --set-env-vars=`"REACT_APP_URL=${REACT_URL}`"" -ForegroundColor Cyan


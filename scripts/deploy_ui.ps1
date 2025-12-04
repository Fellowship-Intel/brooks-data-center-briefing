# Deploy Streamlit UI service to Google Cloud Run (PowerShell)
$ErrorActionPreference = "Stop"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "mikebrooks" }
$SERVICE_NAME = "brooks-briefing-ui"
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$REPO = if ($env:REPO) { $env:REPO } else { "brooks-reports-repo" }
$IMAGE_UI = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/brooks-ui"

Write-Host "🚀 Building and deploying UI service to Cloud Run..." -ForegroundColor Green
Write-Host "Project: ${PROJECT_ID}"
Write-Host "Service: ${SERVICE_NAME}"
Write-Host "Region: ${REGION}"
Write-Host "Repository: ${REPO}"
Write-Host ""

# Set the project
gcloud config set project ${PROJECT_ID}

# Build and submit the image (using Dockerfile.ui)
Write-Host "🔨 Building Docker image..." -ForegroundColor Cyan
gcloud builds submit --tag "${IMAGE_UI}" --file Dockerfile.ui

# Deploy to Cloud Run
Write-Host ""
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Cyan

# Get API service URL if it exists
$API_URL = gcloud run services describe brooks-briefing-api --region ${REGION} --format 'value(status.url)' 2>$null
$REPORTS_BUCKET = if ($env:REPORTS_BUCKET_NAME) { $env:REPORTS_BUCKET_NAME } else { "mikebrooks-reports" }

$envVars = "GCP_PROJECT_ID=${PROJECT_ID},REPORTS_BUCKET_NAME=${REPORTS_BUCKET}"
if ($API_URL) {
    Write-Host "📡 Found API service at: ${API_URL}" -ForegroundColor Cyan
    $envVars = "${envVars},API_URL=${API_URL}"
}

gcloud run deploy ${SERVICE_NAME} `
  --image="${IMAGE_UI}" `
  --platform=managed `
  --region="${REGION}" `
  --allow-unauthenticated `
  --cpu=1 `
  --memory=1Gi `
  --port=8501 `
  --set-env-vars="${envVars}" `
  --command="streamlit" `
  --args="run,app.py,--server.port=8501,--server.address=0.0.0.0"

Write-Host ""
Write-Host "✅ UI service deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Service URL:" -ForegroundColor Cyan
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'


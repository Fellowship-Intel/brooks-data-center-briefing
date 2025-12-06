# Deploy Node.js API service to Google Cloud Run (PowerShell)
$ErrorActionPreference = "Stop"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "mikebrooks" }
$SERVICE_NAME = "brooks-briefing-api-nodejs"
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$REPO = if ($env:REPO) { $env:REPO } else { "brooks-reports-repo" }
$IMAGE_API = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/brooks-api-nodejs"

Write-Host "🚀 Building and deploying Node.js API service to Cloud Run..." -ForegroundColor Green
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

# Build and submit the image (using server/Dockerfile)
Write-Host "🔨 Building Docker image..." -ForegroundColor Cyan
gcloud builds submit --tag "${IMAGE_API}" --file server/Dockerfile

# Deploy to Cloud Run
Write-Host ""
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Cyan

$envVars = "GCP_PROJECT_ID=${PROJECT_ID},REPORTS_BUCKET_NAME=$env:REPORTS_BUCKET_NAME,ENVIRONMENT=production"

# Add CORS origins if provided
if ($env:REACT_APP_URL) {
    $envVars = "${envVars},REACT_APP_URL=$env:REACT_APP_URL"
}
if ($env:STREAMLIT_APP_URL) {
    $envVars = "${envVars},STREAMLIT_APP_URL=$env:STREAMLIT_APP_URL"
}

# Add API keys if provided (otherwise will use Secret Manager)
if ($env:GEMINI_API_KEY) {
    $envVars = "${envVars},GEMINI_API_KEY=$env:GEMINI_API_KEY"
}
if ($env:ELEVEN_LABS_API_KEY) {
    $envVars = "${envVars},ELEVEN_LABS_API_KEY=$env:ELEVEN_LABS_API_KEY"
}

# Get service account email if provided
$serviceAccount = if ($env:SERVICE_ACCOUNT_EMAIL) { $env:SERVICE_ACCOUNT_EMAIL } else { "${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" }

gcloud run deploy ${SERVICE_NAME} `
  --image="${IMAGE_API}" `
  --platform=managed `
  --region="${REGION}" `
  --allow-unauthenticated `
  --cpu=1 `
  --memory=1Gi `
  --port=8000 `
  --set-env-vars="${envVars}" `
  --service-account="${serviceAccount}" `
  --min-instances=0 `
  --max-instances=10

Write-Host ""
Write-Host "✅ Node.js API service deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Service URL:" -ForegroundColor Cyan
$API_URL = gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'
Write-Host "${API_URL}"
Write-Host ""
Write-Host "💡 Update frontend services with this API URL:" -ForegroundColor Yellow
Write-Host "   React: Set VITE_API_URL=${API_URL}" -ForegroundColor Cyan
Write-Host "   Streamlit: Set API_URL=${API_URL}" -ForegroundColor Cyan


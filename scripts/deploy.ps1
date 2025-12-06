# Deployment script for Brooks Data Center Briefing (PowerShell)
# Usage: .\scripts\deploy.ps1 [environment]

param(
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

$ProjectId = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "mikebrooks" }
$Region = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }

Write-Host "🚀 Deploying to $Environment environment..." -ForegroundColor Cyan

# Validate environment
if ($Environment -notin @("development", "staging", "production")) {
    Write-Host "❌ Invalid environment: $Environment" -ForegroundColor Red
    Write-Host "Usage: .\scripts\deploy.ps1 [development|staging|production]"
    exit 1
}

# Check required tools
try {
    gcloud --version | Out-Null
} catch {
    Write-Host "❌ gcloud CLI not found. Install from https://cloud.google.com/sdk" -ForegroundColor Red
    exit 1
}

try {
    docker --version | Out-Null
} catch {
    Write-Host "❌ Docker not found. Install from https://www.docker.com" -ForegroundColor Red
    exit 1
}

# Set project
Write-Host "📦 Setting GCP project to $ProjectId..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Build Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
$ImageName = "gcr.io/$ProjectId/brooks-briefing:$Environment"
docker build -t $ImageName .

# Push to Container Registry
Write-Host "📤 Pushing image to Container Registry..." -ForegroundColor Yellow
docker push $ImageName

# Deploy to Cloud Run
Write-Host "☁️  Deploying to Cloud Run..." -ForegroundColor Yellow
$ServiceName = "brooks-briefing-$Environment"

gcloud run deploy $ServiceName `
    --image $ImageName `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --set-env-vars "ENVIRONMENT=$Environment" `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10

# Get service URL
$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format 'value(status.url)'
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🌐 Service URL: $ServiceUrl" -ForegroundColor Green


# Check Cloud Run service logs (PowerShell version)
# Usage: .\scripts\check_logs.ps1 [api|ui|both]

param(
    [string]$Service = "both"
)

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "mikebrooks" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$API_SERVICE = if ($env:API_SERVICE_NAME) { $env:API_SERVICE_NAME } else { "brooks-briefing-api" }
$UI_SERVICE = if ($env:UI_SERVICE_NAME) { $env:UI_SERVICE_NAME } else { "brooks-briefing-ui" }
$LIMIT = if ($env:LOG_LIMIT) { $env:LOG_LIMIT } else { "50" }

Write-Host "📋 Reading Cloud Run logs" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host "Limit: $LIMIT entries"
Write-Host ""

if ($Service -eq "api" -or $Service -eq "both") {
    Write-Host "🔍 Reading API service logs ($API_SERVICE)..." -ForegroundColor Yellow
    gcloud logs read `
        --project="$PROJECT_ID" `
        --region="$REGION" `
        --service="$API_SERVICE" `
        --limit="$LIMIT"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to read API logs" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

if ($Service -eq "ui" -or $Service -eq "both") {
    Write-Host "🔍 Reading UI service logs ($UI_SERVICE)..." -ForegroundColor Yellow
    gcloud logs read `
        --project="$PROJECT_ID" `
        --region="$REGION" `
        --service="$UI_SERVICE" `
        --limit="$LIMIT"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to read UI logs" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

Write-Host "✅ Log check complete" -ForegroundColor Green


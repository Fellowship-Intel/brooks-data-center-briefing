# Setup Cloud Scheduler job for daily watchlist report generation (PowerShell version)
# This creates a scheduled job that triggers the API endpoint at 3:00 AM PST

$ErrorActionPreference = "Stop"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "mikebrooks" }
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$API_SERVICE = if ($env:API_SERVICE_NAME) { $env:API_SERVICE_NAME } else { "brooks-briefing-api" }
$SCHEDULER_JOB = if ($env:SCHEDULER_JOB_NAME) { $env:SCHEDULER_JOB_NAME } else { "brooks-daily-watchlist" }
$SERVICE_ACCOUNT = if ($env:SERVICE_ACCOUNT_EMAIL) { $env:SERVICE_ACCOUNT_EMAIL } else { "" }

Write-Host "📅 Setting up Cloud Scheduler for daily watchlist report" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host "API Service: $API_SERVICE"
Write-Host "Job Name: $SCHEDULER_JOB"
Write-Host ""

# Set the project
gcloud config set project $PROJECT_ID

# Get the API service URL
Write-Host "🔍 Getting API service URL..." -ForegroundColor Yellow
$API_URL = gcloud run services describe $API_SERVICE --region $REGION --format 'value(status.url)' 2>$null

if (-not $API_URL) {
    Write-Host "❌ Could not find API service: $API_SERVICE" -ForegroundColor Red
    Write-Host "   Make sure the API service is deployed first" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found API service at: $API_URL" -ForegroundColor Green
Write-Host ""

# Get or create service account for Cloud Scheduler
if (-not $SERVICE_ACCOUNT) {
    $SERVICE_ACCOUNT_NAME = "cloud-scheduler-sa"
    $SERVICE_ACCOUNT = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    Write-Host "🔍 Checking for service account: $SERVICE_ACCOUNT" -ForegroundColor Yellow
    
    # Check if service account exists
    $saExists = gcloud iam service-accounts describe $SERVICE_ACCOUNT --project $PROJECT_ID 2>$null
    if (-not $saExists) {
        Write-Host "📝 Creating service account: $SERVICE_ACCOUNT_NAME" -ForegroundColor Cyan
        gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME `
            --display-name="Cloud Scheduler Service Account" `
            --description="Service account for Cloud Scheduler to invoke Cloud Run services" `
            --project $PROJECT_ID
        
        Write-Host "🔐 Granting Cloud Run Invoker role..." -ForegroundColor Cyan
        gcloud run services add-iam-policy-binding $API_SERVICE `
            --region $REGION `
            --member="serviceAccount:$SERVICE_ACCOUNT" `
            --role="roles/run.invoker" `
            --project $PROJECT_ID
    } else {
        Write-Host "✅ Service account already exists" -ForegroundColor Green
    }
} else {
    Write-Host "📝 Using provided service account: $SERVICE_ACCOUNT" -ForegroundColor Cyan
}

Write-Host ""

# Check if job already exists
Write-Host "🔍 Checking for existing scheduler job..." -ForegroundColor Yellow
$jobExists = gcloud scheduler jobs describe $SCHEDULER_JOB --location $REGION --project $PROJECT_ID 2>$null

# Prepare the request body
$REQUEST_BODY = '{"client_id":"michael_brooks","watchlist":["IREN","CRWV","NBIS","MRVL"]}'

# Schedule: 3:00 AM PST/PDT (America/Los_Angeles)
$SCHEDULE = "0 3 * * *"
$TIMEZONE = "America/Los_Angeles"

$ENDPOINT_URL = "${API_URL}/reports/generate/watchlist"

Write-Host "📋 Job Configuration:" -ForegroundColor Cyan
Write-Host "   Schedule: $SCHEDULE ($TIMEZONE)"
Write-Host "   Endpoint: $ENDPOINT_URL"
Write-Host "   Method: POST"
Write-Host "   Service Account: $SERVICE_ACCOUNT"
Write-Host ""

if (-not $jobExists) {
    Write-Host "🚀 Creating Cloud Scheduler job..." -ForegroundColor Green
    gcloud scheduler jobs create http $SCHEDULER_JOB `
        --location=$REGION `
        --schedule="$SCHEDULE" `
        --time-zone="$TIMEZONE" `
        --uri="$ENDPOINT_URL" `
        --http-method=POST `
        --oidc-service-account-email="$SERVICE_ACCOUNT" `
        --oidc-token-audience="$API_URL" `
        --headers="Content-Type=application/json" `
        --message-body="$REQUEST_BODY" `
        --project=$PROJECT_ID
} else {
    Write-Host "🔄 Updating Cloud Scheduler job..." -ForegroundColor Yellow
    gcloud scheduler jobs update http $SCHEDULER_JOB `
        --location=$REGION `
        --schedule="$SCHEDULE" `
        --time-zone="$TIMEZONE" `
        --uri="$ENDPOINT_URL" `
        --http-method=POST `
        --oidc-service-account-email="$SERVICE_ACCOUNT" `
        --oidc-token-audience="$API_URL" `
        --headers="Content-Type=application/json" `
        --message-body="$REQUEST_BODY" `
        --project=$PROJECT_ID
}

Write-Host ""
Write-Host "✅ Cloud Scheduler job configured successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Job Details:" -ForegroundColor Cyan
gcloud scheduler jobs describe $SCHEDULER_JOB --location $REGION --project $PROJECT_ID
Write-Host ""
Write-Host "💡 Useful commands:" -ForegroundColor Cyan
Write-Host "   # Test the job manually"
Write-Host "   gcloud scheduler jobs run $SCHEDULER_JOB --location $REGION"
Write-Host ""
Write-Host "   # View job status"
Write-Host "   gcloud scheduler jobs describe $SCHEDULER_JOB --location $REGION"
Write-Host ""
Write-Host "   # Pause the job"
Write-Host "   gcloud scheduler jobs pause $SCHEDULER_JOB --location $REGION"
Write-Host ""
Write-Host "   # Resume the job"
Write-Host "   gcloud scheduler jobs resume $SCHEDULER_JOB --location $REGION"
Write-Host ""
Write-Host "   # Delete the job"
Write-Host "   gcloud scheduler jobs delete $SCHEDULER_JOB --location $REGION"


# Test the Cloud Scheduler job manually (PowerShell version)
# This triggers the scheduled job immediately for testing

$ErrorActionPreference = "Stop"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "mikebrooks" }
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$SCHEDULER_JOB = if ($env:SCHEDULER_JOB_NAME) { $env:SCHEDULER_JOB_NAME } else { "brooks-daily-watchlist" }

Write-Host "🧪 Testing Cloud Scheduler job: $SCHEDULER_JOB" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host ""

# Set the project
gcloud config set project $PROJECT_ID

Write-Host "🚀 Triggering job manually..." -ForegroundColor Yellow
gcloud scheduler jobs run $SCHEDULER_JOB --location $REGION --project $PROJECT_ID

Write-Host ""
Write-Host "✅ Job triggered successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Check the job execution logs:" -ForegroundColor Cyan
Write-Host "   gcloud scheduler jobs describe $SCHEDULER_JOB --location $REGION"
Write-Host ""
Write-Host "💡 Check Cloud Run logs:" -ForegroundColor Cyan
Write-Host "   gcloud logs read --project=$PROJECT_ID --region=$REGION --service=brooks-briefing-api --limit=20"


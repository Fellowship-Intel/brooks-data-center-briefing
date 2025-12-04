#!/bin/bash

# Setup Cloud Scheduler job for daily watchlist report generation
# This creates a scheduled job that triggers the API endpoint at 3:00 AM PST

set -e

PROJECT_ID="${GCP_PROJECT_ID:-mikebrooks}"
REGION="${REGION:-us-central1}"
API_SERVICE="${API_SERVICE_NAME:-brooks-briefing-api}"
SCHEDULER_JOB="${SCHEDULER_JOB_NAME:-brooks-daily-watchlist}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_EMAIL:-}"

echo "📅 Setting up Cloud Scheduler for daily watchlist report"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "API Service: ${API_SERVICE}"
echo "Job Name: ${SCHEDULER_JOB}"
echo ""

# Set the project
gcloud config set project ${PROJECT_ID}

# Get the API service URL
echo "🔍 Getting API service URL..."
API_URL=$(gcloud run services describe ${API_SERVICE} --region ${REGION} --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "${API_URL}" ]; then
    echo "❌ Could not find API service: ${API_SERVICE}"
    echo "   Make sure the API service is deployed first"
    exit 1
fi

echo "✅ Found API service at: ${API_URL}"
echo ""

# Get or create service account for Cloud Scheduler
if [ -z "${SERVICE_ACCOUNT}" ]; then
    SERVICE_ACCOUNT_NAME="cloud-scheduler-sa"
    SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    echo "🔍 Checking for service account: ${SERVICE_ACCOUNT}"
    
    # Check if service account exists
    if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT} --project ${PROJECT_ID} &>/dev/null; then
        echo "📝 Creating service account: ${SERVICE_ACCOUNT_NAME}"
        gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
            --display-name="Cloud Scheduler Service Account" \
            --description="Service account for Cloud Scheduler to invoke Cloud Run services" \
            --project ${PROJECT_ID}
        
        echo "🔐 Granting Cloud Run Invoker role..."
        gcloud run services add-iam-policy-binding ${API_SERVICE} \
            --region ${REGION} \
            --member="serviceAccount:${SERVICE_ACCOUNT}" \
            --role="roles/run.invoker" \
            --project ${PROJECT_ID}
    else
        echo "✅ Service account already exists"
    fi
else
    echo "📝 Using provided service account: ${SERVICE_ACCOUNT}"
fi

echo ""

# Check if job already exists
echo "🔍 Checking for existing scheduler job..."
if gcloud scheduler jobs describe ${SCHEDULER_JOB} --location ${REGION} --project ${PROJECT_ID} &>/dev/null; then
    echo "⚠️  Scheduler job already exists. Updating..."
    UPDATE_MODE="update"
else
    echo "📝 Creating new scheduler job..."
    UPDATE_MODE="create"
fi

# Prepare the request body
REQUEST_BODY='{"client_id":"michael_brooks","watchlist":["IREN","CRWV","NBIS","MRVL"]}'

# Schedule: 3:00 AM PST/PDT (America/Los_Angeles)
SCHEDULE="0 3 * * *"
TIMEZONE="America/Los_Angeles"

ENDPOINT_URL="${API_URL}/reports/generate/watchlist"

echo "📋 Job Configuration:"
echo "   Schedule: ${SCHEDULE} (${TIMEZONE})"
echo "   Endpoint: ${ENDPOINT_URL}"
echo "   Method: POST"
echo "   Service Account: ${SERVICE_ACCOUNT}"
echo ""

if [ "${UPDATE_MODE}" = "create" ]; then
    echo "🚀 Creating Cloud Scheduler job..."
    gcloud scheduler jobs create http ${SCHEDULER_JOB} \
        --location=${REGION} \
        --schedule="${SCHEDULE}" \
        --time-zone="${TIMEZONE}" \
        --uri="${ENDPOINT_URL}" \
        --http-method=POST \
        --oidc-service-account-email="${SERVICE_ACCOUNT}" \
        --oidc-token-audience="${API_URL}" \
        --headers="Content-Type=application/json" \
        --message-body="${REQUEST_BODY}" \
        --project=${PROJECT_ID}
else
    echo "🔄 Updating Cloud Scheduler job..."
    gcloud scheduler jobs update http ${SCHEDULER_JOB} \
        --location=${REGION} \
        --schedule="${SCHEDULE}" \
        --time-zone="${TIMEZONE}" \
        --uri="${ENDPOINT_URL}" \
        --http-method=POST \
        --oidc-service-account-email="${SERVICE_ACCOUNT}" \
        --oidc-token-audience="${API_URL}" \
        --headers="Content-Type=application/json" \
        --message-body="${REQUEST_BODY}" \
        --project=${PROJECT_ID}
fi

echo ""
echo "✅ Cloud Scheduler job configured successfully!"
echo ""
echo "📝 Job Details:"
gcloud scheduler jobs describe ${SCHEDULER_JOB} --location ${REGION} --project ${PROJECT_ID}
echo ""
echo "💡 Useful commands:"
echo "   # Test the job manually"
echo "   gcloud scheduler jobs run ${SCHEDULER_JOB} --location ${REGION}"
echo ""
echo "   # View job status"
echo "   gcloud scheduler jobs describe ${SCHEDULER_JOB} --location ${REGION}"
echo ""
echo "   # Pause the job"
echo "   gcloud scheduler jobs pause ${SCHEDULER_JOB} --location ${REGION}"
echo ""
echo "   # Resume the job"
echo "   gcloud scheduler jobs resume ${SCHEDULER_JOB} --location ${REGION}"
echo ""
echo "   # Delete the job"
echo "   gcloud scheduler jobs delete ${SCHEDULER_JOB} --location ${REGION}"


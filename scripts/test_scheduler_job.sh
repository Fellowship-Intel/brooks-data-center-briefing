#!/bin/bash

# Test the Cloud Scheduler job manually
# This triggers the scheduled job immediately for testing

set -e

PROJECT_ID="${GCP_PROJECT_ID:-mikebrooks}"
REGION="${REGION:-us-central1}"
SCHEDULER_JOB="${SCHEDULER_JOB_NAME:-brooks-daily-watchlist}"

echo "🧪 Testing Cloud Scheduler job: ${SCHEDULER_JOB}"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Set the project
gcloud config set project ${PROJECT_ID}

echo "🚀 Triggering job manually..."
gcloud scheduler jobs run ${SCHEDULER_JOB} --location ${REGION} --project ${PROJECT_ID}

echo ""
echo "✅ Job triggered successfully!"
echo ""
echo "💡 Check the job execution logs:"
echo "   gcloud scheduler jobs describe ${SCHEDULER_JOB} --location ${REGION}"
echo ""
echo "💡 Check Cloud Run logs:"
echo "   gcloud logs read --project=${PROJECT_ID} --region=${REGION} --service=brooks-briefing-api --limit=20"


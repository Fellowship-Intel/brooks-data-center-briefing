#!/bin/bash

# Deploy Streamlit UI service to Google Cloud Run
set -e

PROJECT_ID="${GCP_PROJECT_ID:-mikebrooks}"
SERVICE_NAME="brooks-briefing-ui"
REGION="${REGION:-us-central1}"
REPO="${REPO:-brooks-reports-repo}"
IMAGE_UI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/brooks-ui"

echo "🚀 Building and deploying UI service to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Repository: ${REPO}"
echo ""

# Set the project
gcloud config set project ${PROJECT_ID}

# Build and submit the image (using Dockerfile.ui)
echo "🔨 Building Docker image..."
gcloud builds submit --tag "${IMAGE_UI}" --file Dockerfile.ui

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."

# Get API service URL if it exists
API_URL=$(gcloud run services describe brooks-briefing-api --region ${REGION} --format 'value(status.url)' 2>/dev/null || echo "")

ENV_VARS="GCP_PROJECT_ID=${PROJECT_ID},REPORTS_BUCKET_NAME=${REPORTS_BUCKET_NAME:-mikebrooks-reports}"
if [ -n "$API_URL" ]; then
    ENV_VARS="${ENV_VARS},API_URL=${API_URL}"
    echo "📡 Found API service at: ${API_URL}"
fi

gcloud run deploy ${SERVICE_NAME} \
  --image="${IMAGE_UI}" \
  --platform=managed \
  --region="${REGION}" \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=1Gi \
  --port=8501 \
  --set-env-vars="${ENV_VARS}" \
  --command="streamlit" \
  --args="run,app.py,--server.port=8501,--server.address=0.0.0.0"

echo ""
echo "✅ UI service deployed successfully!"
echo ""
echo "📝 Service URL:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'


#!/bin/bash

# Deploy FastAPI service to Google Cloud Run
set -e

PROJECT_ID="${GCP_PROJECT_ID:-mikebrooks}"
SERVICE_NAME="brooks-briefing-api"
REGION="${REGION:-us-central1}"
REPO="${REPO:-brooks-reports-repo}"
IMAGE_API="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/brooks-api"

echo "🚀 Building and deploying API service to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Repository: ${REPO}"
echo ""

# Check if required environment variables are set
if [ -z "$REPORTS_BUCKET_NAME" ]; then
    echo "❌ REPORTS_BUCKET_NAME environment variable is not set"
    echo "   Set it with: export REPORTS_BUCKET_NAME=your-bucket-name"
    exit 1
fi

# Set the project
gcloud config set project ${PROJECT_ID}

# Build and submit the image (using Dockerfile.api)
echo "🔨 Building Docker image..."
gcloud builds submit --tag "${IMAGE_API}" --file Dockerfile.api

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."

ENV_VARS="GCP_PROJECT_ID=${PROJECT_ID},REPORTS_BUCKET_NAME=${REPORTS_BUCKET_NAME}"

# Add GOOGLE_API_KEY if provided
if [ -n "$GOOGLE_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},GOOGLE_API_KEY=${GOOGLE_API_KEY}"
fi

gcloud run deploy ${SERVICE_NAME} \
  --image="${IMAGE_API}" \
  --platform=managed \
  --region="${REGION}" \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=1Gi \
  --port=8000 \
  --set-env-vars="${ENV_VARS}" \
  --command="uvicorn" \
  --args="app.main:app,--host,0.0.0.0,--port,8000"

echo ""
echo "✅ API service deployed successfully!"
echo ""
echo "📝 Service URL:"
API_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "${API_URL}"
echo ""
echo "💡 Update UI service with this API URL:"
echo "   gcloud run services update brooks-briefing-ui --region ${REGION} --set-env-vars=\"GCP_PROJECT_ID=${PROJECT_ID},REPORTS_BUCKET_NAME=${REPORTS_BUCKET_NAME},API_URL=${API_URL}\""


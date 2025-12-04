#!/bin/bash

# Deploy FastAPI app to Google Cloud Run
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Docker installed
# - GCP project "mikebrooks" set up
# - Cloud Run API enabled
# - Container Registry API enabled

set -e

PROJECT_ID="mikebrooks"
SERVICE_NAME="michael-brooks-report-api"
REGION="us-central1"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Building and deploying to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo ""

# Check if required environment variables are set
if [ -z "$REPORTS_BUCKET_NAME" ]; then
    echo "❌ REPORTS_BUCKET_NAME environment variable is not set"
    echo "   Set it with: export REPORTS_BUCKET_NAME=your-bucket-name"
    exit 1
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  GOOGLE_API_KEY environment variable is not set"
    echo "   You can set it during deployment or use Secret Manager"
    read -p "Continue without GOOGLE_API_KEY? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set the project
echo "📋 Setting GCP project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Build and submit the image
echo ""
echo "🔨 Building Docker image..."
gcloud builds submit --tag ${IMAGE_TAG}

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."

DEPLOY_CMD="gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_TAG} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=${PROJECT_ID},REPORTS_BUCKET_NAME=${REPORTS_BUCKET_NAME}"

# Add GOOGLE_API_KEY if provided
if [ -n "$GOOGLE_API_KEY" ]; then
    DEPLOY_CMD="${DEPLOY_CMD} --set-env-vars GOOGLE_API_KEY=${GOOGLE_API_KEY}"
fi

# Execute deployment
eval $DEPLOY_CMD

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Service URL:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'
echo ""
echo "💡 Note: Make sure your service account has the necessary permissions:"
echo "   - Cloud Run Invoker"
echo "   - Firestore User"
echo "   - Storage Object Admin"
echo "   - Secret Manager Secret Accessor"


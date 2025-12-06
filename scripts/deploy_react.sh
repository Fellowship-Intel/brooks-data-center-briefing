#!/bin/bash
# Deploy React frontend to Google Cloud Run (Bash)
set -e

PROJECT_ID=${GCP_PROJECT_ID:-mikebrooks}
SERVICE_NAME="brooks-briefing-react"
REGION=${REGION:-us-central1}
REPO=${REPO:-brooks-reports-repo}
IMAGE_REACT="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/brooks-react"

echo "🚀 Building and deploying React frontend to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Repository: ${REPO}"
echo ""

# Set the project
gcloud config set project ${PROJECT_ID}

# Get API service URL if it exists
API_URL=$(gcloud run services describe brooks-briefing-api-nodejs --region ${REGION} --format 'value(status.url)' 2>/dev/null || echo "")
if [ -z "$API_URL" ]; then
    echo "⚠️  Warning: API service not found. React app will use default API URL."
    API_URL="http://localhost:8000"
fi

echo "📡 API URL: ${API_URL}"
echo ""

# Build and submit the image (using Dockerfile.react)
echo "🔨 Building Docker image..."

gcloud builds submit --tag "${IMAGE_REACT}" \
  --file Dockerfile.react \
  --substitutions=_VITE_API_URL="${API_URL}"

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."

gcloud run deploy ${SERVICE_NAME} \
  --image="${IMAGE_REACT}" \
  --platform=managed \
  --region="${REGION}" \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=512Mi \
  --port=80 \
  --min-instances=0 \
  --max-instances=10

echo ""
echo "✅ React frontend deployed successfully!"
echo ""
echo "📝 Service URL:"
REACT_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "${REACT_URL}"
echo ""
echo "💡 Update CORS in API service to allow this origin:"
echo "   gcloud run services update brooks-briefing-api-nodejs --region ${REGION} --set-env-vars=\"REACT_APP_URL=${REACT_URL}\""


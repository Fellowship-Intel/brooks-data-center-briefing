#!/bin/bash
# Deploy Node.js API service to Google Cloud Run (Bash)
set -e

PROJECT_ID=${GCP_PROJECT_ID:-mikebrooks}
SERVICE_NAME="brooks-briefing-api-nodejs"
REGION=${REGION:-us-central1}
REPO=${REPO:-brooks-reports-repo}
IMAGE_API="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/brooks-api-nodejs"

echo "🚀 Building and deploying Node.js API service to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Repository: ${REPO}"
echo ""

# Check if required environment variables are set
if [ -z "$REPORTS_BUCKET_NAME" ]; then
    echo "❌ REPORTS_BUCKET_NAME environment variable is not set"
    echo "   Set it with: export REPORTS_BUCKET_NAME='your-bucket-name'"
    exit 1
fi

# Set the project
gcloud config set project ${PROJECT_ID}

# Build and submit the image (using server/Dockerfile)
echo "🔨 Building Docker image..."
gcloud builds submit --tag "${IMAGE_API}" --file server/Dockerfile

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."

ENV_VARS="GCP_PROJECT_ID=${PROJECT_ID},REPORTS_BUCKET_NAME=${REPORTS_BUCKET_NAME},ENVIRONMENT=production"

# Add CORS origins if provided
if [ -n "$REACT_APP_URL" ]; then
    ENV_VARS="${ENV_VARS},REACT_APP_URL=${REACT_APP_URL}"
fi
if [ -n "$STREAMLIT_APP_URL" ]; then
    ENV_VARS="${ENV_VARS},STREAMLIT_APP_URL=${STREAMLIT_APP_URL}"
fi

# Add API keys if provided (otherwise will use Secret Manager)
if [ -n "$GEMINI_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},GEMINI_API_KEY=${GEMINI_API_KEY}"
fi
if [ -n "$ELEVEN_LABS_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},ELEVEN_LABS_API_KEY=${ELEVEN_LABS_API_KEY}"
fi

# Get service account email if provided
SERVICE_ACCOUNT=${SERVICE_ACCOUNT_EMAIL:-${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com}

gcloud run deploy ${SERVICE_NAME} \
  --image="${IMAGE_API}" \
  --platform=managed \
  --region="${REGION}" \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=1Gi \
  --port=8000 \
  --set-env-vars="${ENV_VARS}" \
  --service-account="${SERVICE_ACCOUNT}" \
  --min-instances=0 \
  --max-instances=10

echo ""
echo "✅ Node.js API service deployed successfully!"
echo ""
echo "📝 Service URL:"
API_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "${API_URL}"
echo ""
echo "💡 Update frontend services with this API URL:"
echo "   React: Set VITE_API_URL=${API_URL}"
echo "   Streamlit: Set API_URL=${API_URL}"


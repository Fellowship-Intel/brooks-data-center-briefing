#!/bin/bash
# Deployment script for Brooks Data Center Briefing
# Usage: ./scripts/deploy.sh [environment]

set -e  # Exit on error

ENVIRONMENT=${1:-production}
PROJECT_ID=${GCP_PROJECT_ID:-mikebrooks}
REGION=${GCP_REGION:-us-central1}

echo "🚀 Deploying to $ENVIRONMENT environment..."

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "Usage: $0 [development|staging|production]"
    exit 1
fi

# Check required tools
command -v gcloud >/dev/null 2>&1 || { echo "❌ gcloud CLI not found. Install from https://cloud.google.com/sdk"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Install from https://www.docker.com"; exit 1; }

# Set project
echo "📦 Setting GCP project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Build Docker image
echo "🔨 Building Docker image..."
IMAGE_NAME="gcr.io/$PROJECT_ID/brooks-briefing:$ENVIRONMENT"
docker build -t $IMAGE_NAME .

# Push to Container Registry
echo "📤 Pushing image to Container Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
SERVICE_NAME="brooks-briefing-$ENVIRONMENT"

gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=$ENVIRONMENT \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"


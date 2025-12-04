#!/bin/bash

# Create the App Backend Service Account for the Michael Brooks report service
# Prerequisites:
# - gcloud CLI installed and authenticated
# - GCP project "mikebrooks" set up

set -e

PROJECT_ID="mikebrooks"
SERVICE_ACCOUNT_NAME="app-backend-sa"
DISPLAY_NAME="App Backend Service Account"

echo "🔧 Creating service account: ${SERVICE_ACCOUNT_NAME}"
echo "=================================================="
echo ""

# Set the project
echo "📋 Setting GCP project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

echo ""
echo "🚀 Creating service account..."
echo ""

# Create the service account
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
  --display-name="${DISPLAY_NAME}" \
  --project=${PROJECT_ID}

echo ""
echo "✅ Service account created successfully!"
echo ""
echo "📧 Service account email: ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo ""
echo "💡 Next steps:"
echo "   1. Grant necessary IAM roles to the service account"
echo "   2. Create and download a service account key (if needed for local development)"
echo "   3. Store the key securely in .secrets/app-backend-sa.json"


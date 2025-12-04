#!/bin/bash

# Setup script to enable required Google Cloud APIs
# Run this once before deploying services

set -e

PROJECT_ID="${GCP_PROJECT_ID:-mikebrooks}"

echo "🔧 Setting up GCP project: ${PROJECT_ID}"
echo ""

# Set the project
echo "📋 Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Authenticate (if not already done)
echo ""
echo "🔐 Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "⚠️  Not authenticated. Please run:"
    echo "   gcloud auth login"
    echo "   gcloud auth application-default login"
    exit 1
fi

# Enable required APIs
echo ""
echo "🚀 Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com

echo ""
echo "✅ All APIs enabled successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Deploy UI service: ./scripts/deploy_ui.sh"
echo "   2. Deploy API service: ./scripts/deploy_api.sh"


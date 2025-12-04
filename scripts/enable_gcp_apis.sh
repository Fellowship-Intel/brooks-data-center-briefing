#!/bin/bash

# Enable required GCP APIs for the Michael Brooks report service
# Prerequisites:
# - gcloud CLI installed and authenticated
# - GCP project "mikebrooks" set up

set -e

PROJECT_ID="mikebrooks"

echo "🔧 Enabling required GCP APIs for project: ${PROJECT_ID}"
echo "=================================================="
echo ""

# Set the project
echo "📋 Setting GCP project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

echo ""
echo "🚀 Enabling APIs..."
echo ""

# Enable Cloud Run API
echo "1️⃣  Enabling Cloud Run API..."
gcloud services enable run.googleapis.com

# Enable Firestore API
echo "2️⃣  Enabling Firestore API..."
gcloud services enable firestore.googleapis.com

# Enable Cloud Storage API
echo "3️⃣  Enabling Cloud Storage API..."
gcloud services enable storage.googleapis.com

# Enable Secret Manager API
echo "4️⃣  Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Enable Cloud Build API
echo "5️⃣  Enabling Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com

# Enable Container Registry API
echo "6️⃣  Enabling Container Registry API..."
gcloud services enable containerregistry.googleapis.com

echo ""
echo "=================================================="
echo "✅ All required APIs enabled!"
echo ""
echo "💡 Note: API enablement may take a few minutes to propagate."
echo "   You can check status with: gcloud services list --enabled"


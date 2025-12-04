#!/bin/bash

# Complete GCP project setup for the Michael Brooks report service
# This script sets up:
# 1. Enables required APIs
# 2. Creates Cloud Storage bucket
# 3. Creates service account
# 4. Grants necessary IAM roles
#
# Prerequisites:
# - gcloud CLI installed and authenticated
# - GCP project "mikebrooks" exists

set -e

PROJECT_ID="mikebrooks"
SERVICE_ACCOUNT_NAME="app-backend-sa"
BUCKET_NAME="mikebrooks-reports"
REGION="us-central1"

echo "🚀 Setting up GCP project: ${PROJECT_ID}"
echo "=================================================="
echo ""

# Set the project
echo "📋 Setting GCP project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

echo ""
echo "=================================================="
echo "Step 1: Enabling required APIs"
echo "=================================================="
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
echo "Step 2: Creating Cloud Storage bucket"
echo "=================================================="
echo ""

# Check if bucket already exists
if gsutil ls -b gs://${BUCKET_NAME} 2>/dev/null; then
    echo "⚠️  Bucket ${BUCKET_NAME} already exists, skipping creation."
else
    echo "📦 Creating bucket: ${BUCKET_NAME}..."
    gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${BUCKET_NAME}
    echo "✅ Bucket created successfully!"
fi

echo ""
echo "=================================================="
echo "Step 3: Creating service account"
echo "=================================================="
echo ""

# Check if service account already exists
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} 2>/dev/null; then
    echo "⚠️  Service account ${SERVICE_ACCOUNT_NAME} already exists, skipping creation."
else
    echo "👤 Creating service account: ${SERVICE_ACCOUNT_NAME}..."
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
      --display-name="App Backend Service Account" \
      --project=${PROJECT_ID}
    echo "✅ Service account created successfully!"
fi

echo ""
echo "=================================================="
echo "Step 4: Granting IAM roles"
echo "=================================================="
echo ""

echo "🔐 Granting IAM roles to service account..."
echo ""

# Grant Firestore User role
echo "  - roles/datastore.user (Firestore)"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/datastore.user" \
  --quiet

# Grant Storage Object Admin role
echo "  - roles/storage.objectAdmin (Cloud Storage)"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectAdmin" \
  --quiet

# Grant Secret Manager Secret Accessor role
echo "  - roles/secretmanager.secretAccessor (Secret Manager)"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet

# Grant Cloud Run Invoker role (if needed for Cloud Run)
echo "  - roles/run.invoker (Cloud Run - optional)"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/run.invoker" \
  --quiet

echo ""
echo "=================================================="
echo "✅ GCP project setup complete!"
echo "=================================================="
echo ""
echo "📋 Summary:"
echo "  - Project ID: ${PROJECT_ID}"
echo "  - Service Account: ${SERVICE_ACCOUNT_EMAIL}"
echo "  - Storage Bucket: gs://${BUCKET_NAME}"
echo ""
echo "💡 Next steps:"
echo "  1. Create a service account key for local development:"
echo "     gcloud iam service-accounts keys create .secrets/app-backend-sa.json \\"
echo "       --iam-account=${SERVICE_ACCOUNT_EMAIL}"
echo ""
echo "  2. Set environment variables:"
echo "     export REPORTS_BUCKET_NAME=${BUCKET_NAME}"
echo "     export GCP_PROJECT_ID=${PROJECT_ID}"
echo ""
echo "  3. Add secrets to Secret Manager:"
echo "     echo -n 'your-api-key' | gcloud secrets create GEMINI_API_KEY \\"
echo "       --data-file=- --project=${PROJECT_ID}"


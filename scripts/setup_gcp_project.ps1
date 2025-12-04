# Complete GCP project setup for the Michael Brooks report service (PowerShell version)
# This script sets up:
# 1. Enables required APIs
# 2. Creates Cloud Storage bucket
# 3. Creates service account
# 4. Grants necessary IAM roles
#
# Prerequisites:
# - gcloud CLI installed and authenticated
# - GCP project "mikebrooks" exists

$ErrorActionPreference = "Stop"

$PROJECT_ID = "mikebrooks"
$SERVICE_ACCOUNT_NAME = "app-backend-sa"
$BUCKET_NAME = "mikebrooks-reports"
$REGION = "us-central1"

Write-Host "🚀 Setting up GCP project: ${PROJECT_ID}" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Set the project
Write-Host "📋 Setting GCP project to ${PROJECT_ID}..." -ForegroundColor Yellow
gcloud config set project ${PROJECT_ID}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Step 1: Enabling required APIs" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Enable Cloud Run API
Write-Host "1️⃣  Enabling Cloud Run API..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com

# Enable Firestore API
Write-Host "2️⃣  Enabling Firestore API..." -ForegroundColor Yellow
gcloud services enable firestore.googleapis.com

# Enable Cloud Storage API
Write-Host "3️⃣  Enabling Cloud Storage API..." -ForegroundColor Yellow
gcloud services enable storage.googleapis.com

# Enable Secret Manager API
Write-Host "4️⃣  Enabling Secret Manager API..." -ForegroundColor Yellow
gcloud services enable secretmanager.googleapis.com

# Enable Cloud Build API
Write-Host "5️⃣  Enabling Cloud Build API..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com

# Enable Container Registry API
Write-Host "6️⃣  Enabling Container Registry API..." -ForegroundColor Yellow
gcloud services enable containerregistry.googleapis.com

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Step 2: Creating Cloud Storage bucket" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if bucket already exists
$bucketExists = $false
try {
    gsutil ls -b "gs://${BUCKET_NAME}" 2>$null | Out-Null
    $bucketExists = $true
} catch {
    $bucketExists = $false
}

if ($bucketExists) {
    Write-Host "⚠️  Bucket ${BUCKET_NAME} already exists, skipping creation." -ForegroundColor Yellow
} else {
    Write-Host "📦 Creating bucket: ${BUCKET_NAME}..." -ForegroundColor Yellow
    gsutil mb -p ${PROJECT_ID} -l ${REGION} "gs://${BUCKET_NAME}"
    Write-Host "✅ Bucket created successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Step 3: Creating service account" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if service account already exists
$SERVICE_ACCOUNT_EMAIL = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
$saExists = $false
try {
    gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} 2>$null | Out-Null
    $saExists = $true
} catch {
    $saExists = $false
}

if ($saExists) {
    Write-Host "⚠️  Service account ${SERVICE_ACCOUNT_NAME} already exists, skipping creation." -ForegroundColor Yellow
} else {
    Write-Host "👤 Creating service account: ${SERVICE_ACCOUNT_NAME}..." -ForegroundColor Yellow
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} `
      --display-name="App Backend Service Account" `
      --project=${PROJECT_ID}
    Write-Host "✅ Service account created successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Step 4: Granting IAM roles" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔐 Granting IAM roles to service account..." -ForegroundColor Yellow
Write-Host ""

# Grant Firestore User role
Write-Host "  - roles/datastore.user (Firestore)" -ForegroundColor Cyan
gcloud projects add-iam-policy-binding ${PROJECT_ID} `
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" `
  --role="roles/datastore.user" `
  --quiet

# Grant Storage Object Admin role
Write-Host "  - roles/storage.objectAdmin (Cloud Storage)" -ForegroundColor Cyan
gcloud projects add-iam-policy-binding ${PROJECT_ID} `
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" `
  --role="roles/storage.objectAdmin" `
  --quiet

# Grant Secret Manager Secret Accessor role
Write-Host "  - roles/secretmanager.secretAccessor (Secret Manager)" -ForegroundColor Cyan
gcloud projects add-iam-policy-binding ${PROJECT_ID} `
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" `
  --role="roles/secretmanager.secretAccessor" `
  --quiet

# Grant Cloud Run Invoker role (if needed for Cloud Run)
Write-Host "  - roles/run.invoker (Cloud Run - optional)" -ForegroundColor Cyan
gcloud projects add-iam-policy-binding ${PROJECT_ID} `
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" `
  --role="roles/run.invoker" `
  --quiet

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "✅ GCP project setup complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "  - Project ID: ${PROJECT_ID}" -ForegroundColor White
Write-Host "  - Service Account: ${SERVICE_ACCOUNT_EMAIL}" -ForegroundColor White
Write-Host "  - Storage Bucket: gs://${BUCKET_NAME}" -ForegroundColor White
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create a service account key for local development:" -ForegroundColor Yellow
Write-Host "     gcloud iam service-accounts keys create .secrets/app-backend-sa.json \`" -ForegroundColor Gray
Write-Host "       --iam-account=${SERVICE_ACCOUNT_EMAIL}" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Set environment variables:" -ForegroundColor Yellow
Write-Host "     `$env:REPORTS_BUCKET_NAME=`"${BUCKET_NAME}`"" -ForegroundColor Gray
Write-Host "     `$env:GCP_PROJECT_ID=`"${PROJECT_ID}`"" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Add secrets to Secret Manager:" -ForegroundColor Yellow
Write-Host "     echo -n 'your-api-key' | gcloud secrets create GEMINI_API_KEY \`" -ForegroundColor Gray
Write-Host "       --data-file=- --project=${PROJECT_ID}" -ForegroundColor Gray


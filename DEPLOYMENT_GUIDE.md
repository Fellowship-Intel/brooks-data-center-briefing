# Deployment Guide for Cloud Run Services

This guide walks you through deploying both the UI (Streamlit) and API (FastAPI) services to Google Cloud Run.

## Prerequisites

1. **Google Cloud SDK installed** - [Install gcloud CLI](https://cloud.google.com/sdk/docs/install)
2. **Docker installed** (for local testing, Cloud Build handles this in the cloud)
3. **GCP Project set up** - Project ID: `mikebrooks` (or update in scripts)

## Step 1: Authenticate with Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set up Application Default Credentials (for local development)
gcloud auth application-default login
```

## Step 2: Set Your Project

```bash
gcloud config set project mikebrooks
```

## Step 3: Enable Required APIs

Run this once to enable all required APIs:

**Bash:**
```bash
./scripts/setup_gcp_apis.sh
```

**PowerShell:**
```powershell
.\scripts\setup_gcp_apis.ps1
```

**Or manually:**
```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

## Step 4: Create Artifact Registry Repository

Create a Docker repository in Artifact Registry:

```bash
gcloud artifacts repositories create brooks-reports-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Container images for Brooks Daily Briefing"
```

## Step 5: Set Environment Variables

**Bash:**
```bash
export GCP_PROJECT_ID="mikebrooks"
export REPORTS_BUCKET_NAME="mikebrooks-reports"
export REGION="us-central1"
export REPO="brooks-reports-repo"

export IMAGE_UI="${REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${REPO}/brooks-ui"
export IMAGE_API="${REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${REPO}/brooks-api"
```

**PowerShell:**
```powershell
$env:GCP_PROJECT_ID = "mikebrooks"
$env:REPORTS_BUCKET_NAME = "mikebrooks-reports"
$env:REGION = "us-central1"
$env:REPO = "brooks-reports-repo"

$env:IMAGE_UI = "${env:REGION}-docker.pkg.dev/${env:GCP_PROJECT_ID}/${env:REPO}/brooks-ui"
$env:IMAGE_API = "${env:REGION}-docker.pkg.dev/${env:GCP_PROJECT_ID}/${env:REPO}/brooks-api"
```

## Step 6: Deploy API Service (Deploy First)

The API service should be deployed first so the UI can reference its URL.

**Bash:**
```bash
./scripts/deploy_api.sh
```

**PowerShell:**
```powershell
.\scripts\deploy_api.ps1
```

**Or manually:**
```bash
# Build the image
gcloud builds submit --tag "${IMAGE_API}" --file Dockerfile.api

# Deploy to Cloud Run
gcloud run deploy brooks-api \
  --image="${IMAGE_API}" \
  --platform=managed \
  --region="${REGION}" \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=1Gi \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID},REPORTS_BUCKET_NAME=${REPORTS_BUCKET_NAME}" \
  --port=8080
```

## Step 7: Deploy UI Service

**Bash:**
```bash
./scripts/deploy_ui.sh
```

**PowerShell:**
```powershell
.\scripts\deploy_ui.ps1
```

**Or manually:**
```bash
# Build the image
gcloud builds submit --tag "${IMAGE_UI}" --file Dockerfile.ui

# Deploy to Cloud Run
gcloud run deploy brooks-briefing-ui \
  --image="${IMAGE_UI}" \
  --platform=managed \
  --region="${REGION}" \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=1Gi \
  --port=8501 \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID},REPORTS_BUCKET_NAME=${REPORTS_BUCKET_NAME}" \
  --command="streamlit" \
  --args="run,app.py,--server.port=8501,--server.address=0.0.0.0"
```

## Step 8: Link UI to API (Optional)

If you want the UI to call the API service, update the UI service with the API URL:

```bash
# Get the API URL
API_URL=$(gcloud run services describe brooks-api --region ${REGION} --format 'value(status.url)')

# Update UI service with API URL
gcloud run services update brooks-briefing-ui \
  --region ${REGION} \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID},REPORTS_BUCKET_NAME=${REPORTS_BUCKET_NAME},API_URL=${API_URL}"
```

## Service URLs

After deployment, get your service URLs:

```bash
# UI Service URL
gcloud run services describe brooks-briefing-ui --region ${REGION} --format 'value(status.url)'

# API Service URL
gcloud run services describe brooks-api --region ${REGION} --format 'value(status.url)'
```

## Updating Services

To update a service after code changes:

1. **Rebuild and redeploy:**
   ```bash
   # For UI
   gcloud builds submit --tag "${IMAGE_UI}" --file Dockerfile.ui
   gcloud run deploy brooks-briefing-ui --image="${IMAGE_UI}" --region="${REGION}"
   
   # For API
   gcloud builds submit --tag "${IMAGE_API}" --file Dockerfile.api
   gcloud run deploy brooks-api --image="${IMAGE_API}" --region="${REGION}"
   ```

2. **Or use the deployment scripts** (they handle rebuild automatically)

## Troubleshooting

### Check service logs:
```bash
# UI logs
gcloud run services logs read brooks-briefing-ui --region ${REGION}

# API logs
gcloud run services logs read brooks-api --region ${REGION}
```

### Check service status:
```bash
gcloud run services list --region ${REGION}
```

### View service details:
```bash
gcloud run services describe brooks-briefing-ui --region ${REGION}
gcloud run services describe brooks-api --region ${REGION}
```

## Notes

- **Ports**: UI uses port 8501 (Streamlit default), API uses port 8080
- **Memory**: Both services use 1Gi memory and 1 CPU
- **Authentication**: Both services are set to `--allow-unauthenticated` for public access
- **Environment Variables**: Set via `--set-env-vars` during deployment
- **Artifact Registry**: Images are stored in Artifact Registry, not Container Registry (gcr.io)


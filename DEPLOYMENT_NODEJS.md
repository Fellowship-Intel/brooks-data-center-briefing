# Node.js Deployment Guide

This document provides comprehensive instructions for deploying the Brooks Data Center Daily Briefing application with the Node.js backend.

## Architecture Overview

The application consists of three main services:

1. **Node.js API** (`brooks-briefing-api-nodejs`)
   - Express.js REST API
   - TypeScript backend
   - Handles report generation, chat, and data access
   - Deployed to Cloud Run

2. **React Frontend** (`brooks-briefing-react`)
   - React + Vite SPA
   - Served via nginx
   - Deployed to Cloud Run

3. **Streamlit UI** (`brooks-briefing-ui`)
   - Python Streamlit interface
   - Calls Node.js API
   - Deployed to Cloud Run

## Prerequisites

- Google Cloud SDK installed and authenticated
- GCP Project created (`mikebrooks` or your project ID)
- Billing enabled on GCP project
- Required permissions to create Cloud Run services, Artifact Registry, and manage secrets

## Step-by-Step Deployment

### 1. Initial GCP Setup

Run the setup script to enable all required APIs:

```powershell
.\scripts\setup_gcp_apis.ps1
```

Or manually:

```bash
gcloud config set project mikebrooks
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

### 2. Create Artifact Registry Repository

```bash
gcloud artifacts repositories create brooks-reports-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for Brooks Briefing services"
```

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create brooks-briefing-api-nodejs \
  --display-name="Brooks Briefing API Node.js Service Account"

# Grant required roles
PROJECT_ID="mikebrooks"
SA_EMAIL="brooks-briefing-api-nodejs@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

### 4. Store Secrets in Secret Manager

```bash
# Store Gemini API key
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Store Eleven Labs API key
echo -n "your-eleven-labs-api-key" | gcloud secrets create ELEVEN_LABS_API_KEY --data-file=-

# Grant access to service account
SA_EMAIL="brooks-briefing-api-nodejs@mikebrooks.iam.gserviceaccount.com"

gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding ELEVEN_LABS_API_KEY \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

### 5. Verify Cloud Storage Bucket

```bash
# Check if bucket exists
gsutil ls gs://mikebrooks-reports

# If it doesn't exist, create it
gsutil mb -p mikebrooks -l us-central1 gs://mikebrooks-reports
```

### 6. Verify Firestore Database

```bash
# Check Firestore status
gcloud firestore databases describe --database="(default)"

# If not initialized, create it (Native mode)
gcloud firestore databases create --region=us-central1
```

### 7. Deploy Node.js API

```powershell
# PowerShell
$env:GCP_PROJECT_ID = "mikebrooks"
$env:REPORTS_BUCKET_NAME = "mikebrooks-reports"
.\scripts\deploy_api_nodejs.ps1
```

```bash
# Bash
export GCP_PROJECT_ID="mikebrooks"
export REPORTS_BUCKET_NAME="mikebrooks-reports"
chmod +x scripts/deploy_api_nodejs.sh
./scripts/deploy_api_nodejs.sh
```

**Save the API URL** from the output - you'll need it for the frontends.

### 8. Deploy React Frontend

```powershell
# PowerShell
.\scripts\deploy_react.ps1
```

```bash
# Bash
chmod +x scripts/deploy_react.sh
./scripts/deploy_react.sh
```

**Save the React URL** from the output.

### 9. Deploy Streamlit UI

```powershell
# PowerShell
.\scripts\deploy_ui.ps1
```

```bash
# Bash
chmod +x scripts/deploy_ui.sh
./scripts/deploy_ui.sh
```

**Save the Streamlit URL** from the output.

### 10. Update CORS Configuration

After deploying both frontends, update the API service to allow CORS:

```bash
API_URL="https://brooks-briefing-api-nodejs-xxx.run.app"
REACT_URL="https://brooks-briefing-react-xxx.run.app"
STREAMLIT_URL="https://brooks-briefing-ui-xxx.run.app"

gcloud run services update brooks-briefing-api-nodejs \
  --region us-central1 \
  --set-env-vars="REACT_APP_URL=${REACT_URL},STREAMLIT_APP_URL=${STREAMLIT_URL}"
```

## Verification

### Test API Health Endpoint

```bash
curl https://YOUR_API_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "components": {
    "firestore": "healthy",
    "storage": "healthy",
    "gemini": "healthy"
  }
}
```

### Test Report Generation

```bash
curl -X POST https://YOUR_API_URL/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-01",
    "watchlist": ["AAPL", "MSFT"],
    "marketData": {}
  }'
```

### Test Frontends

1. Open React frontend URL in browser
2. Open Streamlit UI URL in browser
3. Try generating a report from both interfaces

## Environment Variables

See [DEPLOYMENT_ENV_VARS.md](./DEPLOYMENT_ENV_VARS.md) for detailed environment variable documentation.

## Troubleshooting

### API Not Starting

- Check Cloud Run logs: `gcloud run services logs read brooks-briefing-api-nodejs --region us-central1`
- Verify environment variables are set correctly
- Check service account permissions

### CORS Errors

- Ensure `REACT_APP_URL` and `STREAMLIT_APP_URL` are set in API service
- Verify URLs don't have trailing slashes
- Check browser console for specific CORS error messages

### Secrets Not Found

- Verify secrets exist: `gcloud secrets list`
- Check service account has `secretAccessor` role
- Verify secret names match exactly (case-sensitive)

### Build Failures

- Check Dockerfile syntax
- Verify all dependencies are in package.json
- Check Cloud Build logs: `gcloud builds list --limit=5`

## CI/CD

The application includes GitHub Actions workflows for automated deployment:

- **`.github/workflows/deploy.yml`**: Deploys all three services to Cloud Run
- **`.github/workflows/test.yml`**: Runs tests before deployment

See the workflow files for configuration details.

## Service URLs

After deployment, note these URLs:

- **API**: `https://brooks-briefing-api-nodejs-xxx.run.app`
- **React**: `https://brooks-briefing-react-xxx.run.app`
- **Streamlit**: `https://brooks-briefing-ui-xxx.run.app`

## Next Steps

- Set up custom domains
- Configure monitoring and alerts
- Set up auto-scaling policies
- Configure backup and disaster recovery


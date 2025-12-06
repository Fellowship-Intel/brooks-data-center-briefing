# Quick Deployment Guide - Node.js Version

This guide provides a quick reference for deploying the Brooks Data Center Daily Briefing application with the Node.js backend.

## Prerequisites

1. **Google Cloud SDK** installed and authenticated
2. **GCP Project** created and configured
3. **Required APIs** enabled
4. **Service Account** with proper permissions
5. **Secrets** stored in Secret Manager

## One-Command Setup

Run the setup script to enable all required APIs:

```powershell
# PowerShell
.\scripts\setup_gcp_apis.ps1
```

```bash
# Bash
./scripts/setup_gcp_apis.sh
```

## Deployment Steps

### 1. Set Environment Variables

```powershell
# PowerShell
$env:GCP_PROJECT_ID = "mikebrooks"
$env:REPORTS_BUCKET_NAME = "mikebrooks-reports"
$env:REGION = "us-central1"
```

```bash
# Bash
export GCP_PROJECT_ID="mikebrooks"
export REPORTS_BUCKET_NAME="mikebrooks-reports"
export REGION="us-central1"
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
gcloud iam service-accounts create brooks-briefing-api-nodejs \
  --display-name="Brooks Briefing API Node.js Service Account"

# Grant required roles
gcloud projects add-iam-policy-binding mikebrooks \
  --member="serviceAccount:brooks-briefing-api-nodejs@mikebrooks.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud projects add-iam-policy-binding mikebrooks \
  --member="serviceAccount:brooks-briefing-api-nodejs@mikebrooks.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding mikebrooks \
  --member="serviceAccount:brooks-briefing-api-nodejs@mikebrooks.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding mikebrooks \
  --member="serviceAccount:brooks-briefing-api-nodejs@mikebrooks.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 4. Store Secrets in Secret Manager

```bash
# Store Gemini API key
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Store Eleven Labs API key
echo -n "your-eleven-labs-api-key" | gcloud secrets create ELEVEN_LABS_API_KEY --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:brooks-briefing-api-nodejs@mikebrooks.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding ELEVEN_LABS_API_KEY \
  --member="serviceAccount:brooks-briefing-api-nodejs@mikebrooks.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 5. Deploy Node.js API

```powershell
# PowerShell
.\scripts\deploy_api_nodejs.ps1
```

```bash
# Bash
chmod +x scripts/deploy_api_nodejs.sh
./scripts/deploy_api_nodejs.sh
```

**Note the API URL** from the output - you'll need it for the frontends.

### 6. Deploy React Frontend

```powershell
# PowerShell
.\scripts\deploy_react.ps1
```

```bash
# Bash
chmod +x scripts/deploy_react.sh
./scripts/deploy_react.sh
```

**Note the React URL** from the output.

### 7. Deploy Streamlit UI

```powershell
# PowerShell
.\scripts\deploy_ui.ps1
```

```bash
# Bash
chmod +x scripts/deploy_ui.sh
./scripts/deploy_ui.sh
```

**Note the Streamlit URL** from the output.

### 8. Update CORS in API

After deploying both frontends, update the API service to allow CORS from both origins:

```bash
API_URL="https://brooks-briefing-api-nodejs-xxx.run.app"
REACT_URL="https://brooks-briefing-react-xxx.run.app"
STREAMLIT_URL="https://brooks-briefing-ui-xxx.run.app"

gcloud run services update brooks-briefing-api-nodejs \
  --region us-central1 \
  --set-env-vars="REACT_APP_URL=${REACT_URL},STREAMLIT_APP_URL=${STREAMLIT_URL}"
```

## Verification

### Test API Health

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

### Test API Endpoints

```bash
# Generate a report
curl -X POST https://YOUR_API_URL/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-01",
    "watchlist": ["AAPL", "MSFT"],
    "marketData": {}
  }'

# Get a report
curl https://YOUR_API_URL/reports/2024-01-01
```

### Test Frontends

1. Open React frontend URL in browser
2. Open Streamlit UI URL in browser
3. Try generating a report from both interfaces

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

## Service URLs

After deployment, note these URLs:

- **API**: `https://brooks-briefing-api-nodejs-xxx.run.app`
- **React**: `https://brooks-briefing-react-xxx.run.app`
- **Streamlit**: `https://brooks-briefing-ui-xxx.run.app`

## Next Steps

- Set up CI/CD with GitHub Actions
- Configure custom domains
- Set up monitoring and alerts
- Configure auto-scaling policies


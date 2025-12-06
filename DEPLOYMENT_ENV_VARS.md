# Environment Variables for Deployment

This document lists all required and optional environment variables for deploying the Brooks Data Center Daily Briefing application.

## Node.js API Service (brooks-briefing-api-nodejs)

### Required Variables

- **GCP_PROJECT_ID**: Google Cloud Project ID (default: `mikebrooks`)
- **REPORTS_BUCKET_NAME**: Cloud Storage bucket name for storing reports (default: `mikebrooks-reports`)
- **PORT**: Port number for the API server (default: `8000`)

### Optional Variables

- **ENVIRONMENT**: Environment name (`development`, `production`) (default: `development`)
- **GEMINI_API_KEY**: Google Gemini API key (if not provided, will use Secret Manager)
- **GOOGLE_API_KEY**: Alternative name for Gemini API key
- **ELEVEN_LABS_API_KEY**: Eleven Labs API key for TTS (if not provided, will use Secret Manager)
- **GEMINI_MODEL_NAME**: Gemini model to use (default: `gemini-1.5-pro`)
- **REACT_APP_URL**: React frontend URL for CORS (production only)
- **STREAMLIT_APP_URL**: Streamlit frontend URL for CORS (production only)
- **SENTRY_DSN**: Sentry DSN for error tracking (optional)

### Secret Manager Secrets

The following secrets should be stored in Google Cloud Secret Manager:

- **GEMINI_API_KEY**: Google Gemini API key
- **ELEVEN_LABS_API_KEY**: Eleven Labs API key

The service account must have the `Secret Manager Secret Accessor` role to access these secrets.

## React Frontend (brooks-briefing-react)

### Build-time Variables

- **VITE_API_URL**: URL of the Node.js API service (injected at build time)

### Runtime Variables

- None required (all configuration is baked into the build)

## Streamlit UI (brooks-briefing-ui)

### Required Variables

- **GCP_PROJECT_ID**: Google Cloud Project ID (default: `mikebrooks`)
- **REPORTS_BUCKET_NAME**: Cloud Storage bucket name (default: `mikebrooks-reports`)

### Optional Variables

- **API_URL**: URL of the Node.js API service (if not provided, will use default)

## Setting Environment Variables in Cloud Run

### Using gcloud CLI

```bash
gcloud run services update SERVICE_NAME \
  --region REGION \
  --set-env-vars="VAR1=value1,VAR2=value2"
```

### Using Secret Manager

For sensitive values, use Secret Manager:

```bash
# Create secret
gcloud secrets create SECRET_NAME --data-file=- <<< "secret-value"

# Grant access to service account
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Reference in Cloud Run
gcloud run services update SERVICE_NAME \
  --region REGION \
  --update-secrets="ENV_VAR_NAME=SECRET_NAME:latest"
```

## Example Production Configuration

### Node.js API

```bash
gcloud run services update brooks-briefing-api-nodejs \
  --region us-central1 \
  --set-env-vars="GCP_PROJECT_ID=mikebrooks,REPORTS_BUCKET_NAME=mikebrooks-reports,ENVIRONMENT=production,REACT_APP_URL=https://brooks-briefing-react-xxx.run.app,STREAMLIT_APP_URL=https://brooks-briefing-ui-xxx.run.app" \
  --update-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest,ELEVEN_LABS_API_KEY=ELEVEN_LABS_API_KEY:latest"
```

### React Frontend

The API URL is injected at build time via the deployment script.

### Streamlit UI

```bash
gcloud run services update brooks-briefing-ui \
  --region us-central1 \
  --set-env-vars="GCP_PROJECT_ID=mikebrooks,REPORTS_BUCKET_NAME=mikebrooks-reports,API_URL=https://brooks-briefing-api-nodejs-xxx.run.app"
```


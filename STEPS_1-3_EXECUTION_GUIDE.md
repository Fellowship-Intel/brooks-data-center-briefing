# Steps 1-3 Execution Guide

This guide provides the exact commands to execute steps 1-3: Install dependencies, test locally, and deploy.

## Step 1: Install Dependencies

### Windows PowerShell

```powershell
# Navigate to server directory
cd C:\Dev\Brooks\server

# Install dependencies
npm install
```

**Expected Output:**
- All packages download and install
- No errors
- `node_modules/` directory populated
- New packages installed: express-validator, express-rate-limit, helmet, connect-timeout, uuid

**Verification:**
```powershell
# Check if new packages are installed
npm list express-validator express-rate-limit helmet connect-timeout uuid
```

### Linux/Mac

```bash
cd server
npm install
```

## Step 2: Test Locally

### 2.1 Type Check

```powershell
# PowerShell
cd C:\Dev\Brooks\server
npm run type-check
```

```bash
# Bash
cd server
npm run type-check
```

**Expected:** No TypeScript errors, compilation successful.

### 2.2 Build

```powershell
npm run build
```

**Expected:**
- TypeScript compiles successfully
- `dist/` directory created
- JavaScript files in `dist/` directory

**Verification:**
```powershell
# Check dist directory exists
Test-Path dist/index.js
# Should return True
```

### 2.3 Set Environment Variables

**PowerShell:**
```powershell
$env:GCP_PROJECT_ID = "mikebrooks"
$env:REPORTS_BUCKET_NAME = "mikebrooks-reports"
$env:PORT = "8000"
$env:ENVIRONMENT = "development"

# For local GCP credentials
$env:GOOGLE_APPLICATION_CREDENTIALS = ".secrets\app-backend-sa.json"
```

**Bash:**
```bash
export GCP_PROJECT_ID="mikebrooks"
export REPORTS_BUCKET_NAME="mikebrooks-reports"
export PORT="8000"
export ENVIRONMENT="development"
export GOOGLE_APPLICATION_CREDENTIALS=".secrets/app-backend-sa.json"
```

### 2.4 Start Server

```powershell
npm start
```

**Expected Output:**
```
Environment validation passed
2025-01-27 12:00:00 [info]: Server running on port 8000
2025-01-27 12:00:00 [info]: Environment: development
2025-01-27 12:00:00 [info]: Server ready to accept connections
```

### 2.5 Run Tests (in another terminal)

**Test Health Endpoint:**
```powershell
# PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -ExpandProperty Content
```

```bash
# Bash
curl http://localhost:8000/health
```

**Expected:** JSON response with health status.

**Test Root Endpoint:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/ | Select-Object -ExpandProperty Content
```

**Test Validation:**
```powershell
$body = @{ trading_date = "invalid-date" } | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/reports/generate -Method POST -Body $body -ContentType "application/json"
```

**Expected:** 400 Bad Request with validation errors.

**Test Request ID:**
```powershell
$response = Invoke-WebRequest -Uri http://localhost:8000/health
$response.Headers['X-Request-ID']
```

**Expected:** UUID string.

### 2.6 Stop Server

Press `Ctrl+C` to stop the server.

**Expected:** Server logs "Received SIGINT, starting graceful shutdown..." and exits cleanly.

## Step 3: Deploy to Production

### 3.1 Pre-Deployment Setup

**PowerShell:**
```powershell
# Set deployment variables
$env:GCP_PROJECT_ID = "mikebrooks"
$env:REPORTS_BUCKET_NAME = "mikebrooks-reports"
$env:REGION = "us-central1"

# Optional: Set CORS origins (update after frontends are deployed)
# $env:REACT_APP_URL = "https://brooks-briefing-react-xxx.run.app"
# $env:STREAMLIT_APP_URL = "https://brooks-briefing-ui-xxx.run.app"
```

**Bash:**
```bash
export GCP_PROJECT_ID="mikebrooks"
export REPORTS_BUCKET_NAME="mikebrooks-reports"
export REGION="us-central1"
```

### 3.2 Deploy

**PowerShell:**
```powershell
# From project root
cd C:\Dev\Brooks
.\scripts\deploy_api_nodejs.ps1
```

**Bash:**
```bash
cd /path/to/Brooks
./scripts/deploy_api_nodejs.sh
```

**Expected Output:**
```
🚀 Building and deploying Node.js API service to Cloud Run...
Project: mikebrooks
Service: brooks-briefing-api-nodejs
Region: us-central1
Repository: brooks-reports-repo

🔨 Building Docker image...
[Build output...]

🚀 Deploying to Cloud Run...
[Deployment output...]

✅ Node.js API service deployed successfully!

📝 Service URL:
https://brooks-briefing-api-nodejs-xxx-uc.a.run.app

💡 Update frontend services with this API URL:
   React: Set VITE_API_URL=https://brooks-briefing-api-nodejs-xxx-uc.a.run.app
   Streamlit: Set API_URL=https://brooks-briefing-api-nodejs-xxx-uc.a.run.app
```

### 3.3 Post-Deployment Verification

**Save the API URL from the output, then test:**

```powershell
# Test health endpoint
$API_URL = "https://brooks-briefing-api-nodejs-xxx-uc.a.run.app"
Invoke-WebRequest -Uri "$API_URL/health" | Select-Object -ExpandProperty Content
```

**Expected:** JSON with all components healthy.

**Check Security Headers:**
```powershell
$response = Invoke-WebRequest -Uri "$API_URL/health"
$response.Headers
```

**Expected:** Security headers present (X-Content-Type-Options, X-Frame-Options, etc.)

**Check Logs:**
```powershell
gcloud run services logs read brooks-briefing-api-nodejs --region us-central1 --limit 20
```

**Expected:**
- "Environment validation passed"
- "Server running on port 8000"
- Request IDs in logs
- No critical errors

### 3.4 Update Frontend Services

After deploying both frontends, update CORS:

```powershell
$API_URL = "https://brooks-briefing-api-nodejs-xxx-uc.a.run.app"
$REACT_URL = "https://brooks-briefing-react-xxx-uc.a.run.app"
$STREAMLIT_URL = "https://brooks-briefing-ui-xxx-uc.a.run.app"

# Update API CORS
gcloud run services update brooks-briefing-api-nodejs `
  --region us-central1 `
  --set-env-vars="REACT_APP_URL=${REACT_URL},STREAMLIT_APP_URL=${STREAMLIT_URL}"
```

## Troubleshooting

### npm: command not found

**Solution:**
- Install Node.js from https://nodejs.org/
- Or use nvm (Node Version Manager)
- Verify: `node --version` and `npm --version`

### Environment validation fails

**Error:** "GCP_PROJECT_ID is required"

**Solution:**
- Set `GCP_PROJECT_ID` environment variable
- Or it will default to "mikebrooks" if not set

### Port already in use

**Error:** "Port 8000 is already in use"

**Solution:**
- Change PORT: `$env:PORT = "8001"`
- Or stop the service using port 8000

### Docker build fails

**Error:** Build errors during `gcloud builds submit`

**Solution:**
- Check Dockerfile syntax
- Verify all files are present
- Check Cloud Build logs: `gcloud builds list --limit=5`

### Deployment fails

**Error:** Service deployment errors

**Solution:**
- Check service account permissions
- Verify Artifact Registry exists
- Check Cloud Run quotas
- Review deployment logs

## Success Indicators

✅ Dependencies installed without errors  
✅ TypeScript compiles successfully  
✅ Server starts and responds to requests  
✅ Health endpoint returns healthy status  
✅ Security headers present  
✅ Request IDs in responses  
✅ Docker image builds successfully  
✅ Cloud Run deployment succeeds  
✅ Service URL accessible  
✅ Logs show no critical errors  

## Next Steps After Deployment

1. **Test all endpoints** in production
2. **Monitor logs** for 24 hours
3. **Set up alerting** for health check failures
4. **Update frontend services** with API URL
5. **Configure CORS** with frontend URLs
6. **Document** production URLs

## Quick Reference

**Install:** `cd server && npm install`  
**Build:** `npm run build`  
**Test:** `npm start` (then test endpoints)  
**Deploy:** `.\scripts\deploy_api_nodejs.ps1` (from project root)  
**Verify:** `curl https://YOUR_API_URL/health`


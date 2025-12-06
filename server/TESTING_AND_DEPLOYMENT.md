# Testing and Deployment Guide

## Step 1: Install Dependencies

```bash
cd server
npm install
```

This will install all required dependencies including the new packages:
- `express-validator`
- `express-rate-limit`
- `helmet`
- `connect-timeout`
- `uuid`

## Step 2: Test Locally

### 2.1 Type Check

Verify TypeScript compiles without errors:

```bash
npm run type-check
```

Expected: No errors, compilation successful.

### 2.2 Build

Build the TypeScript code:

```bash
npm run build
```

Expected: Creates `dist/` directory with compiled JavaScript.

### 2.3 Environment Setup

Create a `.env` file in the `server/` directory (or set environment variables):

```bash
# Required
GCP_PROJECT_ID=mikebrooks
REPORTS_BUCKET_NAME=mikebrooks-reports

# Optional (can use Secret Manager instead)
GEMINI_API_KEY=your-key-here
ELEVEN_LABS_API_KEY=your-key-here

# Optional
PORT=8000
ENVIRONMENT=development
```

For local development, also set:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=".secrets/app-backend-sa.json"
```

### 2.4 Start Server

```bash
npm start
```

Or for development with auto-reload:

```bash
npm run dev
```

Expected output:
```
Environment validation passed
Server running on port 8000
Environment: development
Server ready to accept connections
```

### 2.5 Test Endpoints

#### Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected: JSON response with health status, all components healthy.

#### Test Root Endpoint

```bash
curl http://localhost:8000/
```

Expected: JSON with API name, version, status, and requestId.

#### Test Input Validation

```bash
# Should return 400 with validation errors
curl -X POST http://localhost:8000/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"trading_date": "invalid-date"}'
```

Expected: 400 error with validation details.

#### Test Rate Limiting

```bash
# Send multiple rapid requests
for i in {1..15}; do
  curl http://localhost:8000/health
done
```

Expected: After 100 requests in 1 minute, should get 429 Too Many Requests.

#### Test Request Size Limit

```bash
# Create a large payload (>10MB)
curl -X POST http://localhost:8000/reports/generate \
  -H "Content-Type: application/json" \
  -d @large-payload.json
```

Expected: 413 Payload Too Large if payload exceeds 10MB.

#### Test Graceful Shutdown

1. Start server: `npm start`
2. Send SIGTERM: `kill -SIGTERM <pid>` (Linux/Mac) or use Ctrl+C
3. Verify: Server logs "Received SIGTERM, starting graceful shutdown..." and exits cleanly.

### 2.6 Verify Security Headers

```bash
curl -I http://localhost:8000/health
```

Expected headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `X-XSS-Protection: 1; mode=block`
- `X-Request-ID: <uuid>`

### 2.7 Test Request ID Tracking

```bash
curl -v http://localhost:8000/health
```

Expected: Response includes `X-Request-ID` header, and logs include request ID.

## Step 3: Deploy to Production

### 3.1 Pre-Deployment Checklist

- [ ] All dependencies installed
- [ ] TypeScript compiles without errors
- [ ] Local tests pass
- [ ] Environment variables configured in Cloud Run
- [ ] Secrets stored in Secret Manager
- [ ] Service account has required permissions

### 3.2 Build Docker Image

From the project root:

```bash
docker build -t brooks-briefing-api:latest -f server/Dockerfile .
```

Or using the deployment script:

```powershell
# PowerShell
.\scripts\deploy_api_nodejs.ps1
```

```bash
# Bash
./scripts/deploy_api_nodejs.sh
```

### 3.3 Verify Docker Image

```bash
docker run -p 8000:8000 \
  -e GCP_PROJECT_ID=mikebrooks \
  -e REPORTS_BUCKET_NAME=mikebrooks-reports \
  -e GEMINI_API_KEY=your-key \
  brooks-briefing-api:latest
```

Test the containerized version locally before deploying.

### 3.4 Deploy to Cloud Run

Using the deployment script:

```powershell
# Set environment variables
$env:GCP_PROJECT_ID = "mikebrooks"
$env:REPORTS_BUCKET_NAME = "mikebrooks-reports"

# Deploy
.\scripts\deploy_api_nodejs.ps1
```

The script will:
1. Build the Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run
4. Configure environment variables
5. Set up service account
6. Return the service URL

### 3.5 Post-Deployment Verification

#### Test Health Endpoint

```bash
curl https://YOUR_API_URL/health
```

Expected: All components healthy, response time included.

#### Test API Endpoints

```bash
# Generate report
curl -X POST https://YOUR_API_URL/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "trading_date": "2025-01-27",
    "client_id": "mikebrooks",
    "market_data": {
      "tickers": ["SMCI", "IREN"],
      "market_data": []
    }
  }'
```

#### Verify Security Headers

```bash
curl -I https://YOUR_API_URL/health
```

#### Check Logs

```bash
gcloud run services logs read brooks-briefing-api-nodejs \
  --region us-central1 \
  --limit 50
```

Look for:
- Request IDs in logs
- No errors during startup
- Environment validation passed
- Health checks working

### 3.6 Update Frontend Services

After deploying the API, update the frontend services to use the new API URL:

```bash
# Get API URL
API_URL=$(gcloud run services describe brooks-briefing-api-nodejs \
  --region us-central1 \
  --format 'value(status.url)')

# Update React frontend
gcloud run services update brooks-briefing-react \
  --region us-central1 \
  --set-env-vars="VITE_API_URL=${API_URL}"

# Update Streamlit UI
gcloud run services update brooks-briefing-ui \
  --region us-central1 \
  --set-env-vars="API_URL=${API_URL}"

# Update CORS in API
gcloud run services update brooks-briefing-api-nodejs \
  --region us-central1 \
  --set-env-vars="REACT_APP_URL=<REACT_URL>,STREAMLIT_APP_URL=<STREAMLIT_URL>"
```

## Troubleshooting

### Environment Validation Fails

**Error:** "Environment validation failed"

**Solution:**
- Check that `GCP_PROJECT_ID` and `REPORTS_BUCKET_NAME` are set
- Verify port is valid (1-65535)
- Check Cloud Run environment variables are configured

### Rate Limiting Too Strict

**Issue:** Getting 429 errors during normal use

**Solution:**
- Adjust limits in `server/src/middleware/rateLimiter.ts`
- Increase `max` values or `windowMs` duration
- Redeploy after changes

### CORS Errors

**Error:** CORS policy blocking requests

**Solution:**
- Verify `REACT_APP_URL` and `STREAMLIT_APP_URL` are set in API service
- Check URLs don't have trailing slashes
- Verify CORS configuration in `server/src/index.ts`

### Graceful Shutdown Not Working

**Issue:** Server doesn't shut down cleanly

**Solution:**
- Check Cloud Run logs for shutdown messages
- Verify SIGTERM is being sent (Cloud Run does this automatically)
- Check timeout is sufficient (30 seconds default)

## Performance Testing

### Load Test

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Using curl in loop
for i in {1..100}; do
  curl http://localhost:8000/health &
done
wait
```

### Monitor

- Check response times in health endpoint
- Monitor rate limit headers
- Watch for memory leaks
- Check Cloud Run metrics

## Success Criteria

✅ Server starts without errors  
✅ Environment validation passes  
✅ Health endpoint returns 200  
✅ All API endpoints respond correctly  
✅ Input validation works  
✅ Rate limiting active  
✅ Security headers present  
✅ Request IDs in responses  
✅ Graceful shutdown works  
✅ Docker image builds successfully  
✅ Cloud Run deployment successful  
✅ Frontend services can connect  

## Next Steps After Deployment

1. Monitor Cloud Run logs for errors
2. Set up alerting for health check failures
3. Monitor rate limit usage
4. Review security headers
5. Test all endpoints in production
6. Update documentation with production URLs


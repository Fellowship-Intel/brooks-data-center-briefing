# Deployment Verification Checklist

Use this checklist to verify the backend is properly deployed and functioning.

## Pre-Deployment

- [ ] All code changes committed
- [ ] Dependencies updated in `server/package.json`
- [ ] TypeScript compiles without errors (`npm run type-check`)
- [ ] Build succeeds (`npm run build`)
- [ ] Local testing completed

## Deployment Steps

### 1. Install Dependencies

```bash
cd server
npm install
```

**Verify:** No errors, all packages installed.

### 2. Build Verification

```bash
npm run build
```

**Verify:** `dist/` directory created with compiled JavaScript.

### 3. Deploy to Cloud Run

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
./scripts/deploy_api_nodejs.sh
```

**Verify:** Deployment completes successfully, service URL returned.

## Post-Deployment Verification

### Health Check

```bash
curl https://YOUR_API_URL/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T...",
  "components": {
    "firestore": { "status": "healthy" },
    "storage": { "status": "healthy" },
    "secret_manager": { "status": "healthy" },
    "gemini_api": { "status": "available" }
  },
  "responseTimeMs": <number>,
  "requestId": "<uuid>"
}
```

**Check:**
- [ ] Status is "healthy"
- [ ] All components show "healthy" or "available"
- [ ] Response time is reasonable (< 1 second)
- [ ] Request ID is present

### Security Headers

```bash
curl -I https://YOUR_API_URL/health
```

**Check for headers:**
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: SAMEORIGIN`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `X-Request-ID: <uuid>`

### Input Validation

```bash
# Test invalid date format
curl -X POST https://YOUR_API_URL/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"trading_date": "invalid"}'
```

**Expected:** 400 Bad Request with validation error details.

**Check:**
- [ ] Returns 400 status
- [ ] Error message includes validation details
- [ ] Request ID present

### Rate Limiting

```bash
# Send rapid requests
for i in {1..15}; do
  curl https://YOUR_API_URL/health
done
```

**Expected:** After limit exceeded, returns 429 Too Many Requests.

**Check:**
- [ ] Rate limit headers present (`RateLimit-*`)
- [ ] 429 returned when limit exceeded
- [ ] Retry-After header present

### Request Size Limit

```bash
# Create large payload (if possible)
curl -X POST https://YOUR_API_URL/reports/generate \
  -H "Content-Type: application/json" \
  -d @large-file.json
```

**Expected:** 413 Payload Too Large if > 10MB.

### API Functionality

```bash
# Generate report
curl -X POST https://YOUR_API_URL/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "trading_date": "2025-01-27",
    "client_id": "mikebrooks",
    "market_data": {
      "tickers": ["SMCI"],
      "market_data": []
    }
  }'
```

**Check:**
- [ ] Request succeeds or fails gracefully
- [ ] Response includes request ID
- [ ] Error messages are appropriate

### Logs Verification

```bash
gcloud run services logs read brooks-briefing-api-nodejs \
  --region us-central1 \
  --limit 50
```

**Check logs for:**
- [ ] "Environment validation passed"
- [ ] "Server running on port 8000"
- [ ] Request IDs in log entries
- [ ] No critical errors
- [ ] Health checks logging correctly

### Graceful Shutdown Test

```bash
# Get service name
SERVICE_NAME="brooks-briefing-api-nodejs"
REGION="us-central1"

# Update service (triggers new deployment, old instance receives SIGTERM)
gcloud run services update ${SERVICE_NAME} \
  --region ${REGION} \
  --no-traffic
```

**Check logs for:**
- [ ] "Received SIGTERM, starting graceful shutdown..."
- [ ] "HTTP server closed"
- [ ] "Graceful shutdown complete"
- [ ] No abrupt terminations

## Integration Testing

### Frontend Connectivity

1. **Update React Frontend:**
   ```bash
   gcloud run services update brooks-briefing-react \
     --region us-central1 \
     --set-env-vars="VITE_API_URL=https://YOUR_API_URL"
   ```

2. **Update Streamlit UI:**
   ```bash
   gcloud run services update brooks-briefing-ui \
     --region us-central1 \
     --set-env-vars="API_URL=https://YOUR_API_URL"
   ```

3. **Update CORS:**
   ```bash
   gcloud run services update brooks-briefing-api-nodejs \
     --region us-central1 \
     --set-env-vars="REACT_APP_URL=https://REACT_URL,STREAMLIT_APP_URL=https://STREAMLIT_URL"
   ```

### Test Frontends

- [ ] React frontend loads
- [ ] React can call API endpoints
- [ ] Streamlit UI loads
- [ ] Streamlit can call API endpoints
- [ ] No CORS errors in browser console

## Performance Checks

- [ ] Health endpoint responds in < 1 second
- [ ] Report generation completes in reasonable time
- [ ] No memory leaks (monitor over time)
- [ ] Rate limits are appropriate for usage

## Security Verification

- [ ] Security headers present
- [ ] CORS configured correctly
- [ ] Input validation working
- [ ] Rate limiting active
- [ ] No sensitive data in error messages (production)
- [ ] Secrets accessed via Secret Manager

## Success Criteria

All items checked = ✅ **DEPLOYMENT SUCCESSFUL**

If any items fail:
1. Check Cloud Run logs
2. Verify environment variables
3. Check service account permissions
4. Review error messages
5. Consult troubleshooting guide

## Next Steps

After successful deployment:
1. Monitor logs for 24 hours
2. Set up alerting for health check failures
3. Review rate limit usage
4. Optimize if needed
5. Document any issues encountered


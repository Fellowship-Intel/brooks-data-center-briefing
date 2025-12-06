# Quick Start Guide

## Prerequisites Check

Before starting, ensure you have:
- Node.js 20+ installed
- npm installed
- GCP credentials configured
- Required environment variables set

## Step 1: Install Dependencies

```bash
cd server
npm install
```

**Expected:** All packages install successfully, including:
- express-validator
- express-rate-limit
- helmet
- connect-timeout
- uuid

## Step 2: Verify Build

```bash
# Type check
npm run type-check

# Build
npm run build
```

**Expected:** 
- No TypeScript errors
- `dist/` directory created with compiled files

## Step 3: Test Locally

### 3.1 Set Environment Variables

Create `.env` file or export variables:

```bash
export GCP_PROJECT_ID=mikebrooks
export REPORTS_BUCKET_NAME=mikebrooks-reports
export PORT=8000
export ENVIRONMENT=development
```

### 3.2 Start Server

```bash
npm start
```

**Expected Output:**
```
Environment validation passed
Server running on port 8000
Environment: development
Server ready to accept connections
```

### 3.3 Quick Tests

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# Check for request ID
curl -v http://localhost:8000/health | grep X-Request-ID
```

## Step 4: Deploy

```bash
# From project root
cd ..

# Set deployment variables
export GCP_PROJECT_ID=mikebrooks
export REPORTS_BUCKET_NAME=mikebrooks-reports

# Deploy (PowerShell)
.\scripts\deploy_api_nodejs.ps1

# Or (Bash)
./scripts/deploy_api_nodejs.sh
```

## Verification Checklist

After deployment, verify:

- [ ] Health endpoint returns 200
- [ ] All components show "healthy"
- [ ] Request ID header present
- [ ] Security headers present
- [ ] Rate limiting works (test with rapid requests)
- [ ] Input validation works (test with invalid data)
- [ ] Logs show request IDs
- [ ] No startup errors

## Common Issues

**Issue:** "npm: command not found"
- **Solution:** Install Node.js or add npm to PATH

**Issue:** "Environment validation failed"
- **Solution:** Set GCP_PROJECT_ID and REPORTS_BUCKET_NAME

**Issue:** "Port already in use"
- **Solution:** Change PORT or stop other service on port 8000

**Issue:** "GCP credentials not found"
- **Solution:** Set GOOGLE_APPLICATION_CREDENTIALS or use gcloud auth


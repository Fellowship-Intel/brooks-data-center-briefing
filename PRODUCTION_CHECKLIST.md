# Production Deployment Checklist

This checklist ensures the application is ready for production deployment.

## Pre-Deployment Checklist

### Configuration ✅
- [x] Centralized configuration system (`config/app_config.py`)
- [x] Environment variables properly configured
- [x] GCP Secret Manager integration for sensitive keys
- [x] Default values for all configuration options
- [x] Configuration validation on startup

### Security ✅
- [x] Input validation and sanitization (`utils/input_validation.py`)
- [x] Rate limiting implemented
- [x] Error handling with custom exceptions
- [x] API key management via Secret Manager
- [x] XSS protection (HTML escaping)
- [x] DoS protection (JSON depth limits)

### Error Handling ✅
- [x] Custom exception classes with context
- [x] Structured logging
- [x] Sentry integration for error tracking
- [x] Graceful error handling (TTS failures don't break pipeline)
- [x] Retry mechanisms with exponential backoff

### Performance ✅
- [x] Response caching (24-hour TTL for Gemini)
- [x] Firestore query optimization with pagination
- [x] LRU cache for watchlist reports
- [x] Performance metrics collection
- [x] Streamlit optimizations (file watching disabled)

### Testing ✅
- [x] Unit tests for core components
- [x] Integration tests for workflows
- [x] Component tests (progress tracker, keyboard shortcuts)
- [x] End-to-end workflow tests
- [x] Mock fixtures for external services

### Documentation ✅
- [x] API documentation with examples
- [x] Component documentation
- [x] Help center with FAQ
- [x] Quick start guide
- [x] Code comments and docstrings

### Features ✅
- [x] Report generation with AI
- [x] TTS audio generation (Eleven Labs + Gemini fallback)
- [x] Report history with search/filter
- [x] Bookmarking system
- [x] Report comparison
- [x] Advanced charts and visualizations
- [x] Bulk export/import
- [x] Watchlist management with categories
- [x] Report settings and customization
- [x] Desktop notifications
- [x] Keyboard shortcuts

## Deployment Steps

### 1. Environment Setup
```bash
# Set required environment variables
export GCP_PROJECT_ID="mikebrooks"
export GEMINI_API_KEY="your-key"  # Or use Secret Manager
export ELEVEN_LABS_API_KEY="your-key"  # Or use Secret Manager
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

### 2. Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt
```

### 3. GCP Configuration
- [ ] Service account created with required permissions:
  - `roles/datastore.user` (Firestore)
  - `roles/storage.objectAdmin` (Cloud Storage)
  - `roles/secretmanager.secretAccessor` (Secret Manager)
- [ ] Firestore database created
- [ ] Cloud Storage bucket created (`mikebrooks-reports`)
- [ ] Secrets stored in Secret Manager:
  - `GEMINI_API_KEY`
  - `ELEVEN_LABS_API_KEY`

### 4. Testing
```bash
# Run test suite
pytest tests/ -v

# Run deployment agent tests
pytest tests/test_deployment_agent.py -v

# Check health endpoint
curl http://localhost:8000/health
```

### 5. Deployment Options

#### Option A: Streamlit Cloud
- [ ] Push code to GitHub
- [ ] Connect repository to Streamlit Cloud
- [ ] Configure secrets in Streamlit Cloud dashboard
- [ ] Deploy

#### Option B: Google Cloud Run
```bash
# Build and deploy
./scripts/deploy.ps1  # Windows
./scripts/deploy.sh   # Linux/Mac
```

#### Option C: Local Desktop
```bash
# Run Streamlit app
streamlit run app.py

# Or run FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Post-Deployment Verification

### Health Checks
- [ ] `/health` endpoint returns healthy status
- [ ] All service components show as healthy
- [ ] Metrics collection working

### Functional Tests
- [ ] Generate a test report
- [ ] Verify report stored in Firestore
- [ ] Verify audio generated and stored in GCS
- [ ] Test report history viewing
- [ ] Test search and filtering
- [ ] Test bookmarking
- [ ] Test export functionality

### Performance Tests
- [ ] Report generation completes within acceptable time
- [ ] UI is responsive
- [ ] Charts render correctly
- [ ] No memory leaks during extended use

### Security Tests
- [ ] Input validation working (try invalid tickers)
- [ ] Rate limiting enforced
- [ ] API keys not exposed in logs
- [ ] Error messages don't leak sensitive info

## Monitoring Setup

### Logging
- [ ] Structured logging configured
- [ ] Log levels appropriate for production
- [ ] Log rotation configured (if file logging)

### Error Tracking
- [ ] Sentry DSN configured
- [ ] Error tracking initialized
- [ ] Test error capture working

### Metrics
- [ ] Performance metrics being collected
- [ ] Metrics export configured (if needed)
- [ ] Health check endpoint accessible

## Rollback Plan

If issues occur after deployment:

1. **Immediate Rollback**
   - Revert to previous deployment version
   - Check logs for errors
   - Verify service account permissions

2. **Investigation**
   - Review error logs
   - Check Sentry for error reports
   - Verify GCP service status

3. **Fix and Redeploy**
   - Fix identified issues
   - Test locally
   - Redeploy with fixes

## Maintenance

### Regular Tasks
- [ ] Monitor error rates in Sentry
- [ ] Review performance metrics
- [ ] Check Firestore usage and costs
- [ ] Verify Cloud Storage bucket size
- [ ] Review API usage (Gemini, Eleven Labs)

### Updates
- [ ] Keep dependencies updated
- [ ] Monitor for security vulnerabilities
- [ ] Update API keys if needed
- [ ] Review and update documentation

## Support

### Troubleshooting
- Check `APP_STATUS.md` for architecture details
- Review logs for specific errors
- Use health check endpoint for service status
- Check GCP console for service issues

### Common Issues
- **TTS failures**: Check API keys and provider status
- **Firestore errors**: Verify service account permissions
- **Import errors**: Ensure all dependencies installed
- **Rate limiting**: Wait for rate limit window to reset


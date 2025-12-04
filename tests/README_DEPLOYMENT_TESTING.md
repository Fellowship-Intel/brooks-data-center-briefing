# Deployment Testing Agent

Comprehensive testing suite to verify deployment works from the outside and that all dependencies resolve correctly.

## Quick Start

### Run All Tests

```bash
# Test local deployment
python -m pytest tests/test_deployment_agent.py -v

# Test deployed service
BASE_URL=https://your-service.run.app python -m pytest tests/test_deployment_agent.py -v
```

### Quick Health Check

```bash
# Python script (recommended)
python scripts/check_deployment.py

# With log checking
python scripts/check_deployment.py --logs
```

### Check Logs Only

```bash
# Bash
./scripts/check_logs.sh [api|ui|both]

# PowerShell
.\scripts\check_logs.ps1 [api|ui|both]
```

## Test Categories

### 1. Dependency Resolution Tests

Verifies that all required Python packages can be imported:

- Core dependencies (FastAPI, Streamlit, Google Cloud libraries)
- Application modules (app.main, report_service, etc.)

**Run:**
```bash
pytest tests/test_deployment_agent.py::test_import_core_modules -v
pytest tests/test_deployment_agent.py::test_import_app_modules -v
```

### 2. API Health Checks

Tests that the API is accessible and responding:

- Health check endpoint
- Root endpoint
- Report generation endpoints
- Watchlist endpoint
- Get report endpoint

**Run:**
```bash
# Test local API
BASE_URL=http://localhost:8000 pytest tests/test_deployment_agent.py::test_api_health_check -v

# Test deployed API
BASE_URL=https://your-api.run.app pytest tests/test_deployment_agent.py::test_api_health_check -v
```

### 3. GCP Service Checks

Verifies GCP configuration:

- Project ID configuration
- Credentials availability
- Service account permissions

**Run:**
```bash
pytest tests/test_deployment_agent.py::test_gcp_project_configured -v
pytest tests/test_deployment_agent.py::test_gcp_credentials_available -v
```

### 4. Log Reading Tests

Reads recent logs from Cloud Run services (requires gcloud CLI):

- API service logs
- UI service logs

**Run:**
```bash
# Requires gcloud CLI and authentication
pytest tests/test_deployment_agent.py::test_read_api_logs -v
pytest tests/test_deployment_agent.py::test_read_ui_logs -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:8000` | API base URL to test |
| `GCP_PROJECT_ID` | `mikebrooks` | GCP project ID |
| `GCP_REGION` | `us-central1` | GCP region |
| `API_SERVICE_NAME` | `brooks-briefing-api` | Cloud Run API service name |
| `UI_SERVICE_NAME` | `brooks-briefing-ui` | Cloud Run UI service name |

## Usage Examples

### Local Development Testing

```bash
# Start your local API server first
uvicorn app.main:app --reload

# In another terminal, run tests
python -m pytest tests/test_deployment_agent.py -v
```

### CI/CD Integration

```bash
# In your CI/CD pipeline
export BASE_URL=https://${SERVICE_URL}
python -m pytest tests/test_deployment_agent.py -v --tb=short
```

### Post-Deployment Verification

```bash
# After deploying to Cloud Run
export BASE_URL=$(gcloud run services describe brooks-briefing-api \
  --region us-central1 --format 'value(status.url)')

python scripts/check_deployment.py --logs
```

### Manual Log Inspection

```bash
# Read API logs
gcloud logs read \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --service=brooks-briefing-api \
  --limit=50

# Read UI logs
gcloud logs read \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --service=brooks-briefing-ui \
  --limit=50
```

## Expected Results

### ✅ Success Indicators

- All dependency imports succeed
- API responds with 200 status codes
- Endpoints return expected data structures
- GCP credentials are available
- Logs can be read (if gcloud CLI available)

### ❌ Failure Indicators

- Import errors for required modules
- API connection timeouts or errors
- Endpoints returning 4xx/5xx status codes
- Missing GCP credentials
- Log read failures

## Troubleshooting

### Import Errors

If you see import errors:
1. Check that all packages in `requirements.txt` are installed
2. Verify virtual environment is activated
3. Check Python version compatibility

### API Connection Errors

If API tests fail:
1. Verify the server is running
2. Check `BASE_URL` is correct
3. Verify firewall/network settings
4. Check service health in Cloud Run console

### GCP Credential Errors

If credential checks fail:
1. Verify `GOOGLE_APPLICATION_CREDENTIALS` is set (local)
2. Check service account permissions (Cloud Run)
3. Verify project ID is correct

### Log Read Failures

If log reading fails:
1. Ensure gcloud CLI is installed and authenticated
2. Verify you have `logging.logEntries.list` permission
3. Check project ID and region are correct
4. Verify service names match deployed services

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Test Deployment
  env:
    BASE_URL: ${{ secrets.API_URL }}
    GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  run: |
    python -m pytest tests/test_deployment_agent.py -v
```

### GitLab CI Example

```yaml
test_deployment:
  script:
    - export BASE_URL=$API_URL
    - python -m pytest tests/test_deployment_agent.py -v
```

## Related Scripts

- `scripts/check_deployment.py` - Standalone health check script
- `scripts/check_logs.sh` - Log reading script (Bash)
- `scripts/check_logs.ps1` - Log reading script (PowerShell)
- `scripts/smoke_test_cloud_run.sh` - Basic smoke tests
- `scripts/smoke_test_local_api.sh` - Local API smoke tests


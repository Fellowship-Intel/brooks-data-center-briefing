# App Status

**Last Updated:** 2025-01-27  
**Application:** Brooks Data Center Daily Briefing  
**Primary Client:** Michael Brooks

---

## Executive Summary

This is a Python-based daily trading report generation system for Michael Brooks, an active day trader specializing in data center and AI infrastructure equities. The application generates AI-powered daily briefings, stores them in Google Cloud Firestore, and creates audio reports using multiple TTS providers (Eleven Labs primary, Gemini fallback).

**Current Status:** ✅ **PRODUCTION-READY** - Core pipeline working, multiple deployment options available, enhanced UI with custom theming, performance optimizations, comprehensive error handling, retry mechanisms, performance monitoring, and multi-provider TTS support

---

## Architecture Overview

### Technology Stack
- **Backend:** Python 3.8+
- **AI Engine:** Google Gemini (gemini-2.0-flash, gemini-1.5-pro) - **Updated to stable versions**
- **Database:** Google Cloud Firestore
- **Storage:** Google Cloud Storage
- **Text-to-Speech:** 
  - Primary: Eleven Labs (female, professional, natural-sounding voice)
  - Fallback: Google Gemini TTS (gemini-1.5-flash)
  - Automatic fallback on provider failure
- **Web Framework Options:**
  - Streamlit (primary UI - `app.py`)
  - FastAPI (REST API - `app/main.py`)
  - Flask (alternative - `app_flask.py`)

### Key Components

1. **Report Service** (`report_service.py`)
   - Main orchestration for report generation
   - Handles Gemini text generation, Firestore storage, TTS audio generation
   - Graceful TTS failure handling (doesn't break pipeline)
   - Watchlist caching with LRU cache

2. **Gemini Service** (`python_app/services/gemini_service.py`)
   - Streamlit-specific AI integration
   - Handles market data fetching via Google Search
   - Chat session management

3. **TTS Module** 
   - `tts/tts_service.py` - Unified TTS service abstraction with automatic fallback
   - `tts/eleven_labs_tts.py` - Eleven Labs TTS integration (primary provider)
   - `tts/gemini_tts.py` - Google Gemini TTS integration (fallback provider)
   - Automatic provider selection and fallback
   - WAV file generation
   - PCM audio byte handling

4. **GCP Clients** (`gcp_clients.py`)
   - Centralized GCP service client creation
   - Firestore, Cloud Storage, Secret Manager access
   - Application Default Credentials (ADC) support
   - Eleven Labs API key retrieval

5. **Repository Layer** (`report_repository.py`)
   - Firestore data access abstraction
   - Client, Daily Report, Ticker Summary management
   - Optimized queries with pagination

6. **Streamlit UI** (`app.py`)
   - Custom theming system with dark mode
   - Logo integration (Fellowship Intelligence)
   - Enhanced component styling
   - Session state management
   - Watchlist management with Firestore persistence
   - Report history viewer
   - Audio player with GCS signed URLs
   - Export functionality (PDF, CSV)

---

## Current Deployment Status

### ✅ Working Components

1. **Streamlit UI** (`app.py`)
   - Full-featured web interface with custom dark theme
   - Fellowship Intelligence logo integration
   - Auto-initialization with sample data
   - Report generation with AI
   - Interactive Q&A chat
   - Three report views (Top Movers, Deep Dive, Full Narrative)
   - Enhanced styling with green accent colors (#10b981)
   - Responsive design with custom CSS
   - ✅ **Watchlist feature with Firestore persistence** (NEW)
   - ✅ **Performance optimizations** (file watching disabled, fast reruns)
   - ✅ **Report History Viewer** with pagination (NEW)
   - ✅ **Enhanced Audio Player** with GCS signed URLs (NEW)
   - ✅ **Export Functionality** - PDF and CSV export (NEW)

2. **FastAPI REST API** (`app/main.py`)
   - `POST /reports/generate` - Generate new report
   - `GET /reports/{trading_date}` - Fetch existing report
   - `GET /reports/{trading_date}/audio` - Get audio metadata
   - `POST /reports/generate/watchlist` - Generate watchlist report
   - ✅ `GET /health` - Comprehensive health check endpoint (NEW)
     - Checks Firestore, Storage, Secret Manager, TTS providers, Cache
     - Returns detailed component status and metrics

3. **Report Generation Pipeline** (`report_service.py`)
   - ✅ Gemini text generation (with retry logic and caching)
   - ✅ Firestore storage (with retry logic)
   - ✅ TTS audio generation (Eleven Labs primary, Gemini fallback)
   - ✅ Cloud Storage upload (with retry logic)
   - ✅ Email delivery (optional, with error tracking)
   - ✅ **Enhanced JSON parsing with robust error handling** (NEW)
   - ✅ **Structured logging with line numbers** (NEW)
   - ✅ **Performance metrics tracking** (NEW)
   - ✅ **Retry mechanisms on all critical operations** (NEW)
   - ✅ **Error tracking with Sentry integration** (NEW)

4. **Testing Infrastructure**
   - Pytest test suite (`tests/`) - Expanded test coverage
   - Mock fixtures for GCP services (`tests/conftest.py`)
   - API endpoint tests with TestClient (no server required)
   - TTS validation scripts
   - Coverage reporting with pytest-cov
   - ✅ **New test files:**
     - `tests/test_eleven_labs_tts.py` - Eleven Labs TTS tests
     - `tests/test_retry_utils.py` - Retry mechanism tests
     - `tests/test_metrics.py` - Metrics collection tests
     - `tests/test_cache_utils.py` - Cache utility tests
     - `tests/test_config_validator.py` - Config validation tests
     - `tests/test_export_utils.py` - Export utility tests
   - All tests properly mocked (no external dependencies required)

5. **Quality & Reliability Utilities** (NEW)
   - `utils/retry_utils.py` - Retry mechanisms with exponential backoff
   - `utils/circuit_breaker.py` - Circuit breaker pattern for external APIs
   - `utils/exceptions.py` - Custom exception classes with context
   - `utils/metrics.py` - Performance metrics collection and tracking
   - `utils/health_check.py` - Comprehensive health check utilities
   - `utils/cache_utils.py` - File-based caching for Gemini responses
   - `utils/config_validator.py` - Environment configuration validation
   - `utils/error_tracking.py` - Sentry integration for error monitoring
   - `utils/email_service.py` - SMTP email delivery service
   - `utils/auth.py` - Authentication framework for multi-client support
   - `utils/audio_utils.py` - Audio utilities with GCS signed URLs
   - `utils/export_utils.py` - PDF and CSV export functionality
   - `python_app/utils/json_parser.py` - Enhanced JSON parsing with error recovery
   - `utils/logging_config.py` - Structured logging configuration

### ⚠️ Known Limitations

1. **TTS Fallback Behavior**
   - ✅ **ENHANCED** - Automatic fallback: Eleven Labs → Gemini TTS
   - TTS failures are logged but don't break the pipeline
   - Provider used is tracked and logged for each report
   - Check logs for TTS errors and provider selection

2. **Model Configuration**
   - ✅ Updated to stable `gemini-2.0-flash` (was experimental)
   - ✅ Using stable `gemini-1.5-pro` for report generation
   - Google Search tool availability varies by API access level

3. **Streamlit vs FastAPI**
   - Two separate implementations exist
   - Streamlit: Full UI with chat
   - FastAPI: REST API only
   - Consider consolidating if needed

---

## Critical Code Components

### 1. Main Report Generation Function

**File:** `report_service.py`  
**Function:** `generate_and_store_daily_report()`

```python
def generate_and_store_daily_report(
    trading_date: date,
    client_id: str,
    market_data: Dict[str, Any],
    news_items: Dict[str, Any],
    macro_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Orchestrates a full daily report for a given client and trading date.
    - Uses Gemini for text
    - Stores report in Firestore
    - Attempts audio via TTS service (Eleven Labs primary, Gemini fallback)
    - Stores audio file in Cloud Storage and updates Firestore with the GCS path if successful
    """
```

**Key Points:**
- Graceful TTS error handling (logs error, continues)
- Extracts tickers from market_data automatically
- Stores raw payload for audit trail
- Returns consolidated view with audio path and TTS provider used
- Retry logic on all critical operations
- Performance metrics tracking

### 2. TTS Service Abstraction

**File:** `tts/tts_service.py`  
**Function:** `synthesize()`

```python
def synthesize(
    text: str,
    output_path: Optional[str] = None,
    provider: Optional[str] = None,
) -> tuple[bytes, str]:
    """
    Synthesize speech from text with automatic fallback.
    - Primary: Eleven Labs
    - Fallback: Gemini TTS
    - Returns: (audio_bytes, provider_used)
    """
```

**Key Points:**
- Automatic fallback chain
- Provider selection logic
- Consistent audio format output
- Error handling for both providers

### 3. Gemini Configuration

**File:** `report_service.py`  
**Function:** `_configure_gemini_client()`

```python
def _configure_gemini_client() -> None:
    """
    Configure the google-generativeai client using GEMINI_API_KEY from Secret Manager.
    Safe to call multiple times; configuration is idempotent.
    """
    api_key = access_secret_value("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
```

**Key Points:**
- Uses Secret Manager for API key (production)
- Falls back to environment variables (local dev)
- Idempotent configuration
- Retry logic on Secret Manager access

### 4. TTS Synthesis

**File:** `tts/eleven_labs_tts.py` / `tts/gemini_tts.py`  
**Function:** `synthesize()`

```python
def synthesize(
    text: str,
    output_path: Optional[str] = None,
) -> bytes:
    """
    Synthesize speech from text.
    - text: text to be spoken
    - output_path: optional path to store a WAV file on disk
    """
```

**Key Points:**
- Eleven Labs: Uses official SDK, female professional voice
- Gemini: Uses gemini-1.5-flash model
- Returns PCM bytes, writes WAV if path provided
- Handles API key from Secret Manager or env vars
- Automatic fallback on failure

### 5. Firestore Repository

**File:** `report_repository.py`  
**Function:** `create_or_update_daily_report()`

```python
def create_or_update_daily_report(report: Dict[str, Any]) -> None:
    """
    Create or update a daily report document in Firestore.
    Uses the 'trading_date' field as the document ID in the 'daily_reports' collection.
    Automatically sets 'created_at' timestamp if not provided.
    """
```

**Key Points:**
- Document ID = trading_date (ISO format: YYYY-MM-DD)
- Auto-sets `created_at` timestamp
- Stores full raw_payload for audit
- Optimized queries with pagination support

### 6. GCP Client Factory

**File:** `gcp_clients.py`  
**Function:** `get_firestore_client()`, `get_storage_client()`, `access_secret_value()`

```python
def get_firestore_client() -> firestore.Client:
    """
    Returns an authenticated Firestore client using Application Default Credentials.
    Requirements:
    - GOOGLE_APPLICATION_CREDENTIALS points to a valid service account key (local)
      OR the code is running on GCP (Cloud Run, etc.) with a bound service account.
    """
    project_id = get_project_id()
    return firestore.Client(project=project_id)
```

**Key Points:**
- Uses Application Default Credentials (ADC)
- Works locally (via service account JSON) and on GCP (via bound service account)
- Project ID defaults to "mikebrooks" (configurable via GCP_PROJECT_ID)
- Retry logic on client initialization
- Eleven Labs API key access support

---

## Configuration

### Streamlit Configuration (`.streamlit/config.toml`)
- Custom dark theme with green accent colors (#10b981)
- Background: #0f172a (dark slate)
- Secondary background: #1e293b (lighter slate)
- Server port: 8080 (configurable)
- CORS and XSRF protection enabled
- Logo path: `static/images/logo.png` (Fellowship Intelligence)
- Performance optimizations: file watching disabled, fast reruns enabled

### Environment Variables

**Required:**
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` - Gemini API key

**Optional:**
- `GCP_PROJECT_ID` - GCP project ID (defaults to "mikebrooks")
- `REPORTS_BUCKET_NAME` - Cloud Storage bucket for audio files (defaults to "mikebrooks-reports")
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON (local dev)
- `GEMINI_MODEL_NAME` - Override Gemini model (default: "gemini-1.5-pro")
- `ELEVEN_LABS_API_KEY` - Eleven Labs API key (for TTS)
- `ELEVEN_LABS_VOICE_ID` - Eleven Labs voice ID (default: auto-select)
- `TTS_PROVIDER` - TTS provider preference (eleven_labs, gemini, or auto)
- `ENVIRONMENT` - Environment name (development, staging, production)
- `SENTRY_DSN` - Sentry DSN for error tracking
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM` - Email configuration
- `PORT` - Server port (default: 8080)
- `FLASK_DEBUG` - Flask debug mode (default: False)

### GCP Secret Manager

**Secrets:**
- `GEMINI_API_KEY` - Stored in Secret Manager for production
- `ELEVEN_LABS_API_KEY` - Stored in Secret Manager for production

**Access:**
- Service account needs `roles/secretmanager.secretAccessor`
- Local dev can use env vars instead
- Automatic fallback to environment variables

### Firestore Collections

1. **`clients`** - Client profiles
   - Document ID: client_id (e.g., "michael_brooks")
   - Fields: email, name, timezone, preferences, watchlist

2. **`daily_reports`** - Daily reports
   - Document ID: trading_date (ISO format: "2025-12-03")
   - Fields: client_id, trading_date, tickers, summary_text, key_insights, market_context, audio_gcs_path, tts_provider, email_status, raw_payload, created_at

3. **`ticker_summaries`** - Ticker snapshots
   - Document ID: ticker symbol (e.g., "SMCI")
   - Fields: ticker, latest_snapshot, last_updated, last_report_date, notes

### Cloud Storage Structure

```
gs://{REPORTS_BUCKET_NAME}/
  reports/
    {client_id}/
      {trading_date}/
        report.wav
```

Example: `gs://mikebrooks-reports/reports/michael_brooks/2025-12-03/report.wav`

---

## Dependencies

**Core:**
- `google-generativeai>=0.3.0` - Gemini AI
- `google-genai>=0.2.0` - Gemini TTS
- `google-cloud-firestore>=2.0.0` - Firestore
- `google-cloud-storage>=2.0.0` - Cloud Storage
- `google-cloud-secret-manager>=2.0.0` - Secret Manager
- `google-cloud-texttospeech>=2.0.0` - Cloud TTS (fallback, not currently used)

**Web Frameworks:**
- `streamlit>=1.28.0` - Streamlit UI
- `fastapi` - REST API
- `uvicorn[standard]` - ASGI server

**Utilities:**
- `pandas>=2.0.0` - Data manipulation
- `python-dotenv>=1.0.0` - Environment variable loading
- `pytest>=7.4.0` - Testing
- `yfinance>=0.2.0` - Market data
- `Pillow>=10.0.0` - Image processing
- `reportlab>=4.0.0` - PDF generation
- `sentry-sdk>=2.0.0` - Error tracking
- `elevenlabs>=1.0.0` - Eleven Labs TTS

See `requirements.txt` for full list.

---

## Running the Application

### Streamlit UI

```bash
streamlit run app.py
```

Access at: `http://localhost:8080` (configurable via `.streamlit/config.toml`)

**Features:**
- Custom dark theme with green accent colors
- Fellowship Intelligence logo in sidebar
- Enhanced component styling
- Responsive layout
- Watchlist management
- Report history viewer
- Audio player
- Export functionality

### FastAPI REST API

```bash
# PowerShell
.\scripts\run_api_locally.ps1

# Bash
./scripts/run_api_locally.sh

# Or manually
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Access at: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

### Testing

```bash
# Run pytest suite
pytest tests/

# Test API endpoints
.\scripts\test_api.ps1  # PowerShell
./scripts/test_api.sh  # Bash

# Validate TTS
.\scripts\validate_tts.ps1  # PowerShell
./scripts/validate_tts.sh  # Bash
```

---

## Important Code Patterns

### 1. Error Handling in TTS Pipeline

**Location:** `report_service.py:576-632`

```python
try:
    logger.info("Attempting TTS generation for client=%s date=%s", client_id, trading_date.isoformat())
    reports_bucket_name = get_reports_bucket_name()
    audio_bytes, tts_provider_used = _generate_and_store_audio_for_report(
        trading_date=trading_date,
        client_id=client_id,
        summary_text=summary_text,
        reports_bucket_name=reports_bucket_name,
    )
    # ... success handling ...
except Exception as exc:
    # Log the error but keep the text report
    logger.error(
        "TTS generation failed for client=%s date=%s: %s",
        client_id,
        trading_date.isoformat(),
        exc,
        exc_info=True,
    )
```

**Why:** TTS failures should not break the entire report generation. Text reports are more critical than audio.

### 2. JSON Response Parsing

**Location:** `python_app/utils/json_parser.py`

```python
def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text that may contain markdown or extra text.
    Handles common edge cases.
    """
    # Remove markdown code fences
    text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```\s*', '', text)
    
    # Find JSON object boundaries
    start = text.find('{')
    end = text.rfind('}')
    
    if start == -1 or end == -1 or end <= start:
        return None
    
    json_str = text[start:end + 1]
    # ... parsing logic ...
```

**Why:** Gemini sometimes wraps JSON in markdown code blocks or adds conversational text. This extracts the JSON robustly.

### 3. Retry Mechanisms

**Location:** `utils/retry_utils.py`, applied throughout `report_service.py`

```python
@retry_on_api_error(max_retries=3)
def _generate_report_text(...):
    # Gemini API call with automatic retry
    pass

@retry_with_backoff(max_retries=3, initial_delay=1.0)
def _store_report():
    # Firestore write with retry
    pass
```

**Why:** External API calls and database operations can fail transiently. Retry logic improves reliability.

### 4. TTS Service Abstraction

**Location:** `tts/tts_service.py`

```python
def synthesize(text: str, ...) -> tuple[bytes, str]:
    """
    Synthesize speech with automatic fallback.
    Tries Eleven Labs first, falls back to Gemini on failure.
    """
    for provider_name in [primary_provider, fallback_provider]:
        try:
            # Try provider
            return audio_bytes, provider_name
        except Exception:
            # Try next provider
            continue
    raise TTSGenerationError("All providers failed")
```

**Why:** Provides resilience through automatic fallback between TTS providers.

### 5. System Instruction for Gemini

**Location:** `python_app/constants.py:7-126`

The `SYSTEM_INSTRUCTION` constant contains detailed instructions for Gemini on:
- Report structure (mini-reports, deep dive, audio)
- Client profile (Michael Brooks' trading style)
- Audio report requirements (natural phrasing, no lists, proper pacing)
- JSON output constraints (no unescaped quotes)

**Critical:** The system instruction emphasizes avoiding double quotes in JSON strings to prevent parsing errors.

---

## Testing Strategy

### Unit Tests

**File:** `tests/conftest.py`  
**Fixtures:**
- `mock_gemini` - Mocks Gemini API calls
- `mock_firestore` - Mocks Firestore operations
- `mock_storage` - Mocks Cloud Storage operations
- `mock_tts` - Mocks TTS synthesis
- `mock_eleven_labs` - Mocks Eleven Labs TTS

**Usage:**
```python
def test_report_generation(mock_gemini, mock_firestore, mock_storage, mock_tts):
    # Test code here
```

### Integration Tests

**Files:**
- `tests/test_pipeline_small.py` - Small pipeline test
- `tests/test_pipeline_tts_fallback.py` - TTS fallback behavior
- `tests/test_api_endpoints.py` - API endpoint tests
- `tests/test_eleven_labs_tts.py` - Eleven Labs TTS integration tests
- `tests/test_retry_utils.py` - Retry mechanism tests
- `tests/test_metrics.py` - Metrics collection tests

### Manual Testing

**Scripts:**
- `tests/manual_run_michael_report.py` - Manual report generation
- `tests/validate_gemini_tts.py` - TTS validation
- `scripts/validate_tts.ps1` / `scripts/validate_tts.sh` - TTS validation scripts

---

## Deployment Options

### 1. Local Development

**Requirements:**
- Python 3.8+
- Service account JSON file
- Environment variables set

**Run:**
```bash
streamlit run app.py  # UI
# OR
uvicorn app.main:app --reload  # API
```

### 2. Google Cloud Run

**Files:**
- `Dockerfile` - Container definition
- `scripts/deploy_cloud_run.ps1` / `scripts/deploy_cloud_run.sh` - Deployment scripts
- `scripts/deploy.ps1` / `scripts/deploy.sh` - Enhanced deployment scripts
- `.github/workflows/deploy.yml` - CI/CD deployment workflow

**Requirements:**
- GCP project with Cloud Run API enabled
- Service account with required permissions
- Container registry access

### 3. Streamlit Cloud

**Requirements:**
- Streamlit Cloud account
- `requirements.txt` in root
- Secrets configured in Streamlit Cloud dashboard

---

## Critical Environment Setup

### Local Development

1. **Service Account Setup:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
   ```

2. **API Keys:**
   ```bash
   export GEMINI_API_KEY="your-api-key"
   export ELEVEN_LABS_API_KEY="your-eleven-labs-key"
   # OR use Secret Manager (production)
   ```

3. **Project Configuration:**
   ```bash
   export GCP_PROJECT_ID="mikebrooks"
   export REPORTS_BUCKET_NAME="mikebrooks-reports"
   ```

### Production (GCP)

1. **Service Account Permissions:**
   - `roles/datastore.user` - Firestore
   - `roles/storage.objectAdmin` - Cloud Storage
   - `roles/secretmanager.secretAccessor` - Secret Manager

2. **Secrets:**
   - Store `GEMINI_API_KEY` in Secret Manager
   - Store `ELEVEN_LABS_API_KEY` in Secret Manager
   - Code automatically retrieves from Secret Manager

3. **Cloud Storage:**
   - Create bucket: `mikebrooks-reports` (or configure via env var)
   - Service account needs write access

---

## ✅ Completed Features

1. **Email Integration**
   - ✅ **COMPLETED** - Full SMTP email delivery service
   - Email status tracking and delivery
   - HTML and plain text email support
   - Automatic email sending on report generation

2. **Watchlist Feature**
   - ✅ **COMPLETED** - Full implementation with Firestore persistence
   - Watchlist saves automatically on changes
   - Loads from Firestore on app startup

3. **Audio Player**
   - ✅ **COMPLETED** - Enhanced audio player with GCS signed URLs
   - Audio playback in Streamlit UI
   - Fallback to direct download if signed URL fails
   - Support for both Eleven Labs and Gemini TTS audio

4. **Error Monitoring**
   - ✅ **COMPLETED** - Structured logging implemented
   - ✅ **COMPLETED** - Sentry integration for error tracking
   - Logging utility created (`utils/logging_config.py`)
   - Enhanced error messages with context
   - Custom exception classes with rich context

5. **Performance Optimization**
   - ✅ **COMPLETED** - Streamlit config optimized (file watching disabled)
   - ✅ **COMPLETED** - Fast reruns enabled
   - ✅ **COMPLETED** - Response caching for Gemini (24-hour TTL)
   - ✅ **COMPLETED** - Firestore query optimization with pagination
   - ✅ **COMPLETED** - Performance metrics collection
   - ✅ **COMPLETED** - Retry mechanisms on all critical operations

6. **Quality Improvements**
   - ✅ **COMPLETED** - Retry utilities with exponential backoff
   - ✅ **COMPLETED** - Circuit breaker pattern for external APIs
   - ✅ **COMPLETED** - Comprehensive health check endpoint
   - ✅ **COMPLETED** - Performance metrics tracking
   - ✅ **COMPLETED** - Enhanced test coverage
   - ✅ **COMPLETED** - Configuration validation

7. **TTS Integration**
   - ✅ **COMPLETED** - Eleven Labs TTS integration (primary)
   - ✅ **COMPLETED** - Automatic fallback to Gemini TTS
   - ✅ **COMPLETED** - TTS service abstraction layer
   - ✅ **COMPLETED** - Voice selection (female, professional, natural)

8. **Export & History**
   - ✅ **COMPLETED** - PDF export functionality
   - ✅ **COMPLETED** - CSV export functionality
   - ✅ **COMPLETED** - Report history viewer with pagination

---

## Key Files Reference

### Core Application
- `app.py` - Streamlit main application
- `app/main.py` - FastAPI REST API
- `report_service.py` - Main report generation orchestration
- `python_app/services/gemini_service.py` - Streamlit AI service
- `tts/tts_service.py` - TTS service abstraction (primary interface)
- `tts/eleven_labs_tts.py` - Eleven Labs TTS integration
- `tts/gemini_tts.py` - Google Gemini TTS integration (fallback)

### Infrastructure
- `gcp_clients.py` - GCP service clients (Firestore, Storage, Secret Manager)
- `report_repository.py` - Firestore data access with optimized queries
- `settings.py` - Configuration helpers
- `utils/retry_utils.py` - Retry mechanisms
- `utils/circuit_breaker.py` - Circuit breaker pattern
- `utils/metrics.py` - Performance metrics
- `utils/health_check.py` - Health check utilities
- `utils/cache_utils.py` - Response caching
- `utils/config_validator.py` - Configuration validation
- `utils/error_tracking.py` - Sentry integration
- `utils/email_service.py` - Email delivery
- `utils/auth.py` - Authentication framework
- `utils/audio_utils.py` - Audio utilities
- `utils/export_utils.py` - Export functionality

### Data Models
- `python_app/types.py` - Python dataclasses
- `python_app/constants.py` - System instructions and defaults

### Testing
- `tests/conftest.py` - Pytest fixtures
- `tests/test_pipeline_*.py` - Pipeline tests
- `tests/test_api_endpoints.py` - API tests
- `tests/test_eleven_labs_tts.py` - Eleven Labs TTS tests
- `tests/test_retry_utils.py` - Retry mechanism tests
- `tests/test_metrics.py` - Metrics tests
- `tests/test_cache_utils.py` - Cache tests
- `tests/test_config_validator.py` - Config validation tests
- `tests/test_export_utils.py` - Export tests

### Scripts
- `scripts/run_api_locally.ps1` / `.sh` - Run API locally
- `scripts/test_api.ps1` / `.sh` - Test API endpoints
- `scripts/validate_tts.ps1` / `.sh` - Validate TTS
- `scripts/deploy_cloud_run.ps1` / `.sh` - Deploy to Cloud Run
- `scripts/deploy.ps1` / `.sh` - Enhanced deployment scripts
- `scripts/scheduled_report.py` - Scheduled report generation

---

## Support & Maintenance

### Logging

The application uses Python's `logging` module. Configure log level via:
```python
logging.basicConfig(level=logging.INFO)
```

### Debugging

1. **Check TTS:**
   ```bash
   python -m tts.gemini_tts
   python -m tts.eleven_labs_tts
   ```

2. **Test Firestore:**
   ```bash
   python report_repository.py
   ```

3. **Test GCP Clients:**
   ```bash
   python gcp_clients.py
   ```

4. **Check Health:**
   ```bash
   curl http://localhost:8000/health
   ```

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Check Secret Manager or environment variable
   - Verify service account has secret accessor role

2. **"ELEVEN_LABS_API_KEY not found"**
   - Check Secret Manager or environment variable
   - Verify service account has secret accessor role
   - Store key: `gcloud secrets create ELEVEN_LABS_API_KEY --data-file=-`

3. **"Firestore permission denied"**
   - Check service account has `roles/datastore.user`
   - Verify `GCP_PROJECT_ID` is correct

4. **"TTS generation failed"**
   - Check TTS provider API status
   - Verify API keys are valid
   - Check logs for detailed error (fallback should occur automatically)

5. **"Circuit breaker open"**
   - Too many failures to external API
   - Wait for timeout period or manually reset
   - Check underlying service health

---

## Handoff Notes

### For New Developers

1. **Start Here:**
   - Read `README.md` for overview
   - Review `CONVERSION_SUMMARY.md` for architecture history
   - Check `requirements.txt` for dependencies
   - Review `APP_STATUS.md` (this file) for current status

2. **Key Entry Points:**
   - Streamlit: `app.py`
   - FastAPI: `app/main.py`
   - Report generation: `report_service.py`
   - TTS: `tts/tts_service.py` (use this, not direct providers)

3. **Testing:**
   - Run `pytest tests/` to verify setup
   - Use `tests/manual_run_michael_report.py` for manual testing

4. **Configuration:**
   - Set up GCP service account
   - Configure environment variables
   - Store `GEMINI_API_KEY` and `ELEVEN_LABS_API_KEY` in Secret Manager

### For Operations

1. **Monitoring:**
   - Check Firestore for daily reports
   - Monitor Cloud Storage for audio files
   - Review logs for TTS failures
   - Check `/health` endpoint for system status
   - Monitor Sentry for error tracking

2. **Deployment:**
   - Use `scripts/deploy.ps1` or `scripts/deploy.sh` for Cloud Run
   - Or deploy Streamlit app to Streamlit Cloud
   - CI/CD via GitHub Actions (`.github/workflows/deploy.yml`)

3. **Backup:**
   - Firestore data is automatically replicated
   - Cloud Storage files should be backed up if needed

---

## Version History

- **2025-01-27:** Quality Improvements Phase & Eleven Labs Integration
  - ✅ Added Eleven Labs TTS integration (primary provider)
  - ✅ Implemented TTS service abstraction with automatic fallback
  - ✅ Added retry mechanisms with exponential backoff to all critical operations
  - ✅ Implemented circuit breaker pattern for external APIs
  - ✅ Created comprehensive performance metrics collection
  - ✅ Enhanced health check endpoint with component-level status
  - ✅ Added custom exception classes with rich context
  - ✅ Implemented file-based caching for Gemini responses (24-hour TTL)
  - ✅ Added configuration validation system
  - ✅ Integrated Sentry for error tracking
  - ✅ Enhanced audio player with GCS signed URLs
  - ✅ Added PDF and CSV export functionality
  - ✅ Implemented report history viewer with pagination
  - ✅ Added email delivery service
  - ✅ Expanded test coverage with new test suites
  - ✅ Updated documentation with all new features

- **2025-12-04:** 
  - Enhanced Streamlit UI with custom dark theme
  - Added Fellowship Intelligence logo integration
  - Fixed Streamlit configuration issues (CORS/XSRF, invalid options)
  - Improved test suite (13 tests passing, 100% test file coverage)
  - Added pytest-cov for coverage reporting
  - Updated port configuration (default: 8080)
  - Enhanced CSS styling for all components
  
- **2025-01-27 (Initial):** Initial App Status document created
- Application converted from TypeScript/React to Python/Streamlit
- FastAPI REST API added for programmatic access
- TTS integration with Gemini TTS
- Full GCP integration (Firestore, Storage, Secret Manager)

---

**End of App Status Document**

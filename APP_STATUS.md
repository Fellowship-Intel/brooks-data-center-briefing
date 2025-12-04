# App Status

**Last Updated:** 2025-12-04  
**Application:** Brooks Data Center Daily Briefing  
**Primary Client:** Michael Brooks

---

## Executive Summary

This is a Python-based daily trading report generation system for Michael Brooks, an active day trader specializing in data center and AI infrastructure equities. The application generates AI-powered daily briefings, stores them in Google Cloud Firestore, and creates audio reports using Google Gemini TTS.

**Current Status:** ✅ **FUNCTIONAL** - Core pipeline working, multiple deployment options available, enhanced UI with custom theming

---

## Architecture Overview

### Technology Stack
- **Backend:** Python 3.8+
- **AI Engine:** Google Gemini (gemini-2.0-flash-exp, gemini-1.5-pro)
- **Database:** Google Cloud Firestore
- **Storage:** Google Cloud Storage
- **Text-to-Speech:** Google Gemini TTS (gemini-2.5-flash-preview-tts)
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

3. **TTS Module** (`tts/gemini_tts.py`)
   - Google Gemini TTS integration
   - WAV file generation
   - PCM audio byte handling

4. **GCP Clients** (`gcp_clients.py`)
   - Centralized GCP service client creation
   - Firestore, Cloud Storage, Secret Manager access
   - Application Default Credentials (ADC) support

5. **Repository Layer** (`report_repository.py`)
   - Firestore data access abstraction
   - Client, Daily Report, Ticker Summary management

6. **Streamlit UI** (`app.py`)
   - Custom theming system with dark mode
   - Logo integration (Fellowship Intelligence)
   - Enhanced component styling
   - Session state management

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

2. **FastAPI REST API** (`app/main.py`)
   - `POST /reports/generate` - Generate new report
   - `GET /reports/{trading_date}` - Fetch existing report
   - `GET /reports/{trading_date}/audio` - Get audio metadata

3. **Report Generation Pipeline** (`report_service.py`)
   - ✅ Gemini text generation
   - ✅ Firestore storage
   - ✅ TTS audio generation (with fallback)
   - ✅ Cloud Storage upload

4. **Testing Infrastructure**
   - Pytest test suite (`tests/`) - 13 tests passing
   - Mock fixtures for GCP services (`tests/conftest.py`)
   - API endpoint tests with TestClient (no server required)
   - TTS validation scripts
   - Coverage reporting with pytest-cov
   - All tests properly mocked (no external dependencies required)

### ⚠️ Known Limitations

1. **TTS Fallback Behavior**
   - TTS failures are logged but don't break the pipeline
   - Audio generation may fail silently if Gemini TTS API issues occur
   - Check logs for TTS errors

2. **Model Configuration**
   - Currently using `gemini-2.0-flash-exp` (experimental)
   - May need updates as Google deprecates models
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
    - Attempts audio via Gemini TTS (but does NOT fail the whole pipeline if TTS fails)
    - Stores audio file in Cloud Storage and updates Firestore with the GCS path if successful
    """
```

**Key Points:**
- Graceful TTS error handling (logs error, continues)
- Extracts tickers from market_data automatically
- Stores raw payload for audit trail
- Returns consolidated view with audio path

### 2. Gemini Configuration

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

### 3. TTS Synthesis

**File:** `tts/gemini_tts.py`  
**Function:** `synthesize_speech()`

```python
def synthesize_speech(
    text: str,
    *,
    output_path: Optional[str] = None,
) -> bytes:
    """
    Simple convenience wrapper used by the rest of the app.
    - text: text to be spoken
    - output_path: optional path to store a WAV file on disk
    """
    path = Path(output_path) if output_path else None
    return get_tts().synthesize(text, output_path=path)
```

**Key Points:**
- Uses Gemini TTS model: `gemini-2.5-flash-preview-tts`
- Voice: "Kore" (configurable)
- Returns PCM bytes, writes WAV if path provided
- Handles API key from Secret Manager or env vars

### 4. Firestore Repository

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

### 5. GCP Client Factory

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

---

## Configuration

### Streamlit Configuration (`.streamlit/config.toml`)
- Custom dark theme with green accent colors (#10b981)
- Background: #0f172a (dark slate)
- Secondary background: #1e293b (lighter slate)
- Server port: 8080 (configurable)
- CORS and XSRF protection enabled
- Logo path: `static/images/logo.png` (Fellowship Intelligence)

### Environment Variables

**Required:**
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` - Gemini API key
- `GCP_PROJECT_ID` - GCP project ID (defaults to "mikebrooks")
- `REPORTS_BUCKET_NAME` - Cloud Storage bucket for audio files (defaults to "mikebrooks-reports")
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON (local dev)

**Optional:**
- `GEMINI_MODEL_NAME` - Override Gemini model (default: "gemini-1.5-pro")
- `GCP_TTS_VOICE_NAME` - TTS voice (default: "en-US-Neural2-D")
- `GCP_TTS_LANGUAGE_CODE` - TTS language (default: "en-US")

### GCP Secret Manager

**Secrets:**
- `GEMINI_API_KEY` - Stored in Secret Manager for production

**Access:**
- Service account needs `roles/secretmanager.secretAccessor`
- Local dev can use env var instead

### Firestore Collections

1. **`clients`** - Client profiles
   - Document ID: client_id (e.g., "michael_brooks")
   - Fields: email, name, timezone, preferences

2. **`daily_reports`** - Daily reports
   - Document ID: trading_date (ISO format: "2025-12-03")
   - Fields: client_id, trading_date, tickers, summary_text, key_insights, market_context, audio_gcs_path, email_status, raw_payload, created_at

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

**Location:** `report_service.py:529-565`

```python
try:
    logger.info("Attempting TTS generation for client=%s date=%s", client_id, trading_date.isoformat())
    reports_bucket_name = get_reports_bucket_name()
    audio_bytes, audio_gcs_path = _generate_and_store_audio_for_report(
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

**Location:** `python_app/services/gemini_service.py:162-174`

```python
# CLEANUP: Remove common markdown fences if present
text = re.sub(r'```json', '', text, flags=re.IGNORECASE)
text = re.sub(r'```', '', text).strip()

# ROBUST JSON EXTRACTION
# Find the first '{' and the last '}' to extract the JSON object
start = text.find('{')
end = text.rfind('}')

if start != -1 and end != -1:
    text = text[start:end + 1]
else:
    raise ValueError(f"Model response did not contain a valid JSON object: {text[:500]}")
```

**Why:** Gemini sometimes wraps JSON in markdown code blocks or adds conversational text. This extracts the JSON robustly.

### 3. Ticker Extraction

**Location:** `report_service.py:499-509`

```python
# Extract tickers from market_data
if isinstance(market_data, dict):
    if "tickers" in market_data and isinstance(market_data["tickers"], list):
        tickers = market_data["tickers"]
    elif "prices" in market_data and isinstance(market_data["prices"], dict):
        tickers = list(market_data["prices"].keys())
    else:
        excluded_keys = {"indices", "tickers", "prices"}
        tickers = [k for k in market_data.keys() if k not in excluded_keys]
else:
    tickers = []
```

**Why:** Market data can come in multiple formats. This handles all common structures.

### 4. System Instruction for Gemini

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

2. **API Key:**
   ```bash
   export GEMINI_API_KEY="your-api-key"
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
   - Code automatically retrieves from Secret Manager

3. **Cloud Storage:**
   - Create bucket: `mikebrooks-reports` (or configure via env var)
   - Service account needs write access

---

## Known Issues & TODOs

### Issues

1. **TTS Model Availability**
   - Using `gemini-2.5-flash-preview-tts` (preview)
   - May need to update if Google deprecates
   - Fallback to Cloud TTS available but not implemented

2. **Gemini Model Versioning**
   - Using `gemini-2.0-flash-exp` (experimental)
   - Should monitor for stable release
   - Google Search tool availability varies

3. **JSON Parsing Edge Cases**
   - Sometimes fails if Gemini includes unexpected formatting
   - Current extraction logic handles most cases
   - May need refinement for edge cases

### TODOs

1. **Email Integration**
   - Email status tracking exists but no sending logic
   - Consider adding email delivery service

2. **Watchlist Feature**
   - Streamlit UI has watchlist state but not fully implemented
   - Can be added using session state

3. **Audio Player**
   - Streamlit version shows audio script only
   - Consider integrating audio playback component

4. **Error Monitoring**
   - Add structured logging
   - Consider error tracking service (Sentry, etc.)

5. **Performance Optimization**
   - Cache Gemini responses where appropriate
   - Optimize Firestore queries
   - Consider CDN for audio files

---

## Key Files Reference

### Core Application
- `app.py` - Streamlit main application
- `app/main.py` - FastAPI REST API
- `report_service.py` - Main report generation orchestration
- `python_app/services/gemini_service.py` - Streamlit AI service
- `tts/gemini_tts.py` - Text-to-speech synthesis

### Infrastructure
- `gcp_clients.py` - GCP service clients
- `report_repository.py` - Firestore data access
- `settings.py` - Configuration helpers

### Data Models
- `python_app/types.py` - Python dataclasses
- `python_app/constants.py` - System instructions and defaults

### Testing
- `tests/conftest.py` - Pytest fixtures
- `tests/test_pipeline_*.py` - Pipeline tests
- `tests/test_api_endpoints.py` - API tests

### Scripts
- `scripts/run_api_locally.ps1` / `.sh` - Run API locally
- `scripts/test_api.ps1` / `.sh` - Test API endpoints
- `scripts/validate_tts.ps1` / `.sh` - Validate TTS
- `scripts/deploy_cloud_run.ps1` / `.sh` - Deploy to Cloud Run

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
   ```

2. **Test Firestore:**
   ```bash
   python report_repository.py
   ```

3. **Test GCP Clients:**
   ```bash
   python gcp_clients.py
   ```

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Check Secret Manager or environment variable
   - Verify service account has secret accessor role

2. **"Firestore permission denied"**
   - Check service account has `roles/datastore.user`
   - Verify `GCP_PROJECT_ID` is correct

3. **"TTS generation failed"**
   - Check Gemini TTS API status
   - Verify model name is still available
   - Check logs for detailed error

---

## Handoff Notes

### For New Developers

1. **Start Here:**
   - Read `README.md` for overview
   - Review `CONVERSION_SUMMARY.md` for architecture history
   - Check `requirements.txt` for dependencies

2. **Key Entry Points:**
   - Streamlit: `app.py`
   - FastAPI: `app/main.py`
   - Report generation: `report_service.py`

3. **Testing:**
   - Run `pytest tests/` to verify setup
   - Use `tests/manual_run_michael_report.py` for manual testing

4. **Configuration:**
   - Set up GCP service account
   - Configure environment variables
   - Store `GEMINI_API_KEY` in Secret Manager

### For Operations

1. **Monitoring:**
   - Check Firestore for daily reports
   - Monitor Cloud Storage for audio files
   - Review logs for TTS failures

2. **Deployment:**
   - Use `scripts/deploy_cloud_run.ps1` for Cloud Run
   - Or deploy Streamlit app to Streamlit Cloud

3. **Backup:**
   - Firestore data is automatically replicated
   - Cloud Storage files should be backed up if needed

---

## Version History

- **2025-12-04:** 
  - Enhanced Streamlit UI with custom dark theme
  - Added Fellowship Intelligence logo integration
  - Fixed Streamlit configuration issues (CORS/XSRF, invalid options)
  - Improved test suite (13 tests passing, 100% test file coverage)
  - Added pytest-cov for coverage reporting
  - Updated port configuration (default: 8080)
  - Enhanced CSS styling for all components
  
- **2025-01-27:** Initial App Status document created
- Application converted from TypeScript/React to Python/Streamlit
- FastAPI REST API added for programmatic access
- TTS integration with Gemini TTS
- Full GCP integration (Firestore, Storage, Secret Manager)

---

**End of App Status Document**


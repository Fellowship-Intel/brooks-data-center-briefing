# API Testing Guide

Quick reference for testing the FastAPI report generation endpoints.

## Starting the Server

Run the FastAPI server locally:

```powershell
# PowerShell (Windows)
.\scripts\run_api_locally.ps1

# Or manually:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
# Bash (Linux/Mac)
./scripts/run_api_locally.sh

# Or manually:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## API Endpoints

### 1. Generate a Report (with dummy data)

Generate a report using dummy data (for Michael, today):

```bash
curl -X POST "http://localhost:8000/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**PowerShell version:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/reports/generate" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{}'
```

### 2. Fetch a Report

Fetch a previously generated report (replace `2025-12-04` with the trading date):

```bash
curl "http://localhost:8000/reports/2025-12-04"
```

**PowerShell version:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/reports/2025-12-04" -Method GET
```

### 3. Fetch Audio Metadata

Get audio information for a report:

```bash
curl "http://localhost:8000/reports/2025-12-04/audio"
```

**PowerShell version:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/reports/2025-12-04/audio" -Method GET
```

## Custom Report Generation

You can also provide custom data when generating a report:

```bash
curl -X POST "http://localhost:8000/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "trading_date": "2025-12-04",
    "client_id": "michael_brooks",
    "market_data": {
      "tickers": ["SMCI", "IREN"],
      "prices": {
        "SMCI": {"close": 850.25, "change_percent": 1.8},
        "IREN": {"close": 10.42, "change_percent": -0.9}
      }
    },
    "news_items": {
      "SMCI": [{
        "headline": "Supermicro extends rally",
        "source": "Example Newswire",
        "summary": "AI infrastructure demand stays strong"
      }]
    },
    "macro_context": {
      "risk_appetite": "moderate",
      "volatility_regime": "low_to_moderate"
    }
  }'
```

## Response Examples

### Generate Report Response
```json
{
  "trading_date": "2025-12-04",
  "client_id": "michael_brooks",
  "tickers": ["SMCI", "IREN"],
  "summary_text": "...",
  "key_insights": [...],
  "market_context": {...},
  "audio_gcs_path": "gs://bucket-name/reports/2025-12-04/audio.mp3"
}
```

### Get Report Audio Response
```json
{
  "client_id": "michael_brooks",
  "trading_date": "2025-12-04",
  "audio_gcs_path": "gs://bucket-name/reports/2025-12-04/audio.mp3"
}
```

## Notes

- All endpoints default to `client_id="michael_brooks"` if not specified
- If `trading_date` is omitted in generate request, it defaults to today's date
- If `market_data`, `news_items`, or `macro_context` are omitted, dummy data is used
- Trading dates must be in ISO format: `YYYY-MM-DD`


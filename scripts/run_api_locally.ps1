# Run the FastAPI app locally (PowerShell version)
# Prerequisites:
# - Virtual environment activated
# - Environment variables set:
#   - GOOGLE_API_KEY or GEMINI_API_KEY
#   - GOOGLE_APPLICATION_CREDENTIALS
#   - GCP_PROJECT_ID (optional, defaults to "mikebrooks")
#   - REPORTS_BUCKET_NAME

Write-Host "🚀 Starting FastAPI server locally..." -ForegroundColor Green
Write-Host ""

# Check if uvicorn is available
try {
    $null = Get-Command uvicorn -ErrorAction Stop
} catch {
    Write-Host "❌ uvicorn not found. Installing from requirements.txt..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Run the FastAPI app
Write-Host "Starting uvicorn on http://0.0.0.0:8000" -ForegroundColor Cyan
Write-Host "API docs available at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


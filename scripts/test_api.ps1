# Test script for FastAPI endpoints (PowerShell version)
# Prerequisites: API should be running on http://localhost:8000

$API_URL = "http://localhost:8000"
$TRADING_DATE = Get-Date -Format "yyyy-MM-dd"

Write-Host "🧪 Testing FastAPI endpoints" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Generate a report using dummy data
Write-Host "1️⃣  Generating report with dummy data (POST /reports/generate)..." -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "${API_URL}/reports/generate" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{}'
    
    Write-Host "✅ Report generated successfully!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
    Write-Host ""
    
    # Extract trading_date from response if available
    if ($response.trading_date) {
        $TRADING_DATE = $response.trading_date
        Write-Host "📅 Using trading_date from response: $TRADING_DATE" -ForegroundColor Cyan
    } else {
        Write-Host "📅 Using today's date: $TRADING_DATE" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Failed to generate report: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Test 2: Fetch the report
Write-Host "2️⃣  Fetching report for $TRADING_DATE (GET /reports/{trading_date})..." -ForegroundColor Yellow
Write-Host ""

try {
    $report = Invoke-RestMethod -Uri "${API_URL}/reports/${TRADING_DATE}"
    $report | ConvertTo-Json -Depth 10
    Write-Host ""
    Write-Host "✅ Report fetched successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to fetch report: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Test 3: Fetch audio metadata
Write-Host "3️⃣  Fetching audio metadata for $TRADING_DATE (GET /reports/{trading_date}/audio)..." -ForegroundColor Yellow
Write-Host ""

try {
    $audio = Invoke-RestMethod -Uri "${API_URL}/reports/${TRADING_DATE}/audio"
    $audio | ConvertTo-Json -Depth 10
    Write-Host ""
    Write-Host "✅ Audio metadata fetched successfully!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Failed to fetch audio metadata (this is OK if audio hasn't been generated yet): $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ Testing complete!" -ForegroundColor Green


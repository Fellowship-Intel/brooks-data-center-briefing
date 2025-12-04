# Test script for FastAPI report endpoints
# Prerequisites: FastAPI server must be running on http://localhost:8000

$baseUrl = "http://localhost:8000"
$ErrorActionPreference = "Stop"

Write-Host "🧪 Testing FastAPI Report Endpoints" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Generate a report using dummy data
Write-Host "1️⃣  Generating report with dummy data..." -ForegroundColor Yellow
try {
    $generateResponse = Invoke-RestMethod -Uri "$baseUrl/reports/generate" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{}'
    
    $tradingDate = $generateResponse.trading_date
    Write-Host "   ✅ Report generated successfully!" -ForegroundColor Green
    Write-Host "   📅 Trading Date: $tradingDate" -ForegroundColor Gray
    Write-Host "   📊 Client ID: $($generateResponse.client_id)" -ForegroundColor Gray
    
    if ($generateResponse.audio_gcs_path) {
        Write-Host "   🎵 Audio path: $($generateResponse.audio_gcs_path)" -ForegroundColor Gray
    }
    
    Write-Host ""
    
    # Test 2: Fetch that report
    Write-Host "2️⃣  Fetching report for $tradingDate..." -ForegroundColor Yellow
    try {
        $fetchResponse = Invoke-RestMethod -Uri "$baseUrl/reports/$tradingDate" -Method GET
        Write-Host "   ✅ Report fetched successfully!" -ForegroundColor Green
        Write-Host "   📝 Summary (first 100 chars): $($fetchResponse.summary_text.Substring(0, [Math]::Min(100, $fetchResponse.summary_text.Length)))..." -ForegroundColor Gray
        Write-Host ""
    } catch {
        Write-Host "   ❌ Failed to fetch report: $_" -ForegroundColor Red
        Write-Host ""
    }
    
    # Test 3: Fetch audio metadata
    Write-Host "3️⃣  Fetching audio metadata for $tradingDate..." -ForegroundColor Yellow
    try {
        $audioResponse = Invoke-RestMethod -Uri "$baseUrl/reports/$tradingDate/audio" -Method GET
        Write-Host "   ✅ Audio metadata fetched successfully!" -ForegroundColor Green
        Write-Host "   🎵 Audio GCS Path: $($audioResponse.audio_gcs_path)" -ForegroundColor Gray
        Write-Host ""
    } catch {
        Write-Host "   ⚠️  Audio metadata not available (this is OK if audio generation is still in progress)" -ForegroundColor Yellow
        Write-Host "   Error: $_" -ForegroundColor Gray
        Write-Host ""
    }
    
} catch {
    Write-Host "   ❌ Failed to generate report: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Make sure the FastAPI server is running:" -ForegroundColor Yellow
    Write-Host "   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Gray
    exit 1
}

Write-Host "✅ All tests completed!" -ForegroundColor Green


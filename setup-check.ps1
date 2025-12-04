# Setup Verification Script
# Run this to verify your setup is complete

Write-Host "🔍 Checking Setup..." -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python not found" -ForegroundColor Red
}

# Check Dependencies
Write-Host ""
Write-Host "Checking Dependencies..." -ForegroundColor Yellow
$deps = @("streamlit", "google.generativeai", "pandas", "yfinance", "fastapi")
foreach ($dep in $deps) {
    try {
        python -c "import $dep" 2>$null
        Write-Host "  ✅ $dep" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ $dep not installed" -ForegroundColor Red
    }
}

# Check Authentication
Write-Host ""
Write-Host "Checking Authentication..." -ForegroundColor Yellow
if (Test-Path ".secrets\app-backend-sa.json") {
    Write-Host "  ✅ Service account file found" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Service account file not found" -ForegroundColor Yellow
    Write-Host "     Using API key from .env or environment variable" -ForegroundColor Gray
}

if (Test-Path ".env") {
    Write-Host "  ✅ .env file found" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "     Set GEMINI_API_KEY environment variable or create .env file" -ForegroundColor Gray
}

# Check Environment Variables
Write-Host ""
Write-Host "Checking Environment Variables..." -ForegroundColor Yellow
if ($env:GEMINI_API_KEY) {
    Write-Host "  ✅ GEMINI_API_KEY is set" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  GEMINI_API_KEY not set" -ForegroundColor Yellow
}

if ($env:GOOGLE_APPLICATION_CREDENTIALS) {
    Write-Host "  ✅ GOOGLE_APPLICATION_CREDENTIALS is set" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  GOOGLE_APPLICATION_CREDENTIALS not set" -ForegroundColor Yellow
    if (Test-Path ".secrets\app-backend-sa.json") {
        Write-Host "     Run: `$env:GOOGLE_APPLICATION_CREDENTIALS=`"`$PWD\.secrets\app-backend-sa.json`"" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Set up authentication (see SETUP.md Step 3)" -ForegroundColor White
Write-Host "  2. Run the app: streamlit run app.py" -ForegroundColor White
Write-Host "  3. Or use: .\run.bat (for terminal version)" -ForegroundColor White


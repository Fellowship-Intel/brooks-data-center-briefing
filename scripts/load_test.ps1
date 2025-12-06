# Load testing script for Brooks Data Center application
# 
# Usage:
#   .\scripts\load_test.ps1 [options]
#
# Options:
#   -BaseUrl URL          Base URL for API (default: http://localhost:8000)
#   -Concurrent N         Number of concurrent requests (default: 10)
#   -Requests N           Number of requests per test (default: 10)
#   -Suite SUITE          Test suite: api, all (default: all)
#   -Output FILE          Output file for report
#   -Format FORMAT        Report format: json, csv (default: json)

param(
    [string]$BaseUrl = $env:BASE_URL,
    [int]$Concurrent = $env:CONCURRENT,
    [int]$Requests = $env:REQUESTS,
    [string]$Suite = $env:SUITE,
    [string]$Output = $env:OUTPUT,
    [string]$Format = $env:FORMAT
)

# Set defaults if not provided
if ([string]::IsNullOrEmpty($BaseUrl)) {
    $BaseUrl = "http://localhost:8000"
}

if ($Concurrent -eq 0) {
    $Concurrent = 10
}

if ($Requests -eq 0) {
    $Requests = 10
}

if ([string]::IsNullOrEmpty($Suite)) {
    $Suite = "all"
}

if ([string]::IsNullOrEmpty($Format)) {
    $Format = "json"
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StressTestScript = Join-Path $ScriptDir "stress_test.py"

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if stress_test.py exists
if (-not (Test-Path $StressTestScript)) {
    Write-Host "Error: stress_test.py not found at $StressTestScript" -ForegroundColor Red
    exit 1
}

# Build command arguments
$Arguments = @(
    "`"$StressTestScript`"",
    "--base-url", "`"$BaseUrl`"",
    "--concurrent", $Concurrent,
    "--requests", $Requests,
    "--suite", $Suite,
    "--format", $Format
)

if (-not [string]::IsNullOrEmpty($Output)) {
    $Arguments += "--output"
    $Arguments += "`"$Output`""
}

# Display configuration
Write-Host "Running stress tests..." -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl"
Write-Host "Concurrent: $Concurrent"
Write-Host "Requests: $Requests"
Write-Host "Suite: $Suite"
Write-Host ""

# Run the stress test
try {
    $exitCode = 0
    & python $Arguments
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "Stress tests completed successfully" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Stress tests failed with exit code: $exitCode" -ForegroundColor Red
    }
    
    exit $exitCode
} catch {
    Write-Host "Error running stress tests: $_" -ForegroundColor Red
    exit 1
}


# Migration Script: Move project from Google Drive to C:\Dev\brooks
# This script will copy all necessary files to the new location

$ErrorActionPreference = "Stop"

$sourcePath = "G:\My Drive\Cursor\Brooks"
$targetPath = "C:\Dev\brooks"

Write-Host "Migrating project to local folder..." -ForegroundColor Green
Write-Host "Source: $sourcePath" -ForegroundColor Cyan
Write-Host "Target: $targetPath" -ForegroundColor Cyan
Write-Host ""

# Check if source exists
if (-not (Test-Path $sourcePath)) {
    Write-Host "Source path not found: $sourcePath" -ForegroundColor Red
    Write-Host "Please update the source path in this script if different." -ForegroundColor Yellow
    exit 1
}

# Create target directory if it doesn't exist
if (-not (Test-Path $targetPath)) {
    Write-Host "Creating target directory: $targetPath" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
} else {
    Write-Host "Target directory already exists: $targetPath" -ForegroundColor Yellow
    $response = Read-Host "Continue anyway? (y/n)"
    if ($response -ne "y" -and $response -ne "Y") {
        exit 0
    }
}

Write-Host ""
Write-Host "Copying files..." -ForegroundColor Cyan

# Use robocopy for efficient copying
$robocopyArgs = @(
    $sourcePath,
    $targetPath,
    "/E",           # Copy subdirectories including empty ones
    "/XD",          # Exclude directories
    "__pycache__",
    ".git",
    "node_modules",
    "venv",
    "dist",
    "build",
    ".pytest_cache",
    "/XF",          # Exclude files
    "*.pyc",
    ".DS_Store",
    "Thumbs.db",
    "/NFL",         # Don't log file names
    "/NDL",         # Don't log directory names
    "/NJH",         # Don't log job header
    "/NJS"          # Don't log job summary
)

$robocopyResult = & robocopy @robocopyArgs

# Robocopy returns exit codes 0-7 for success, 8+ for errors
if ($LASTEXITCODE -ge 8) {
    Write-Host "Some files may not have been copied. Exit code: $LASTEXITCODE" -ForegroundColor Yellow
} else {
    Write-Host "Files copied successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Navigate to the new location:" -ForegroundColor White
Write-Host "     cd C:\Dev\brooks" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Verify .secrets folder was copied:" -ForegroundColor White
Write-Host "     Test-Path .secrets\app-backend-sa.json" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Set up environment variables:" -ForegroundColor White
Write-Host "     `$env:GOOGLE_APPLICATION_CREDENTIALS=`"`$PWD\.secrets\app-backend-sa.json`"" -ForegroundColor Gray
Write-Host "     `$env:GCP_PROJECT_ID=`"mikebrooks`"" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Install dependencies (if needed):" -ForegroundColor White
Write-Host "     pip install -r requirements.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Run the app:" -ForegroundColor White
Write-Host "     streamlit run app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Migration complete!" -ForegroundColor Green

# Enable Development Mode for Brooks App
# This bypasses OAuth authentication for local development

Write-Host "🔧 Enabling Development Mode..." -ForegroundColor Yellow

# Set environment variable
$env:ENVIRONMENT = "development"

# Stop existing Streamlit process
Write-Host "Stopping existing app..." -ForegroundColor Yellow
Get-Process python,streamlit -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*Brooks*' } | Stop-Process -Force
Start-Sleep -Seconds 2

# Start Streamlit with development mode
Write-Host "Starting app in development mode..." -ForegroundColor Green
Write-Host "You can now use the 'Initialize Dev Auth' button to bypass OAuth" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Dev\Brooks"
streamlit run app.py --server.port=8080 --server.address=0.0.0.0

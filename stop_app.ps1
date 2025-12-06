# Stop Streamlit App
# This script stops any running Streamlit/Python processes

Write-Host "🛑 Stopping Brooks Data Center Daily Briefing App..." -ForegroundColor Yellow
Write-Host ""

# Find processes using port 8080
$portProcesses = netstat -ano | Select-String ":8080" | ForEach-Object {
    if ($_ -match '\s+(\d+)\s*$') {
        $matches[1]
    }
} | Select-Object -Unique

if ($portProcesses) {
    Write-Host "Found processes using port 8080:" -ForegroundColor Yellow
    foreach ($pid in $portProcesses) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  - PID $pid : $($proc.ProcessName) - $($proc.Path)" -ForegroundColor Cyan
        }
    }
    Write-Host ""
    
    $portProcesses | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
    Write-Host "✅ Stopped processes on port 8080" -ForegroundColor Green
} else {
    Write-Host "No processes found using port 8080" -ForegroundColor Gray
}

# Also stop any Python/Streamlit processes related to the app
$pythonProcesses = Get-Process python,streamlit -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*Brooks*" -or $_.CommandLine -like "*app.py*"
}

if ($pythonProcesses) {
    Write-Host ""
    Write-Host "Found related Python/Streamlit processes:" -ForegroundColor Yellow
    foreach ($proc in $pythonProcesses) {
        Write-Host "  - PID $($proc.Id) : $($proc.ProcessName)" -ForegroundColor Cyan
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "✅ Stopped related processes" -ForegroundColor Green
} else {
    Write-Host "No related Python/Streamlit processes found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Done!" -ForegroundColor Green


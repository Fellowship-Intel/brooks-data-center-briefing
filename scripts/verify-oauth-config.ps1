# Google OAuth 2.0 Setup - Quick Verification Script
# This script helps verify your OAuth credentials are configured correctly

Write-Host "=== Brooks OAuth Configuration Verification ===" -ForegroundColor Cyan
Write-Host ""

# Check 1: Verify .secrets directory exists
Write-Host "Checking .secrets directory..." -ForegroundColor Yellow
if (Test-Path ".secrets") {
    Write-Host "✓ .secrets directory exists" -ForegroundColor Green
} else {
    Write-Host "✗ .secrets directory not found" -ForegroundColor Red
    Write-Host "  Creating .secrets directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path ".secrets" | Out-Null
    Write-Host "✓ Created .secrets directory" -ForegroundColor Green
}
Write-Host ""

# Check 2: Verify client_secret.json exists
Write-Host "Checking client_secret.json..." -ForegroundColor Yellow
if (Test-Path ".secrets\client_secret.json") {
    Write-Host "✓ client_secret.json exists" -ForegroundColor Green
    
    # Validate JSON structure
    try {
        $secrets = Get-Content ".secrets\client_secret.json" | ConvertFrom-Json
        
        if ($secrets.web) {
            Write-Host "✓ Valid JSON structure (web application)" -ForegroundColor Green
            
            # Check required fields
            if ($secrets.web.client_id) {
                Write-Host "✓ client_id found: $($secrets.web.client_id.Substring(0, 20))..." -ForegroundColor Green
            } else {
                Write-Host "✗ client_id missing" -ForegroundColor Red
            }
            
            if ($secrets.web.client_secret) {
                Write-Host "✓ client_secret found: ********" -ForegroundColor Green
            } else {
                Write-Host "✗ client_secret missing" -ForegroundColor Red
            }
            
            if ($secrets.web.redirect_uris) {
                Write-Host "✓ redirect_uris configured:" -ForegroundColor Green
                foreach ($uri in $secrets.web.redirect_uris) {
                    Write-Host "  - $uri" -ForegroundColor Cyan
                }
            } else {
                Write-Host "✗ redirect_uris missing" -ForegroundColor Red
            }
        } else {
            Write-Host "✗ Invalid JSON structure (missing 'web' key)" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Invalid JSON file: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "✗ client_secret.json not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "To set up OAuth credentials:" -ForegroundColor Yellow
    Write-Host "1. Go to https://console.cloud.google.com/" -ForegroundColor White
    Write-Host "2. Navigate to APIs and Services > Credentials" -ForegroundColor White
    Write-Host "3. Create OAuth 2.0 Client ID (Web application)" -ForegroundColor White
    Write-Host "4. Download JSON and save as .secrets\client_secret.json" -ForegroundColor White
    Write-Host ""
    Write-Host "See oauth_setup_guide.md for detailed instructions" -ForegroundColor Cyan
}
Write-Host ""

# Check 3: Environment variables (alternative method)
Write-Host "Checking environment variables..." -ForegroundColor Yellow
$hasClientId = [bool]$env:GOOGLE_CLIENT_ID
$hasClientSecret = [bool]$env:GOOGLE_CLIENT_SECRET
$hasRedirectUri = [bool]$env:REDIRECT_URI

if ($hasClientId -or $hasClientSecret -or $hasRedirectUri) {
    if ($hasClientId) {
        Write-Host "✓ GOOGLE_CLIENT_ID set: $($env:GOOGLE_CLIENT_ID.Substring(0, 20))..." -ForegroundColor Green
    } else {
        Write-Host "✗ GOOGLE_CLIENT_ID not set" -ForegroundColor Red
    }
    
    if ($hasClientSecret) {
        Write-Host "✓ GOOGLE_CLIENT_SECRET set: ********" -ForegroundColor Green
    } else {
        Write-Host "✗ GOOGLE_CLIENT_SECRET not set" -ForegroundColor Red
    }
    
    if ($hasRedirectUri) {
        Write-Host "✓ REDIRECT_URI set: $env:REDIRECT_URI" -ForegroundColor Green
    } else {
        Write-Host "  REDIRECT_URI not set (will use default: http://localhost:8080)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  No OAuth environment variables set (using client_secret.json)" -ForegroundColor Cyan
}
Write-Host ""

# Check 4: Development mode
Write-Host "Checking development mode..." -ForegroundColor Yellow
if ($env:ENVIRONMENT -eq "development") {
    Write-Host "✓ Development mode enabled (auth bypass available)" -ForegroundColor Green
} else {
    Write-Host "  Development mode not enabled" -ForegroundColor Cyan
    Write-Host "  To enable: `$env:ENVIRONMENT = 'development'" -ForegroundColor White
}
Write-Host ""

# Summary
Write-Host "=== Summary ===" -ForegroundColor Cyan
$hasJsonFile = Test-Path ".secrets\client_secret.json"
$hasEnvVars = $hasClientId -and $hasClientSecret

if ($hasJsonFile -or $hasEnvVars) {
    Write-Host "✓ OAuth credentials are configured" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Run: streamlit run app.py" -ForegroundColor White
    Write-Host "2. Navigate to http://localhost:8080" -ForegroundColor White
    Write-Host "3. Test the OAuth login flow" -ForegroundColor White
} else {
    Write-Host "✗ OAuth credentials not configured" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please follow the setup guide in oauth_setup_guide.md" -ForegroundColor Yellow
    Write-Host "Or enable development mode for testing without OAuth" -ForegroundColor Yellow
}
Write-Host ""

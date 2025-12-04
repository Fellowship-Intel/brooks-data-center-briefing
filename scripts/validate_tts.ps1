# Validate TTS functionality (PowerShell version)
# This script tests the Gemini TTS integration to ensure it's working correctly

$ErrorActionPreference = "Stop"

Write-Host "🧪 Validating TTS functionality" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if required environment variables are set
if (-not $env:GOOGLE_API_KEY -and -not $env:GEMINI_API_KEY) {
    Write-Host "❌ GOOGLE_API_KEY or GEMINI_API_KEY must be set" -ForegroundColor Red
    Write-Host "   Set it with: `$env:GOOGLE_API_KEY='your-key'" -ForegroundColor Yellow
    exit 1
}

if (-not $env:REPORTS_BUCKET_NAME) {
    Write-Host "⚠️  REPORTS_BUCKET_NAME not set, will skip GCS upload test" -ForegroundColor Yellow
    $SKIP_GCS = $true
} else {
    $SKIP_GCS = $false
}

Write-Host "✓ Environment variables checked" -ForegroundColor Green
Write-Host ""

# Test 1: Import TTS module
Write-Host "1️⃣  Testing TTS module import..." -ForegroundColor Yellow
try {
    python -c "from tts.gemini_tts import synthesize_speech; print('✓ TTS module imported successfully')"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to import TTS module" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Failed to import TTS module: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Generate a small audio sample
Write-Host ""
Write-Host "2️⃣  Testing audio synthesis..." -ForegroundColor Yellow
$TEST_TEXT = "This is a test of the Gemini TTS system. If you can hear this, the text-to-speech is working correctly."
$OUTPUT_FILE = "artifacts\audio\test_validation.wav"

# Create directory if it doesn't exist
New-Item -ItemType Directory -Force -Path "artifacts\audio" | Out-Null

$pythonScript = @"
from tts.gemini_tts import synthesize_speech
import os

test_text = """$TEST_TEXT"""
output_file = r"""$OUTPUT_FILE"""

try:
    audio_bytes = synthesize_speech(test_text, output_path=output_file)
    file_size = len(audio_bytes)
    print(f"✓ Audio generated successfully")
    print(f"  - Size: {file_size} bytes")
    print(f"  - Saved to: {output_file}")
    
    if os.path.exists(output_file):
        actual_size = os.path.getsize(output_file)
        print(f"  - File size: {actual_size} bytes")
        if actual_size > 0:
            print("✓ Audio file is valid and non-empty")
        else:
            print("⚠️  Warning: Audio file is empty")
            exit(1)
    else:
        print("⚠️  Warning: Output file was not created")
        exit(1)
        
except Exception as e:
    print(f"❌ Audio generation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
"@

try {
    $pythonScript | python
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Audio synthesis test failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Audio synthesis test failed: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Test GCS upload (if bucket is configured)
if (-not $SKIP_GCS) {
    Write-Host ""
    Write-Host "3️⃣  Testing GCS upload..." -ForegroundColor Yellow
    
    $gcsScript = @"
from gcp_clients import get_storage_client
from datetime import date
import os

bucket_name = """$env:REPORTS_BUCKET_NAME"""
test_file = r"""$OUTPUT_FILE"""

if not os.path.exists(test_file):
    print("❌ Test audio file not found")
    exit(1)

try:
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    
    # Upload to a test path
    test_path = f"test/tts_validation_{date.today().isoformat()}.wav"
    blob = bucket.blob(test_path)
    
    with open(test_file, 'rb') as f:
        blob.upload_from_file(f, content_type="audio/wav")
    
    print(f"✓ Audio uploaded to GCS successfully")
    print(f"  - Path: gs://{bucket_name}/{test_path}")
    
    # Clean up test file
    blob.delete()
    print(f"✓ Test file cleaned up from GCS")
    
except Exception as e:
    print(f"❌ GCS upload failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
"@

    try {
        $gcsScript | python
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ GCS upload test failed" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ GCS upload test failed: $_" -ForegroundColor Red
        exit 1
}
} else {
    Write-Host ""
    Write-Host "3️⃣  Skipping GCS upload test (REPORTS_BUCKET_NAME not set)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ TTS validation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 You can listen to the test audio at: ${OUTPUT_FILE}" -ForegroundColor Cyan


#!/bin/bash

# Validate TTS functionality
# This script tests the Gemini TTS integration to ensure it's working correctly

set -e

echo "🧪 Validating TTS functionality"
echo "================================"
echo ""

# Check if required environment variables are set
if [ -z "$GOOGLE_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GOOGLE_API_KEY or GEMINI_API_KEY must be set"
    echo "   Set it with: export GOOGLE_API_KEY=your-key"
    exit 1
fi

if [ -z "$REPORTS_BUCKET_NAME" ]; then
    echo "⚠️  REPORTS_BUCKET_NAME not set, will skip GCS upload test"
    SKIP_GCS=true
else
    SKIP_GCS=false
fi

echo "✓ Environment variables checked"
echo ""

# Test 1: Import TTS module
echo "1️⃣  Testing TTS module import..."
python3 -c "from tts.gemini_tts import synthesize_speech; print('✓ TTS module imported successfully')" || {
    echo "❌ Failed to import TTS module"
    exit 1
}

# Test 2: Generate a small audio sample
echo ""
echo "2️⃣  Testing audio synthesis..."
TEST_TEXT="This is a test of the Gemini TTS system. If you can hear this, the text-to-speech is working correctly."

OUTPUT_FILE="artifacts/audio/test_validation.wav"
mkdir -p artifacts/audio

python3 << EOF
from tts.gemini_tts import synthesize_speech
import os

test_text = "${TEST_TEXT}"
output_file = "${OUTPUT_FILE}"

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
EOF

if [ $? -ne 0 ]; then
    echo "❌ Audio synthesis test failed"
    exit 1
fi

# Test 3: Test GCS upload (if bucket is configured)
if [ "$SKIP_GCS" = false ]; then
    echo ""
    echo "3️⃣  Testing GCS upload..."
    python3 << EOF
from gcp_clients import get_storage_client
from datetime import date
import os

bucket_name = "${REPORTS_BUCKET_NAME}"
test_file = "${OUTPUT_FILE}"

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
EOF

    if [ $? -ne 0 ]; then
        echo "❌ GCS upload test failed"
        exit 1
    fi
else
    echo ""
    echo "3️⃣  Skipping GCS upload test (REPORTS_BUCKET_NAME not set)"
fi

echo ""
echo "================================"
echo "✅ TTS validation complete!"
echo ""
echo "💡 You can listen to the test audio at: ${OUTPUT_FILE}"

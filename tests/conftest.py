import os
import pytest  # type: ignore[reportMissingImports]
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_gemini():
    """Mock Gemini API key retrieval and client.
    
    Uses real API key from environment (GEMINI_API_KEY or GOOGLE_API_KEY)
    but mocks the actual API calls to avoid making real requests.
    """
    # Get real API key from environment
    real_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    with patch("report_service.access_secret_value") as mock_secret, \
         patch("report_service.genai.GenerativeModel") as mock_model_class:
        
        # Mock secret manager to return the real API key from environment
        # This allows genai.configure() to use the real key
        if real_api_key:
            mock_secret.return_value = real_api_key
        else:
            # Fallback to fake key if env var not set (shouldn't happen in your case)
            mock_secret.return_value = "fake-api-key-12345"
        
        # Mock the Gemini model (so we don't make real API calls)
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        # Mock the generate_content response
        mock_response = MagicMock()
        mock_response.text = '{"summary_text": "Test summary for trading day", "key_insights": ["Insight 1", "Insight 2"], "market_context": "Test market context"}'
        mock_model.generate_content.return_value = mock_response
        
        yield {
            "mock_secret": mock_secret,
            "mock_model": mock_model,
            "mock_model_class": mock_model_class,
            "api_key_used": real_api_key or "fake-api-key-12345",
        }


@pytest.fixture
def mock_firestore():
    """Mock Firestore client + repository interactions."""
    with patch("report_service.get_firestore_client") as mock_client:
        client = MagicMock()
        mock_client.return_value = client

        # Mock repo functions to simulate Firestore writes
        with patch("report_service.create_or_update_daily_report") as mock_upsert, \
             patch("report_service.update_daily_report_audio_path") as mock_audio_update:

            # These functions return None in the actual implementation
            mock_upsert.return_value = None
            mock_audio_update.return_value = None

            yield {
                "client": client,
                "mock_upsert": mock_upsert,
                "mock_audio_update": mock_audio_update,
            }


@pytest.fixture
def mock_storage():
    """Mock Cloud Storage bucket + blob.upload_from_string."""
    with patch("report_service.get_storage_client") as mock_client, \
         patch("report_service.get_reports_bucket_name") as mock_bucket_name:
        
        # Mock bucket name
        mock_bucket_name.return_value = "test-reports-bucket"
        
        storage_client = MagicMock()
        mock_client.return_value = storage_client

        bucket = MagicMock()
        blob = MagicMock()

        storage_client.bucket.return_value = bucket
        bucket.blob.return_value = blob

        yield {
            "client": storage_client,
            "bucket": bucket,
            "blob": blob,
            "mock_bucket_name": mock_bucket_name,
        }


@pytest.fixture
def mock_tts():
    """Mock TTS so no real Gemini call happens."""
    with patch("report_service.tts_synthesize") as mock_tts_func:
        mock_tts_func.return_value = (b"FAKE_AUDIO_BYTES", "gemini")
        yield mock_tts_func


@pytest.fixture
def mock_eleven_labs():
    """Mock Eleven Labs TTS."""
    with patch("tts.eleven_labs_tts.ELEVEN_LABS_AVAILABLE", True), \
         patch("tts.eleven_labs_tts.generate") as mock_generate, \
         patch("tts.eleven_labs_tts.set_api_key"), \
         patch("tts.eleven_labs_tts.voices") as mock_voices, \
         patch("tts.eleven_labs_tts.ElevenLabs"):
        
        # Mock voice response
        mock_voice = MagicMock()
        mock_voice.name = "Rachel"
        mock_voice.voice_id = "test_voice_id"
        mock_voices.return_value.voices = [mock_voice]
        
        # Mock audio generation
        mock_generate.return_value = b"fake_eleven_labs_audio"
        
        yield {
            "generate": mock_generate,
            "voices": mock_voices,
        }


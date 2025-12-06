"""Tests for Eleven Labs TTS integration."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.exceptions import TTSGenerationError, APIError


class TestElevenLabsTTS:
    """Test Eleven Labs TTS service."""
    
    @pytest.fixture
    def mock_eleven_labs(self):
        """Mock Eleven Labs SDK."""
        with patch('tts.eleven_labs_tts.ELEVEN_LABS_AVAILABLE', True), \
             patch('tts.eleven_labs_tts.generate') as mock_generate, \
             patch('tts.eleven_labs_tts.set_api_key'), \
             patch('tts.eleven_labs_tts.voices') as mock_voices, \
             patch('tts.eleven_labs_tts.ElevenLabs') as mock_client:
            
            # Mock voice response
            mock_voice = MagicMock()
            mock_voice.name = "Rachel"
            mock_voice.voice_id = "test_voice_id"
            mock_voices.return_value.voices = [mock_voice]
            
            # Mock audio generation
            mock_generate.return_value = b"fake_audio_bytes"
            
            yield {
                "generate": mock_generate,
                "voices": mock_voices,
                "client": mock_client,
            }
    
    def test_initialization_with_api_key(self, mock_eleven_labs):
        """Test TTS initialization with API key."""
        from tts.eleven_labs_tts import ElevenLabsTTS
        
        with patch('tts.eleven_labs_tts._USE_SECRET_MANAGER', False), \
             patch.dict('os.environ', {'ELEVEN_LABS_API_KEY': 'test_key'}):
            tts = ElevenLabsTTS(api_key='test_key')
            assert tts.api_key == 'test_key'
    
    def test_synthesize_success(self, mock_eleven_labs):
        """Test successful audio synthesis."""
        from tts.eleven_labs_tts import ElevenLabsTTS
        
        with patch('tts.eleven_labs_tts._USE_SECRET_MANAGER', False), \
             patch.dict('os.environ', {'ELEVEN_LABS_API_KEY': 'test_key'}):
            tts = ElevenLabsTTS(api_key='test_key')
            audio_bytes = tts.synthesize("Test text")
            
            assert audio_bytes == b"fake_audio_bytes"
            mock_eleven_labs["generate"].assert_called_once()
    
    def test_synthesize_empty_text(self, mock_eleven_labs):
        """Test synthesis with empty text raises error."""
        from tts.eleven_labs_tts import ElevenLabsTTS
        
        with patch('tts.eleven_labs_tts._USE_SECRET_MANAGER', False), \
             patch.dict('os.environ', {'ELEVEN_LABS_API_KEY': 'test_key'}):
            tts = ElevenLabsTTS(api_key='test_key')
            
            with pytest.raises(ValueError):
                tts.synthesize("")
    
    def test_synthesize_api_error(self, mock_eleven_labs):
        """Test handling of API errors."""
        from tts.eleven_labs_tts import ElevenLabsTTS
        
        # Make generate raise an exception
        mock_eleven_labs["generate"].side_effect = Exception("API error")
        
        with patch('tts.eleven_labs_tts._USE_SECRET_MANAGER', False), \
             patch.dict('os.environ', {'ELEVEN_LABS_API_KEY': 'test_key'}):
            tts = ElevenLabsTTS(api_key='test_key')
            
            with pytest.raises(TTSGenerationError):
                tts.synthesize("Test text")
    
    def test_voice_selection(self, mock_eleven_labs):
        """Test voice selection logic."""
        from tts.eleven_labs_tts import ElevenLabsTTS
        
        with patch('tts.eleven_labs_tts._USE_SECRET_MANAGER', False), \
             patch.dict('os.environ', {'ELEVEN_LABS_API_KEY': 'test_key'}):
            tts = ElevenLabsTTS(api_key='test_key')
            # Should use the mocked voice
            assert tts.voice_id is not None


class TestTTSService:
    """Test TTS service abstraction."""
    
    def test_eleven_labs_primary_fallback(self):
        """Test Eleven Labs as primary with Gemini fallback."""
        from tts.tts_service import TTSService
        
        with patch('tts.tts_service.ElevenLabsTTS') as mock_eleven, \
             patch('tts.tts_service.GeminiTTSConfig') as mock_gemini:
            
            # Mock Eleven Labs success
            mock_eleven_instance = MagicMock()
            mock_eleven_instance.synthesize.return_value = b"eleven_labs_audio"
            mock_eleven.return_value = mock_eleven_instance
            
            service = TTSService(primary_provider="eleven_labs", fallback_provider="gemini")
            audio, provider = service.synthesize("Test text")
            
            assert provider == "eleven_labs"
            assert audio == b"eleven_labs_audio"
            mock_eleven_instance.synthesize.assert_called_once()
    
    def test_fallback_to_gemini(self):
        """Test fallback to Gemini when Eleven Labs fails."""
        from tts.tts_service import TTSService
        from utils.exceptions import TTSGenerationError
        
        with patch('tts.tts_service.ElevenLabsTTS') as mock_eleven, \
             patch('tts.tts_service.GeminiTTSConfig') as mock_gemini:
            
            # Mock Eleven Labs failure
            mock_eleven_instance = MagicMock()
            mock_eleven_instance.synthesize.side_effect = TTSGenerationError("Eleven Labs failed")
            mock_eleven.return_value = mock_eleven_instance
            
            # Mock Gemini success
            mock_gemini_instance = MagicMock()
            mock_gemini_instance.synthesize.return_value = b"gemini_audio"
            mock_gemini.return_value = mock_gemini_instance
            
            service = TTSService(primary_provider="eleven_labs", fallback_provider="gemini")
            audio, provider = service.synthesize("Test text")
            
            assert provider == "gemini"
            assert audio == b"gemini_audio"
    
    def test_all_providers_fail(self):
        """Test error when all providers fail."""
        from tts.tts_service import TTSService
        from utils.exceptions import TTSGenerationError
        
        with patch('tts.tts_service.ElevenLabsTTS') as mock_eleven, \
             patch('tts.tts_service.GeminiTTSConfig') as mock_gemini:
            
            # Both fail
            mock_eleven_instance = MagicMock()
            mock_eleven_instance.synthesize.side_effect = TTSGenerationError("Eleven Labs failed")
            mock_eleven.return_value = mock_eleven_instance
            
            mock_gemini_instance = MagicMock()
            mock_gemini_instance.synthesize.side_effect = TTSGenerationError("Gemini failed")
            mock_gemini.return_value = mock_gemini_instance
            
            service = TTSService(primary_provider="eleven_labs", fallback_provider="gemini")
            
            with pytest.raises(TTSGenerationError):
                service.synthesize("Test text")


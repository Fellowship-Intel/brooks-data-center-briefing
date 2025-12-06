"""Eleven Labs TTS integration."""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional

try:
    from elevenlabs import generate, set_api_key, voices, VoiceSettings
    from elevenlabs.client import ElevenLabs
    ELEVEN_LABS_AVAILABLE = True
except ImportError:
    ELEVEN_LABS_AVAILABLE = False
    # Create dummy classes for type hints
    class ElevenLabs:
        pass
    class VoiceSettings:
        pass

# Try to import from gcp_clients for Secret Manager, fall back to env var
try:
    from gcp_clients import access_eleven_labs_api_key
    _USE_SECRET_MANAGER = True
except ImportError:
    _USE_SECRET_MANAGER = False

from utils.exceptions import TTSGenerationError, APIError

logger = logging.getLogger(__name__)


# Recommended female, professional, natural-sounding voices
# Research shows these are good options - will be verified during implementation
RECOMMENDED_VOICES = [
    "Rachel",  # Professional, clear, natural
    "Bella",   # Warm, professional
    "Antoni",  # Note: Verify this is female
    "Elli",    # Professional, clear
    "Dorothy", # Professional, authoritative
]

DEFAULT_VOICE = "Rachel"  # Will be set after voice research


class ElevenLabsTTS:
    """
    Eleven Labs TTS client wrapper.
    
    Provides text-to-speech conversion using Eleven Labs API with
    a female, professional, natural-sounding voice.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
    ) -> None:
        """
        Initialize Eleven Labs TTS client.
        
        Args:
            api_key: Eleven Labs API key. If None, retrieved from Secret Manager or env.
            voice_id: Voice ID to use. If None, uses default recommended voice.
            model_id: Model ID for TTS generation
            stability: Voice stability (0.0-1.0)
            similarity_boost: Similarity boost (0.0-1.0)
            style: Style setting (0.0-1.0)
            use_speaker_boost: Whether to use speaker boost
        """
        if not ELEVEN_LABS_AVAILABLE:
            raise ImportError(
                "elevenlabs package not installed. Install with: pip install elevenlabs"
            )
        
        # Get API key
        if api_key:
            self.api_key = api_key
        elif _USE_SECRET_MANAGER:
            try:
                self.api_key = access_eleven_labs_api_key()
            except Exception as e:
                logger.warning("Failed to get API key from Secret Manager: %s", str(e))
                self.api_key = os.getenv("ELEVEN_LABS_API_KEY")
        else:
            self.api_key = os.getenv("ELEVEN_LABS_API_KEY")
        
        if not self.api_key:
            raise RuntimeError(
                "Eleven Labs API key not found. Set ELEVEN_LABS_API_KEY in environment, "
                "or ensure ELEVEN_LABS_API_KEY exists in Secret Manager."
            )
        
        # Set API key
        set_api_key(self.api_key)
        self.client = ElevenLabs(api_key=self.api_key)
        
        # Get or set voice ID
        self.voice_id = voice_id or os.getenv("ELEVEN_LABS_VOICE_ID") or self._get_default_voice()
        self.model_id = model_id
        self.voice_settings = VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
            use_speaker_boost=use_speaker_boost,
        )
        
        logger.info("Eleven Labs TTS initialized with voice_id=%s", self.voice_id)
    
    def _get_default_voice(self) -> str:
        """
        Get default voice ID by name.
        
        Returns:
            Voice ID string
        """
        try:
            # Get available voices
            available_voices = voices()
            
            # Try to find recommended voice by name
            for voice_name in RECOMMENDED_VOICES:
                for voice in available_voices.voices:
                    if voice.name == voice_name:
                        logger.info("Selected Eleven Labs voice: %s (ID: %s)", voice.name, voice.voice_id)
                        return voice.voice_id
            
            # If no recommended voice found, use first available
            if available_voices.voices:
                voice = available_voices.voices[0]
                logger.warning(
                    "Recommended voices not found. Using first available: %s (ID: %s)",
                    voice.name,
                    voice.voice_id
                )
                return voice.voice_id
            
            raise RuntimeError("No voices available from Eleven Labs API")
            
        except Exception as e:
            logger.error("Failed to get voices from Eleven Labs: %s", str(e))
            # Fallback to a known voice ID (Rachel's ID - update if needed)
            logger.warning("Using fallback voice ID")
            return "21m00Tcm4TlvDq8ikWAM"  # Rachel's voice ID (verify this)
    
    def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None,
    ) -> bytes:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save audio file (WAV format)
            
        Returns:
            Audio data as bytes (WAV format)
            
        Raises:
            TTSGenerationError: If synthesis fails
            APIError: If API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text must not be empty")
        
        try:
            logger.debug(
                "Generating speech with Eleven Labs: voice_id=%s, text_length=%d",
                self.voice_id,
                len(text)
            )
            
            # Generate audio
            audio_bytes = generate(
                text=text,
                voice=self.voice_id,
                model=self.model_id,
                voice_settings=self.voice_settings,
            )
            
            # Save to file if path provided
            if output_path:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(audio_bytes)
                logger.info("Saved Eleven Labs audio to %s", output_path)
            
            logger.debug("Successfully generated audio: %d bytes", len(audio_bytes))
            return audio_bytes
            
        except Exception as e:
            error_msg = f"Eleven Labs TTS generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Check if it's an API error
            if "api" in str(e).lower() or "http" in str(e).lower():
                raise APIError(
                    error_msg,
                    api_name="eleven_labs",
                    response=str(e)
                ) from e
            
            raise TTSGenerationError(
                error_msg,
                provider="eleven_labs",
                text_length=len(text),
            ) from e


def synthesize_speech(
    text: str,
    output_path: Optional[str] = None,
    voice_id: Optional[str] = None,
) -> bytes:
    """
    Convenience function for Eleven Labs TTS synthesis.
    
    Args:
        text: Text to convert to speech
        output_path: Optional path to save audio file
        voice_id: Optional voice ID override
        
    Returns:
        Audio data as bytes
    """
    tts = ElevenLabsTTS(voice_id=voice_id)
    return tts.synthesize(text, output_path=output_path)


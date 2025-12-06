"""TTS service abstraction layer supporting multiple providers."""
from __future__ import annotations

import logging
from typing import Optional
from pathlib import Path

from utils.exceptions import TTSGenerationError
from utils.retry_utils import retry_on_api_error

logger = logging.getLogger(__name__)


class TTSService:
    """
    Unified TTS service abstraction.
    
    Supports multiple TTS providers with automatic fallback:
    - Primary: Eleven Labs
    - Fallback: Gemini TTS
    """
    
    def __init__(
        self,
        primary_provider: str = "eleven_labs",
        fallback_provider: str = "gemini",
    ):
        """
        Initialize TTS service.
        
        Args:
            primary_provider: Primary TTS provider ("eleven_labs" or "gemini")
            fallback_provider: Fallback TTS provider
        """
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self._eleven_labs = None
        self._gemini_tts = None
        
        logger.info("TTS Service initialized: primary=%s, fallback=%s", primary_provider, fallback_provider)
    
    def _get_eleven_labs(self):
        """Lazy load Eleven Labs TTS."""
        if self._eleven_labs is None:
            try:
                from tts.eleven_labs_tts import ElevenLabsTTS
                self._eleven_labs = ElevenLabsTTS()
            except Exception as e:
                logger.warning("Failed to initialize Eleven Labs TTS: %s", str(e))
                raise
        return self._eleven_labs
    
    def _get_gemini_tts(self):
        """Lazy load Gemini TTS."""
        if self._gemini_tts is None:
            try:
                from tts.gemini_tts import GeminiTTSConfig
                self._gemini_tts = GeminiTTSConfig()
            except Exception as e:
                logger.warning("Failed to initialize Gemini TTS: %s", str(e))
                raise
        return self._gemini_tts
    
    @retry_on_api_error(max_retries=2)
    def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> tuple[bytes, str]:
        """
        Synthesize speech from text with automatic fallback.
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save audio file
            provider: Optional provider override ("eleven_labs" or "gemini")
            
        Returns:
            Tuple of (audio_bytes, provider_used)
            
        Raises:
            TTSGenerationError: If all providers fail
        """
        # Determine which provider to try first
        if provider:
            providers_to_try = [provider]
            if provider == self.primary_provider and self.fallback_provider:
                providers_to_try.append(self.fallback_provider)
            elif provider == self.fallback_provider and self.primary_provider:
                providers_to_try.append(self.primary_provider)
        else:
            providers_to_try = [self.primary_provider]
            if self.fallback_provider:
                providers_to_try.append(self.fallback_provider)
        
        last_error = None
        
        for provider_name in providers_to_try:
            try:
                logger.info("Attempting TTS with provider: %s", provider_name)
                
                if provider_name == "eleven_labs":
                    tts_client = self._get_eleven_labs()
                    audio_bytes = tts_client.synthesize(text, output_path=output_path)
                elif provider_name == "gemini":
                    tts_client = self._get_gemini_tts()
                    audio_bytes = tts_client.synthesize(text, output_path=output_path)
                else:
                    raise ValueError(f"Unknown TTS provider: {provider_name}")
                
                logger.info("Successfully generated audio with provider: %s (%d bytes)", provider_name, len(audio_bytes))
                return audio_bytes, provider_name
                
            except Exception as e:
                last_error = e
                logger.warning(
                    "TTS provider %s failed: %s. Trying fallback...",
                    provider_name,
                    str(e)
                )
                continue
        
        # All providers failed
        error_msg = f"All TTS providers failed. Last error: {str(last_error)}"
        logger.error(error_msg, exc_info=True)
        raise TTSGenerationError(
            error_msg,
            provider="all",
            text_length=len(text),
        ) from last_error


# Global TTS service instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get or create global TTS service instance."""
    global _tts_service
    if _tts_service is None:
        # Determine provider from environment or use default
        import os
        primary = os.getenv("TTS_PROVIDER", "eleven_labs")
        if primary not in ["eleven_labs", "gemini"]:
            primary = "eleven_labs"
        
        fallback = "gemini" if primary == "eleven_labs" else "eleven_labs"
        _tts_service = TTSService(primary_provider=primary, fallback_provider=fallback)
    return _tts_service


def synthesize_speech(
    text: str,
    output_path: Optional[str] = None,
    provider: Optional[str] = None,
) -> tuple[bytes, str]:
    """
    Convenience function for TTS synthesis.
    
    Args:
        text: Text to convert to speech
        output_path: Optional path to save audio file
        provider: Optional provider override
        
    Returns:
        Tuple of (audio_bytes, provider_used)
    """
    service = get_tts_service()
    return service.synthesize(text, output_path=output_path, provider=provider)


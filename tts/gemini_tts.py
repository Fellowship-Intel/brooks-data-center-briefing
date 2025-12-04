from __future__ import annotations

import os
import wave
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

# Try to import from gcp_clients for Secret Manager, fall back to env var
try:
    from gcp_clients import access_secret_value
    _USE_SECRET_MANAGER = True
except ImportError:
    _USE_SECRET_MANAGER = False


class GeminiTTSConfig:
    """
    Configuration and client wrapper for Gemini TTS.

    Expects GOOGLE_API_KEY to be set in the environment, or GEMINI_API_KEY in Secret Manager.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash-preview-tts",
        voice_name: str = "Kore",
        sample_rate_hz: int = 24000,
        channels: int = 1,
        sample_width: int = 2,
    ) -> None:
        if api_key:
            self.api_key = api_key
        elif _USE_SECRET_MANAGER:
            # Try Secret Manager first
            try:
                self.api_key = access_secret_value("GEMINI_API_KEY")
            except Exception:
                # Fall back to environment variable
                self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        else:
            self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise RuntimeError(
                "API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY in environment, "
                "or ensure GEMINI_API_KEY exists in Secret Manager."
            )

        self.model = model
        self.voice_name = voice_name
        self.sample_rate_hz = sample_rate_hz
        self.channels = channels
        self.sample_width = sample_width

        # Single reusable client instance
        self._client = genai.Client(api_key=self.api_key)

    def synthesize(
        self,
        text: str,
        *,
        output_path: Optional[Path] = None,
    ) -> bytes:
        """
        Synthesize speech from text using Gemini TTS.

        Returns raw PCM bytes.
        If output_path is provided, also writes a WAV file.
        """
        if not text or not text.strip():
            raise ValueError("Text must be a non-empty string.")

        response = self._client.models.generate_content(
            model=self.model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice_name
                        )
                    )
                ),
            ),
        )

        # First candidate, first part is assumed to contain audio
        try:
            part = response.candidates[0].content.parts[0]
            pcm: bytes = part.inline_data.data  # type: ignore[attr-defined]
        except Exception as exc:
            raise RuntimeError(f"Unexpected audio format from Gemini TTS: {exc}") from exc

        if output_path is not None:
            self._write_wave(output_path, pcm)

        return pcm

    def _write_wave(self, filename: Path, pcm: bytes) -> None:
        """
        Write raw PCM bytes to a WAV file with the configured audio format.
        """
        filename.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(filename), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.sample_width)
            wf.setframerate(self.sample_rate_hz)
            wf.writeframes(pcm)


_default_tts_config: Optional[GeminiTTSConfig] = None


def get_tts() -> GeminiTTSConfig:
    """
    Lazily construct and reuse a single GeminiTTSConfig instance.
    """
    global _default_tts_config
    if _default_tts_config is None:
        _default_tts_config = GeminiTTSConfig()
    return _default_tts_config


def synthesize_speech(
    text: str,
    *,
    output_path: Optional[str] = None,
) -> bytes:
    """
    Simple convenience wrapper used by the rest of the app.

    - text: text to be spoken
    - output_path: optional path to store a WAV file on disk
    """
    path = Path(output_path) if output_path else None
    return get_tts().synthesize(text, output_path=path)


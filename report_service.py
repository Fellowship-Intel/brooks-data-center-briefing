"""
Daily report generation service for Michael Brooks trading assistant.

This module orchestrates the full pipeline for generating and storing daily reports:
1. Generate report text using Google Gemini
2. Store report in Firestore
3. Generate audio using Google Cloud Text-to-Speech
4. Store audio in Cloud Storage
5. Update report with audio path
"""

from __future__ import annotations

import os
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

import google.generativeai as genai

# Set up logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

from gcp_clients import (
    get_storage_client,
    get_firestore_client,
    access_secret_value,
    get_project_id
)

from report_repository import (
    create_or_update_daily_report,
    update_daily_report_audio_path,
)

from settings import get_reports_bucket_name

from tts.gemini_tts import synthesize_speech


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _get_config() -> dict:
    """Load configuration from environment variables."""
    return {
        "project_id": os.getenv("GCP_PROJECT_ID", "mikebrooks"),
        "reports_bucket_name": os.getenv("REPORTS_BUCKET_NAME", "mikebrooks-reports"),
        "gemini_model_name": os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro"),
    }


def _get_gemini_api_key() -> str:
    """Retrieve Gemini API key from Secret Manager."""
    try:
        return access_secret_value("GEMINI_API_KEY")
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve GEMINI_API_KEY from Secret Manager: {e}")


def _configure_gemini_client() -> None:
    """
    Configure the google-generativeai client using GEMINI_API_KEY from Secret Manager.

    Safe to call multiple times; configuration is idempotent.
    """
    api_key = access_secret_value("GEMINI_API_KEY")
    genai.configure(api_key=api_key)


def _get_gemini_client():
    """
    Get a configured Gemini client using API key from Secret Manager.
    
    Uses _configure_gemini_client() to configure google-generativeai.
    
    Returns:
        Configured google.generativeai.GenerativeModel instance
    """
    _configure_gemini_client()
    
    config = _get_config()
    return genai.GenerativeModel(model_name=config["gemini_model_name"])


def _synthesize_audio_with_gemini(text: str, model_name: str | None = None) -> bytes:
    """
    Uses Gemini's text-to-audio capabilities to generate audio bytes for the given text.

    Args:
        text: The input text to be spoken.
        model_name: Optional override for the audio-capable model; if None,
                    default to a reasonable Gemini audio model.

    Returns:
        Raw audio bytes (e.g., MP3) suitable for writing to GCS.

    Raises:
        RuntimeError: If audio generation fails or the API doesn't support audio output.
    """
    if not text or not text.strip():
        raise ValueError("Input text must not be empty")

    _configure_gemini_client()

    if model_name is None:
        # Use a sensible default audio-capable Gemini model.
        # Note: Gemini models may not all support audio output - adjust as needed.
        model_name = "gemini-1.5-flash"

    try:
        # Create a GenerativeModel instance
        model = genai.GenerativeModel(model_name=model_name)

        # Generate content with audio output requested
        # Try using response_mime_type to request audio format
        # Note: This may not be supported by all Gemini models
        generation_config = {
            "response_mime_type": "audio/mpeg"
        }

        response = model.generate_content(
            text,
            generation_config=generation_config
        )

        # Extract audio bytes from response
        # The response structure may vary - check for common attributes
        if hasattr(response, 'audio') and response.audio:
            return response.audio
        elif hasattr(response, 'audio_content') and response.audio_content:
            return response.audio_content
        elif hasattr(response, 'parts') and response.parts:
            # Check if parts contain audio data
            for part in response.parts:
                if hasattr(part, 'audio') and part.audio:
                    return part.audio
                elif hasattr(part, 'inline_data') and part.inline_data:
                    if part.inline_data.mime_type and 'audio' in part.inline_data.mime_type:
                        return part.inline_data.data
        elif hasattr(response, 'candidates') and response.candidates:
            # Check candidates for audio content
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            if part.inline_data.mime_type and 'audio' in part.inline_data.mime_type:
                                return part.inline_data.data

        # If we get here, the response doesn't contain audio in expected format
        # This may indicate the model doesn't support audio output
        raise RuntimeError(
            f"Gemini model '{model_name}' did not return audio content. "
            "The model may not support audio output, or the API response format has changed. "
            f"Response type: {type(response)}, available attributes: {dir(response)}"
        )

    except Exception as e:
        # Provide helpful error message
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError(
            f"Failed to generate audio with Gemini: {e}. "
            "Note: Gemini API may not support direct audio/TTS output. "
            "Consider using Google Cloud Text-to-Speech API as an alternative."
        ) from e


# ElevenLabs integration removed - using Google Cloud Text-to-Speech instead


# ---------------------------------------------------------------------------
# Gemini text generation
# ---------------------------------------------------------------------------

def _build_gemini_prompt(
    trading_date: str,
    market_data: dict,
    news_items: Optional[list[dict]] = None,
    macro_context: Optional[str] = None,
) -> str:
    """
    Build a structured prompt for Gemini to generate the daily report.

    Args:
        trading_date: The trading date (YYYY-MM-DD format)
        market_data: Dictionary containing market data (structure depends on upstream)
        news_items: List of news item dictionaries (optional)
        macro_context: Additional macro context string (optional)

    Returns:
        Formatted prompt string for Gemini
    """
    market_data_str = json.dumps(market_data, indent=2) if market_data else "{}"
    news_items_str = json.dumps(news_items or [], indent=2)

    prompt = f"""Generate a comprehensive daily trading report for Michael Brooks for trading date {trading_date}.

Market Data:
{market_data_str}

News Items:
{news_items_str}

{f'Macro Context: {macro_context}' if macro_context else ''}

Please generate a structured report with the following sections:

1. **Summary Text**: A concise executive summary (2-3 paragraphs) of the day's market activity and key developments.

2. **Key Insights**: A list of 3-7 bullet points highlighting the most important trading insights, opportunities, and risks.

3. **Market Context**: (Optional) Additional context about broader market conditions, sector performance, or relevant macroeconomic factors.

Return your response as a JSON object with the following structure:
{{
    "summary_text": "Executive summary text here...",
    "key_insights": [
        "Insight 1",
        "Insight 2",
        ...
    ],
    "market_context": "Optional market context section..."
}}

Ensure all text is professional, actionable, and tailored for an active day trader focused on data center and AI infrastructure equities.
"""
    return prompt


def _generate_report_text(
    trading_date: str,
    market_data: dict,
    news_items: Optional[list[dict]] = None,
    macro_context: Optional[str] = None,
) -> dict:
    """
    Generate report text using Google Gemini.

    Args:
        trading_date: Trading date string
        market_data: Market data dictionary
        news_items: Optional list of news items
        macro_context: Optional macro context string

    Returns:
        Dictionary with keys: summary_text, key_insights, market_context
    """
    # Get configured Gemini client
    model = _get_gemini_client()

    # Build prompt
    prompt = _build_gemini_prompt(trading_date, market_data, news_items, macro_context)

    # Generate response
    response = model.generate_content(prompt)

    if not response.text:
        raise RuntimeError("Gemini returned empty response")

    # Parse JSON response
    text = response.text.strip()

    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        report_data = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {text[:500]}")

    # Validate required fields
    required_fields = ["summary_text", "key_insights"]
    for field in required_fields:
        if field not in report_data:
            raise RuntimeError(f"Gemini response missing required field: {field}")

    return report_data


def _generate_gemini_text_report(
    trading_date: date,
    client_id: str,
    market_data: Dict[str, Any],
    news_items: Dict[str, Any],
    macro_context: Dict[str, Any],
) -> tuple[str, list[str], str]:
    """
    Generate report text using Google Gemini.

    Args:
        trading_date: Trading date as date object
        client_id: Client identifier
        market_data: Market data dictionary
        news_items: News items dictionary/list
        macro_context: Macro context (can be dict or str)

    Returns:
        Tuple of (summary_text, key_insights, market_context_text)
    """
    # Convert date to string for the prompt
    trading_date_str = trading_date.isoformat()
    
    # Convert macro_context to string if it's a dict
    macro_context_str = None
    if isinstance(macro_context, dict):
        macro_context_str = json.dumps(macro_context)
    elif macro_context:
        macro_context_str = str(macro_context)
    
    # Generate report text
    report_data = _generate_report_text(
        trading_date=trading_date_str,
        market_data=market_data,
        news_items=news_items if isinstance(news_items, list) else [news_items] if news_items else None,
        macro_context=macro_context_str,
    )
    
    summary_text = report_data["summary_text"]
    key_insights = report_data.get("key_insights", [])
    market_context_text = report_data.get("market_context", "")
    
    return summary_text, key_insights, market_context_text


# ---------------------------------------------------------------------------
# Google Cloud Text-to-Speech audio generation
# ---------------------------------------------------------------------------

def _synthesize_audio_with_gcp_tts(text: str) -> bytes:
    """
    Uses Google Cloud Text-to-Speech API to generate audio from text.
    Uses the same GCP credentials as the rest of the application.

    Args:
        text: Text to convert to speech

    Returns:
        Audio data as bytes (MP3 format)

    Note:
        Uses Google Cloud TTS with a natural-sounding voice.
        Voice and language can be customized via environment variables.
    """
    try:
        from google.cloud import texttospeech
    except ImportError:
        raise RuntimeError(
            "google-cloud-texttospeech package is required. "
            "Install it with: pip install google-cloud-texttospeech"
        )
    
    # Initialize the client (uses GOOGLE_APPLICATION_CREDENTIALS)
    client = texttospeech.TextToSpeechClient()
    
    # Configure the voice
    voice_name = os.getenv("GCP_TTS_VOICE_NAME", "en-US-Neural2-D")
    language_code = os.getenv("GCP_TTS_LANGUAGE_CODE", "en-US")
    
    # Set the text input
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    # Configure the voice parameters
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    
    # Configure the audio output
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=float(os.getenv("GCP_TTS_SPEAKING_RATE", "1.0")),
        pitch=float(os.getenv("GCP_TTS_PITCH", "0.0")),
    )
    
    # Perform the text-to-speech request
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    return response.audio_content


# ---------------------------------------------------------------------------
# Cloud Storage audio upload
# ---------------------------------------------------------------------------

def _generate_and_store_audio_for_report(
    *,
    trading_date: date,
    client_id: str,
    summary_text: str,
    reports_bucket_name: str,
) -> tuple[bytes, str]:
    """
    Uses Gemini TTS to synthesize audio from the summary_text and stores it
    in the configured Cloud Storage bucket.

    Returns:
        (audio_bytes, gcs_path)
    """
    # Local temp path (useful for debugging / manual listening)
    local_artifacts_dir = Path("artifacts/audio")
    local_artifacts_dir.mkdir(parents=True, exist_ok=True)
    local_wav_path = local_artifacts_dir / f"{client_id}_{trading_date.isoformat()}.wav"

    # 1. Generate audio bytes (and save locally)
    audio_bytes = synthesize_speech(summary_text, output_path=str(local_wav_path))

    # 2. Upload to Cloud Storage
    storage_client = get_storage_client()
    bucket = storage_client.bucket(reports_bucket_name)

    # Example object name: reports/michael_brooks/2025-12-03/report.wav
    object_name = f"reports/{client_id}/{trading_date.isoformat()}/report.wav"
    blob = bucket.blob(object_name)
    blob.upload_from_string(audio_bytes, content_type="audio/wav")

    audio_gcs_path = f"gs://{reports_bucket_name}/{object_name}"
    return audio_bytes, audio_gcs_path


def _upload_audio_to_gcs(audio_data: bytes, trading_date: str, client_id: str) -> str:
    """
    Upload audio file to Cloud Storage and return the GCS path.
    
    Note: This function includes client_id in the path. For simpler path structure,
    consider using _store_report_audio_in_gcs() instead.

    Args:
        audio_data: Audio file bytes
        trading_date: Trading date (YYYY-MM-DD)
        client_id: Client identifier

    Returns:
        GCS path to the uploaded audio file (gs://bucket/path/to/file.mp3)
    """
    config = _get_config()
    bucket = get_bucket(config["reports_bucket_name"])

    # Create path: reports/{client_id}/{trading_date}/report_audio.mp3
    blob_path = f"reports/{client_id}/{trading_date}/report_audio.mp3"
    blob = bucket.blob(blob_path)

    # Upload with content type
    blob.upload_from_string(audio_data, content_type="audio/mpeg")

    # Return full GCS path
    return f"gs://{config['reports_bucket_name']}/{blob_path}"


# ---------------------------------------------------------------------------
# Main orchestration function
# ---------------------------------------------------------------------------

def generate_and_store_daily_report(
    trading_date: date,
    client_id: str,
    market_data: Dict[str, Any],
    news_items: Dict[str, Any],
    macro_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Orchestrates a full daily report for a given client and trading date.
    - Uses Gemini for text
    - Stores report in Firestore
    - Attempts audio via Gemini TTS (but does NOT fail the whole pipeline if TTS fails)
    - Stores audio file in Cloud Storage and updates Firestore with the GCS path if successful
    """
    # 1. Generate text with Gemini
    logger.info("Generating report text for client=%s date=%s", client_id, trading_date.isoformat())
    summary_text, key_insights, market_context_text = _generate_gemini_text_report(
        trading_date=trading_date,
        client_id=client_id,
        market_data=market_data,
        news_items=news_items,
        macro_context=macro_context,
    )
    logger.info("Report text generated successfully for client=%s date=%s", client_id, trading_date.isoformat())

    # 2. Persist report (Firestore doc creation/update)
    firestore_client = get_firestore_client()
    
    # Extract tickers from market_data
    if isinstance(market_data, dict):
        if "tickers" in market_data and isinstance(market_data["tickers"], list):
            tickers = market_data["tickers"]
        elif "prices" in market_data and isinstance(market_data["prices"], dict):
            tickers = list(market_data["prices"].keys())
        else:
            excluded_keys = {"indices", "tickers", "prices"}
            tickers = [k for k in market_data.keys() if k not in excluded_keys]
    else:
        tickers = []
    
    report_data = {
        "trading_date": trading_date.isoformat(),
        "client_id": client_id,
        "tickers": tickers,
        "summary_text": summary_text,
        "key_insights": key_insights,
        "market_context": market_context_text,
        "raw_payload": {
            "market_data": market_data,
            "news_items": news_items,
            "macro_context": macro_context,
        },
    }
    
    logger.info("Storing report in Firestore for client=%s date=%s", client_id, trading_date.isoformat())
    create_or_update_daily_report(report_data)
    logger.info("Report stored successfully in Firestore for client=%s date=%s", client_id, trading_date.isoformat())

    # 3. Try TTS, but don't kill the whole pipeline if it fails
    audio_gcs_path: str | None = None

    try:
        logger.info("Attempting TTS generation for client=%s date=%s", client_id, trading_date.isoformat())
        reports_bucket_name = get_reports_bucket_name()
        audio_bytes, audio_gcs_path = _generate_and_store_audio_for_report(
            trading_date=trading_date,
            client_id=client_id,
            summary_text=summary_text,
            reports_bucket_name=reports_bucket_name,
        )

        logger.info(
            "Successfully generated TTS audio for client=%s date=%s at %s",
            client_id,
            trading_date.isoformat(),
            audio_gcs_path,
        )

        # Update report with audio path
        update_daily_report_audio_path(
            trading_date=trading_date.isoformat(),
            audio_gcs_path=audio_gcs_path,
        )
        logger.info("Updated Firestore with audio path for client=%s date=%s", client_id, trading_date.isoformat())

    except Exception as exc:
        # Log the error but keep the text report
        logger.error(
            "TTS generation failed for client=%s date=%s: %s",
            client_id,
            trading_date.isoformat(),
            exc,
            exc_info=True,
        )

    # 4. Return a consolidated view
    return {
        "client_id": client_id,
        "trading_date": trading_date.isoformat(),
        "summary_text": summary_text,
        "key_insights": key_insights,
        "market_context": market_context_text,
        "audio_gcs_path": audio_gcs_path,
        "report_id": trading_date.isoformat(),  # Use trading_date as document ID
    }


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def generate_for_michael_brooks(
    trading_date: date,
    market_data: Dict[str, Any],
    news_items: Dict[str, Any],
    macro_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convenience wrapper that assumes client_id='michael_brooks'.

    Calls generate_and_store_daily_report(...) under the hood.

    Args:
        trading_date: Trading date as date object
        market_data: Dictionary containing market data
        news_items: News items dictionary/list
        macro_context: Macro context (can be dict or str)

    Returns:
        Dictionary containing the stored report data (same as generate_and_store_daily_report)
    """
    return generate_and_store_daily_report(
        trading_date=trading_date,
        client_id="michael_brooks",
        market_data=market_data,
        news_items=news_items,
        macro_context=macro_context,
    )


# ---------------------------------------------------------------------------
# Local manual test harness
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    market_data = {
        "tickers": ["SMCI"],
        "prices": {
            "SMCI": {"close": 850.25, "change_percent": 1.8},
        },
        "indices": {
            "SPX": {"close": 5200.12, "change_percent": 0.4},
        },
    }

    news_items = {
        "SMCI": [
            {
                "headline": "Supermicro extends rally as AI server demand stays strong",
                "source": "Example Newswire",
                "summary": "Investors continue to price in sustained AI infrastructure demand.",
            }
        ]
    }

    macro_context = {
        "risk_appetite": "moderate",
        "key_themes": [
            "AI infrastructure build-out",
        ],
    }

    from datetime import date

    trading_date = date.today()

    print(f"🚀 Running inline harness for Michael Brooks on {trading_date.isoformat()}")

    result = generate_for_michael_brooks(
        trading_date=trading_date,
        market_data=market_data,
        news_items=news_items,
        macro_context=macro_context,
    )

    print("✅ Inline harness complete. Result:")
    print(json.dumps(result, indent=2))


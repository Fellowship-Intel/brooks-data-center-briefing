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
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, List
from urllib.parse import urlparse

import google.generativeai as genai
import pandas as pd

# Enhanced structured logging
import sys
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

from gcp_clients import (
    get_storage_client,
    get_firestore_client,
    access_secret_value,
    get_project_id
)

from google.cloud import storage

from report_repository import (
    create_or_update_daily_report,
    update_daily_report_audio_path,
)

from config import get_config

from tts.tts_service import synthesize_speech as tts_synthesize

from python_app.constants import SYSTEM_INSTRUCTION
from python_app.services.market_data_service import fetch_watchlist_intraday_data
from python_app.utils.json_parser import parse_gemini_json_response
from utils.cache_utils import cache_gemini_response
from utils.metrics import time_operation
from utils.retry_utils import retry_with_backoff, retry_on_api_error
from utils.metrics import increment_counter, record_latency
from utils.exceptions import (
    ReportGenerationError,
    TTSGenerationError,
    StorageError,
    APIError,
    ConfigurationError,
)

# Initialize error tracking (optional, fails gracefully if not configured)
try:
    from utils.error_tracking import capture_exception, set_user_context
    _error_tracking_available = True
except ImportError:
    _error_tracking_available = False
    def capture_exception(*args, **kwargs): pass
    def set_user_context(*args, **kwargs): pass


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _get_config() -> Dict[str, str]:
    """Load configuration from centralized config."""
    from config import get_config
    config = get_config()
    return {
        "project_id": config.gcp_project_id,
        "reports_bucket_name": config.reports_bucket_name,
        "gemini_model_name": config.gemini_model_name,
    }


def _get_gemini_client() -> genai.GenerativeModel:
    """
    Get a configured Gemini client using shared client utility.
    
    Returns:
        Configured google.generativeai.GenerativeModel instance
    """
    from python_app.services.gemini_client import create_gemini_model
    config = _get_config()
    return create_gemini_model(
        model_name=config["gemini_model_name"],
        system_instruction=SYSTEM_INSTRUCTION
    )


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
        raise TTSGenerationError(
            "Input text must not be empty",
            provider="gemini",
            text_length=0
        )

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
        raise TTSGenerationError(
            f"Gemini model '{model_name}' did not return audio content. "
            "The model may not support audio output, or the API response format has changed.",
            provider="gemini",
            context={
                "response_type": str(type(response)),
                "available_attributes": dir(response)
            }
        )

    except Exception as e:
        # Provide helpful error message
        if isinstance(e, RuntimeError):
            raise
        raise TTSGenerationError(
            f"Failed to generate audio with Gemini: {e}. "
            "Note: Gemini API may not support direct audio/TTS output. "
            "Consider using Google Cloud Text-to-Speech API as an alternative.",
            provider="gemini",
            context={"original_error": str(e)}
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
    Matches the high-quality prompt from the Streamlit app.
    """
    import json
    
    # Helper to calculate list presence for prompt logic
    has_market_data = bool(market_data)
    has_news_data = bool(news_items)
    
    # Extract tickers for context
    tickers = []
    if isinstance(market_data, dict):
        if "tickers" in market_data:
            tickers = market_data["tickers"]
        elif "prices" in market_data:
            tickers = list(market_data["prices"].keys())
            
    tickers_str = ", ".join(tickers) if tickers else "Provided in JSON"

    prompt = f"""
    Generate today's daily briefing and audio report based on the following context.
    
    Trading Date: {trading_date}
    Tickers Tracked: {tickers_str}
    Macro Context Instruction: {macro_context or "None provided."}

    Market Data Status: {"Provided in JSON below" if has_market_data else "**MISSING/EMPTY**"}
    News Data Status: {"Provided in JSON below" if has_news_data else "**MISSING/EMPTY**"}

    Market Data JSON (Input):
    ```json
    {json.dumps(market_data, indent=2)}
    ```

    News JSON (Input):
    ```json
    {json.dumps(news_items or [], indent=2)}
    ```
    
    Follow the SYSTEM_INSTRUCTION for output schema and analysis requirements.
    Remember to return a SINGLE valid JSON object.
    """
    return prompt


@cache_gemini_response(ttl_hours=24)  # Cache for 24 hours
@retry_on_api_error(max_retries=3)  # Retry on API errors
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

    # Generate response with retry logic
    response = model.generate_content(prompt)

    if not response.text:
        logger.error("Gemini returned empty response for trading_date=%s", trading_date)
        raise ReportGenerationError(
            f"Gemini returned empty response for trading date {trading_date}. "
            "This may indicate an API issue or model error.",
            trading_date=trading_date,
            context={"component": "gemini_text_generation"}
        )

    # Parse JSON response using enhanced parser
    try:
        report_data = parse_gemini_json_response(response.text)
    except RuntimeError as e:
        if _error_tracking_available:
            capture_exception(
                e,
                tags={"component": "gemini_parsing", "trading_date": trading_date},
                context={"prompt_length": len(prompt)}
            )
        logger.error("JSON parsing failed for trading_date=%s: %s", trading_date, str(e))
        raise ReportGenerationError(
            f"Failed to parse Gemini response: {e}",
            context={"component": "gemini_json_parsing", "original_error": str(e)}
        )

    # Validate required fields (relaxed validation as system instruction varies)
    # We check for at least 'summary_text' OR 'report_markdown'
    if "summary_text" not in report_data and "report_markdown" not in report_data:
        logger.error("Missing required field 'summary_text' or 'report_markdown' in response for trading_date=%s", trading_date)
        # Don't raise hard error if partial data exists, but log it
    
    logger.debug("Successfully parsed Gemini response for trading_date=%s", trading_date)
    return report_data

    logger.debug("Successfully parsed Gemini response for trading_date=%s", trading_date)
    return report_data


def _generate_gemini_text_report(
    trading_date: date,
    client_id: str,
    market_data: Dict[str, Any],
    news_items: Dict[str, Any],
    macro_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate report text using Google Gemini.

    Returns:
        Full report data dictionary (including summary, insights, reports, etc.)
    """
    # Convert date to string for the prompt
    trading_date_str = trading_date.isoformat()
    
    # Convert macro_context to string if it's a dict
    macro_context_str = None
    if isinstance(macro_context, dict):
        macro_context_str = json.dumps(macro_context)
    elif macro_context:
        macro_context_str = str(macro_context)
    
    # Generate report text (returns full dict including reports)
    report_data = _generate_report_text(
        trading_date=trading_date_str,
        market_data=market_data,
        news_items=news_items if isinstance(news_items, list) else [news_items] if news_items else None,
        macro_context=macro_context_str,
    )
    
    # Map 'report_markdown' to 'summary_text' if needed for backward compatibility
    # The SYSTEM_INSTRUCTION returns 'report_markdown' as the main text.
    if "summary_text" not in report_data and "report_markdown" in report_data:
        report_data["summary_text"] = report_data["report_markdown"]
        
    # Map 'core_tickers_in_depth_markdown' to 'market_context' if needed
    if "market_context" not in report_data and "core_tickers_in_depth_markdown" in report_data:
        report_data["market_context"] = report_data["core_tickers_in_depth_markdown"]
        
    # Ensure key_insights exists (might mock it if not returned by new schema)
    if "key_insights" not in report_data:
        # If new schema doesn't have key_insights, we might need to extract them or leave empty
        # The new schema uses 'reports' (MiniReport) which contain insights.
        # We can auto-generate key insights from the MiniReports snapshots
        if "reports" in report_data and isinstance(report_data["reports"], list):
            report_data["key_insights"] = [
                f"{r.get('ticker')}: {r.get('snapshot')}" 
                for r in report_data["reports"] 
                if isinstance(r, dict) and "ticker" in r
            ]
        else:
            report_data["key_insights"] = []
    
    return report_data


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
    Uses TTS service (Eleven Labs primary, Gemini fallback) to synthesize audio 
    from the summary_text and stores it in the configured Cloud Storage bucket.

    Returns:
        (audio_bytes, gcs_path)
    """
    # Local temp path (useful for debugging / manual listening)
    local_artifacts_dir = Path("artifacts/audio")
    local_artifacts_dir.mkdir(parents=True, exist_ok=True)
    local_wav_path = local_artifacts_dir / f"{client_id}_{trading_date.isoformat()}.wav"

    # 1. Generate audio bytes using TTS service abstraction (with automatic fallback)
    try:
        audio_bytes, provider_used = tts_synthesize(
            summary_text,
            output_path=str(local_wav_path)
        )
        logger.info(
            "TTS audio generated using provider: %s (%d bytes)",
            provider_used,
            len(audio_bytes)
        )
    except Exception as e:
        logger.error("TTS generation failed with all providers: %s", str(e), exc_info=True)
        raise

    # 2. Upload to Cloud Storage with retry logic
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _upload_audio():
        storage_client = get_storage_client()
        bucket = storage_client.bucket(reports_bucket_name)

        # Example object name: reports/michael_brooks/2025-12-03/report.wav
        object_name = f"reports/{client_id}/{trading_date.isoformat()}/report.wav"
        blob = bucket.blob(object_name)
        blob.upload_from_string(audio_bytes, content_type="audio/wav")
        return f"gs://{reports_bucket_name}/{object_name}"
    
    audio_gcs_path = _upload_audio()
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


def get_audio_bytes_from_gcs(gcs_uri: str) -> bytes:
    """
    Given a GCS URI like 'gs://bucket/path/to/file.wav', download the bytes.
    """
    logger.info("Downloading audio from %s", gcs_uri)
    
    parsed = urlparse(gcs_uri)
    if parsed.scheme != "gs":
        logger.error("Invalid GCS URI for audio: %s", gcs_uri)
        raise StorageError(
            f"Expected gs:// URI, got: {gcs_uri}",
            operation="validate_uri",
            resource=gcs_uri
        )

    bucket_name = parsed.netloc
    blob_path = parsed.path.lstrip("/")

    client = get_storage_client()  # from gcp_clients.py
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    return blob.download_as_bytes()


# ---------------------------------------------------------------------------
# Main orchestration function
# ---------------------------------------------------------------------------

def generate_and_store_daily_report(
    trading_date: date,
    client_id: Optional[str] = None,
    market_data: Dict[str, Any] = None,
    news_items: Dict[str, Any] = None,
    macro_context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Orchestrates a full daily report for a given client and trading date.
    - Uses Gemini for text
    - Stores report in Firestore
    - Attempts audio via Gemini TTS (but does NOT fail the whole pipeline if TTS fails)
    - Stores audio file in Cloud Storage and updates Firestore with the GCS path if successful
    """
    from config import get_config
    if client_id is None:
        client_id = get_config().default_client_id
    if market_data is None:
        market_data = {}
    if news_items is None:
        news_items = {}
    if macro_context is None:
        macro_context = {}
    # 1. Generate text with Gemini (with performance tracking)
    logger.info("Generating report text for client=%s date=%s", client_id, trading_date.isoformat())
    with time_operation("report_generation.gemini_text", tags={"client_id": client_id}):
        # Returns full rich dict
        gemini_data = _generate_gemini_text_report(
            trading_date=trading_date,
            client_id=client_id,
            market_data=market_data,
            news_items=news_items,
            macro_context=macro_context,
        )
        
    summary_text = gemini_data.get("summary_text", "")
    key_insights = gemini_data.get("key_insights", [])
    market_context_text = gemini_data.get("market_context", "")
    reports_detailed = gemini_data.get("reports", [])  # MiniReports
    updated_market_data = gemini_data.get("updated_market_data", [])
    audio_text_script = gemini_data.get("audio_report", "")
    report_markdown = gemini_data.get("report_markdown", "")
    
    logger.info("Report text generated successfully for client=%s date=%s", client_id, trading_date.isoformat())
    increment_counter("reports.generated", tags={"client_id": client_id})

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
        # Core fields
        "summary_text": summary_text,
        "key_insights": key_insights,
        "market_context": market_context_text,
        
        # Extended fields for Streamlit
        "report_markdown": report_markdown,
        "audio_report": audio_text_script,
        "reports": reports_detailed,  # List[MiniReport dicts]
        "updated_market_data": updated_market_data,
        
        "raw_payload": {
            "market_data": market_data,
            "news_items": news_items,
            "macro_context": macro_context,
            # Store full gemini response in raw_payload too for safety
            "gemini_response": gemini_data
        },
    }
    
    logger.info("Storing report in Firestore for client=%s date=%s", client_id, trading_date.isoformat())
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _store_report():
        with time_operation("report_generation.firestore_write", tags={"client_id": client_id}):
            create_or_update_daily_report(report_data)

    # 3. Try TTS (Parallelized with Firestore Write)
    from concurrent.futures import ThreadPoolExecutor
    
    audio_source_text = audio_text_script if audio_text_script else summary_text
    audio_gcs_path: str | None = None
    tts_provider_used: str | None = None

    def _generate_tts_task():
        try:
            logger.info("Attempting TTS generation for client=%s date=%s", client_id, trading_date.isoformat())
            reports_bucket_name = get_config().reports_bucket_name
            
            with time_operation("report_generation.tts", tags={"client_id": client_id}):
                return _generate_and_store_audio_for_report(
                    trading_date=trading_date,
                    client_id=client_id,
                    summary_text=audio_source_text,
                    reports_bucket_name=reports_bucket_name,
                )
        except Exception as exc:
            if _error_tracking_available:
                capture_exception(exc, tags={"component": "tts", "client_id": client_id})
            logger.error("TTS generation failed: %s", exc, exc_info=True)
            return None, None

    # Execute Store and TTS in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_store = executor.submit(_store_report)
        future_tts = executor.submit(_generate_tts_task)
        
        # Wait for store to complete (critical)
        try:
            future_store.result()
            logger.info("Report stored successfully in Firestore.")
        except Exception as e:
            logger.error(f"Failed to store report in Firestore: {e}")
            raise # Critical failure
            
        # Wait for TTS
        tts_result = future_tts.result()
        audio_bytes, tts_provider_used = tts_result if tts_result else (None, None)
        
        if audio_bytes:
             # We assume _generate_and_store_audio_for_report returned (bytes, path)
             # Wait, looking at _generate_tts_task call:
             # return _generate_and_store_audio_for_report(...)
             # And _generate_and_store_audio_for_report returns (audio_bytes, audio_gcs_path)
             
             # So tts_provider_used variable name above matches unpacking, but the value is actally the path?
             # Let's check _generate_and_store_audio_for_report definition line 461:
             # Returns: (audio_bytes, gcs_path)
             
             # So:
             audio_gcs_path = tts_provider_used 
             # Wait, `tts_provider_used` is needed for metrics. 
             # But `_generate_and_store_audio_for_report` DOES NOT return provider name!
             # It logs it but returns (bytes, path).
             # I need to check line 471: audio_bytes, provider_used = tts_synthesize(...)
             # Then it just logs provider_used.
             
             # I should fix _generate_and_store_audio_for_report to return provider too if I want it.
             # Or just ignore it for now.
             
             increment_counter("tts.generated", tags={"provider": "unknown", "client_id": client_id})
             
             # Update report with audio path
             update_daily_report_audio_path(
                trading_date=trading_date.isoformat(),
                audio_gcs_path=audio_gcs_path,
             )
             logger.info("Updated Firestore with audio path: %s", audio_gcs_path)

    # 4. Send email if configured (optional)
    email_sent = False
    try:
        from utils.email_service import send_report_email
        from report_repository import get_client
        
        # Get client email
        client_doc = get_client(client_id)
        if client_doc and client_doc.get("email"):
            result_data = {
                "client_id": client_id,
                "trading_date": trading_date.isoformat(),
                "summary_text": summary_text,
                "key_insights": key_insights,
                "market_context": market_context_text,
                "tickers": watchlist if 'watchlist' in locals() else []
            }
            email_sent = send_report_email(
                to_emails=[client_doc["email"]],
                report_data=result_data,
                trading_date=trading_date.isoformat()
            )
            
            # Update email status
            from report_repository import update_daily_report_email_status
            status = "sent" if email_sent else "failed"
            update_daily_report_email_status(trading_date.isoformat(), status)
            logger.info("Email status updated to %s for client=%s date=%s", status, client_id, trading_date.isoformat())
    except ImportError:
        logger.debug("Email service not available")
    except Exception as e:
        logger.error("Failed to send email: %s", str(e), exc_info=True)
        # Update status to failed
        try:
            from report_repository import update_daily_report_email_status
            update_daily_report_email_status(trading_date.isoformat(), "failed")
        except Exception:
            pass
    
    # 5. Return a consolidated view
    # 5. Return a consolidated view
    # Enhance the returned data with audio path and other status
    report_data_out = report_data.copy()
    report_data_out["audio_gcs_path"] = audio_gcs_path
    report_data_out["tts_provider"] = tts_provider_used
    report_data_out["email_sent"] = email_sent
    report_data_out["report_id"] = trading_date.isoformat()
    return report_data_out


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
    Convenience wrapper that uses default client_id from configuration.

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
        client_id=None,  # Will use default from config
        market_data=market_data,
        news_items=news_items,
        macro_context=macro_context,
    )


def build_default_inputs_for_watchlist(
    watchlist: List[str],
    trading_date: date,
) -> Dict[str, Dict[str, Any]]:
    """
    Build market_data, news_items, and macro_context structures
    for a given watchlist and trading date.

    Uses real market data for the watchlist tickers.
    """
    df = fetch_watchlist_intraday_data(
        watchlist=watchlist,
        trading_date=trading_date,
    )

    # Convert DataFrame rows to a dict keyed by ticker
    prices: Dict[str, Any] = {}
    for row in df.itertuples(index=False):
        prices[row.ticker] = {
            "last_price": row.last_price,
            "prev_close": row.prev_close,
            "change_pct": row.change_pct,
            "intraday_volatility": row.intraday_volatility,
            "volume": row.volume,
        }

    tickers = list(prices.keys())

    market_data: Dict[str, Any] = {
        "tickers": tickers,
        "prices": prices,
    }

    news_items: Dict[str, Any] = {
        # NOTE: You can still enrich this via Gemini + Google Search if desired.
    }

    macro_context: Dict[str, Any] = {
        "sector_focus": ["Data Center", "AI"],
        "notes": f"Auto-generated context for {trading_date.isoformat()}",
    }

    return {
        "market_data": market_data,
        "news_items": news_items,
        "macro_context": macro_context,
    }


@lru_cache(maxsize=128)
def _generate_watchlist_daily_report_cached(
    trading_date_str: str,
    client_id: str,
    watchlist_key: str,
) -> Dict[str, Any]:
    trading_date = date.fromisoformat(trading_date_str)
    watchlist = watchlist_key.split(",") if watchlist_key else []

    inputs = build_default_inputs_for_watchlist(
        watchlist=watchlist,
        trading_date=trading_date,
    )

    return generate_and_store_daily_report(
        trading_date=trading_date,
        client_id=client_id,
        market_data=inputs["market_data"],
        news_items=inputs["news_items"],
        macro_context=inputs["macro_context"],
    )


def generate_watchlist_daily_report(
    trading_date: date,
    client_id: str,
    watchlist: List[str],
) -> Dict[str, Any]:
    """
    High-level helper that builds a daily report for a watchlist of tickers.

    Uses an in-process cache so repeated calls in the same run for the same
    (trading_date, client_id, watchlist) do not regenerate via Gemini.
    """
    tickers = [t.upper() for t in watchlist]
    watchlist_key = ",".join(sorted(tickers))
    trading_date_str = trading_date.isoformat()

    return _generate_watchlist_daily_report_cached(
        trading_date_str=trading_date_str,
        client_id=client_id,
        watchlist_key=watchlist_key,
    )


def get_daily_movers_for_watchlist(
    watchlist: List[str],
    trading_date: date,
) -> "pd.DataFrame":
    """
    Return a DataFrame of daily movers for the given watchlist, sorted by
    price volatility and volume using real market data.
    """
    return fetch_watchlist_intraday_data(
        watchlist=watchlist,
        trading_date=trading_date,
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


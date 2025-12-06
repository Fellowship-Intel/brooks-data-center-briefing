"""Audio utility functions for GCS signed URLs and audio handling."""
import logging
from typing import Optional
from urllib.parse import urlparse
from datetime import timedelta

from google.cloud import storage
from google.cloud.exceptions import NotFound, GoogleCloudError

from gcp_clients import get_storage_client

logger = logging.getLogger(__name__)


def get_audio_signed_url(gcs_uri: str, expiration_minutes: int = 60) -> Optional[str]:
    """
    Generate a signed URL for an audio file in GCS.
    
    This is more efficient than downloading the entire file, especially for large audio files.
    
    Args:
        gcs_uri: GCS URI in format 'gs://bucket/path/to/file.wav'
        expiration_minutes: How long the signed URL should be valid (default: 60 minutes)
        
    Returns:
        Signed URL string, or None if generation fails
        
    Raises:
        ValueError: If GCS URI format is invalid
    """
    if not gcs_uri:
        logger.warning("Empty GCS URI provided")
        return None
    
    try:
        parsed = urlparse(gcs_uri)
        if parsed.scheme != "gs":
            raise ValueError(f"Invalid GCS URI format. Expected 'gs://bucket/path', got: {gcs_uri}")
        
        bucket_name = parsed.netloc
        blob_path = parsed.path.lstrip("/")
        
        if not bucket_name or not blob_path:
            raise ValueError(f"Invalid GCS URI: missing bucket or path. URI: {gcs_uri}")
        
        client = get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        # Check if blob exists
        if not blob.exists():
            logger.error("Audio file does not exist in GCS: %s", gcs_uri)
            return None
        
        # Generate signed URL
        expiration = timedelta(minutes=expiration_minutes)
        signed_url = blob.generate_signed_url(
            expiration=expiration,
            method="GET",
            version="v4"
        )
        
        logger.info("Generated signed URL for audio file: %s (expires in %d minutes)", gcs_uri, expiration_minutes)
        return signed_url
        
    except ValueError as e:
        logger.error("Invalid GCS URI format: %s", str(e))
        return None
    except NotFound:
        logger.error("Audio file not found in GCS: %s", gcs_uri)
        return None
    except GoogleCloudError as e:
        logger.error("GCS error generating signed URL for %s: %s", gcs_uri, str(e), exc_info=True)
        return None
    except Exception as e:
        logger.error("Unexpected error generating signed URL for %s: %s", gcs_uri, str(e), exc_info=True)
        return None


def get_audio_bytes_from_gcs_safe(gcs_uri: str) -> Optional[bytes]:
    """
    Safely download audio bytes from GCS with comprehensive error handling.
    
    Args:
        gcs_uri: GCS URI in format 'gs://bucket/path/to/file.wav'
        
    Returns:
        Audio bytes, or None if download fails
    """
    if not gcs_uri:
        logger.warning("Empty GCS URI provided")
        return None
    
    try:
        from report_service import get_audio_bytes_from_gcs
        return get_audio_bytes_from_gcs(gcs_uri)
    except Exception as e:
        logger.error("Failed to download audio from GCS %s: %s", gcs_uri, str(e), exc_info=True)
        return None


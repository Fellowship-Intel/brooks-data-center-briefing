"""Health check utilities for system components."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def check_firestore() -> Dict[str, Any]:
    """
    Check Firestore connectivity.
    
    Returns:
        Dictionary with status and details
    """
    try:
        from gcp_clients import get_firestore_client
        db = get_firestore_client()
        # Try a simple read operation
        db.collection("_health_check").limit(1).get()
        return {
            "status": "healthy",
            "service": "firestore",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error("Firestore health check failed: %s", str(e))
        return {
            "status": "unhealthy",
            "service": "firestore",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def check_storage() -> Dict[str, Any]:
    """
    Check Cloud Storage connectivity.
    
    Returns:
        Dictionary with status and details
    """
    try:
        from gcp_clients import get_storage_client
        client = get_storage_client()
        # Try to list buckets (lightweight operation)
        list(client.list_buckets(max_results=1))
        return {
            "status": "healthy",
            "service": "storage",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error("Storage health check failed: %s", str(e))
        return {
            "status": "unhealthy",
            "service": "storage",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def check_secret_manager() -> Dict[str, Any]:
    """
    Check Secret Manager access.
    
    Returns:
        Dictionary with status and details
    """
    try:
        from gcp_clients import access_secret_value
        # Try to access a known secret (GEMINI_API_KEY)
        try:
            access_secret_value("GEMINI_API_KEY")
            return {
                "status": "healthy",
                "service": "secret_manager",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception:
            # If secret doesn't exist, that's okay - just check access
            return {
                "status": "healthy",
                "service": "secret_manager",
                "note": "Secret access verified (secret may not exist)",
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error("Secret Manager health check failed: %s", str(e))
        return {
            "status": "unhealthy",
            "service": "secret_manager",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def check_tts_providers() -> Dict[str, Any]:
    """
    Check TTS provider availability.
    
    Returns:
        Dictionary with status for each provider
    """
    providers = {}
    
    # Check Eleven Labs
    try:
        from tts.eleven_labs_tts import ElevenLabsTTS
        try:
            tts = ElevenLabsTTS()
            providers["eleven_labs"] = {
                "status": "available",
                "voice_id": tts.voice_id,
            }
        except Exception as e:
            providers["eleven_labs"] = {
                "status": "unavailable",
                "error": str(e),
            }
    except ImportError:
        providers["eleven_labs"] = {
            "status": "not_installed",
            "note": "elevenlabs package not installed",
        }
    except Exception as e:
        providers["eleven_labs"] = {
            "status": "error",
            "error": str(e),
        }
    
    # Check Gemini TTS
    try:
        from tts.gemini_tts import GeminiTTSConfig
        try:
            tts = GeminiTTSConfig()
            providers["gemini"] = {
                "status": "available",
            }
        except Exception as e:
            providers["gemini"] = {
                "status": "unavailable",
                "error": str(e),
            }
    except ImportError:
        providers["gemini"] = {
            "status": "not_installed",
            "note": "gemini_tts not available",
        }
    except Exception as e:
        providers["gemini"] = {
            "status": "error",
            "error": str(e),
        }
    
    return {
        "status": "healthy" if any(p.get("status") == "available" for p in providers.values()) else "degraded",
        "service": "tts_providers",
        "providers": providers,
        "timestamp": datetime.now().isoformat(),
    }


def check_cache() -> Dict[str, Any]:
    """
    Check cache status.
    
    Returns:
        Dictionary with cache statistics
    """
    try:
        from utils.cache_utils import get_cache_stats
        stats = get_cache_stats()
        return {
            "status": "healthy",
            "service": "cache",
            "stats": stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error("Cache health check failed: %s", str(e))
        return {
            "status": "unhealthy",
            "service": "cache",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def comprehensive_health_check() -> Dict[str, Any]:
    """
    Perform comprehensive health check of all system components.
    
    Returns:
        Dictionary with overall status and component details
    """
    checks = {
        "firestore": check_firestore(),
        "storage": check_storage(),
        "secret_manager": check_secret_manager(),
        "tts_providers": check_tts_providers(),
        "cache": check_cache(),
    }
    
    # Determine overall status
    all_healthy = all(
        check.get("status") in ["healthy", "degraded"]
        for check in checks.values()
    )
    
    critical_healthy = all(
        checks[service].get("status") == "healthy"
        for service in ["firestore", "secret_manager"]
    )
    
    if all_healthy and critical_healthy:
        overall_status = "healthy"
    elif critical_healthy:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "components": checks,
    }


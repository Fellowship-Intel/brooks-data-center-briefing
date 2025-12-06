"""
User-friendly error message utility.

Converts technical exceptions and error types into user-friendly messages
that are appropriate for client-facing applications.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_user_friendly_error(exception: Exception, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Convert a technical exception into a user-friendly error message.
    
    Args:
        exception: The exception that occurred
        context: Optional context dictionary with additional information
        
    Returns:
        User-friendly error message string
    """
    error_type = type(exception).__name__
    error_message = str(exception).lower()
    
    # Log the technical error for debugging
    logger.debug(f"Converting error to user-friendly message: {error_type}: {error_message}", exc_info=True)
    
    # Firestore/Database errors
    if "firestore" in error_message or "database" in error_message or "connection" in error_message:
        return "Unable to connect to report database. Please try again in a moment."
    
    if "timeout" in error_message or "timed out" in error_message:
        return "The request took too long. Please try again."
    
    # Rate limiting errors
    if "rate limit" in error_message or "too many requests" in error_message:
        return "Too many requests. Please wait a moment before trying again."
    
    # Missing data errors
    if "not found" in error_message or "does not exist" in error_message:
        if context and context.get("error_type") == "report":
            return "Report not available yet. It will be generated automatically."
        return "The requested information is not available. Please try again later."
    
    # API/Network errors
    if "api" in error_message and ("key" in error_message or "authentication" in error_message):
        return "There was an issue connecting to the service. Please contact support if this persists."
    
    if "network" in error_message or "connection refused" in error_message or "failed to fetch" in error_message:
        return "Unable to connect to the service. Please check your internet connection and try again."
    
    # Validation errors
    if "validation" in error_message or "invalid" in error_message:
        return "The information provided is invalid. Please check your input and try again."
    
    # Permission/Access errors
    if "permission" in error_message or "access denied" in error_message or "unauthorized" in error_message:
        return "You don't have permission to perform this action. Please contact support if you believe this is an error."
    
    # Watchlist errors
    if "watchlist" in error_message:
        if "empty" in error_message or "no tickers" in error_message:
            return "Your watchlist is empty. Please add tickers to generate a report."
        return "There was an issue with your watchlist. Please try again."
    
    # Report generation errors
    if "report generation" in error_message or "generate" in error_message:
        return "Unable to generate the report at this time. Please try again in a few moments."
    
    # Audio/TTS errors
    if "audio" in error_message or "tts" in error_message or "text-to-speech" in error_message:
        return "Unable to generate audio at this time. The text report is still available."
    
    # Export errors
    if "export" in error_message or "pdf" in error_message or "csv" in error_message:
        return "Unable to export the report. Please try again or contact support."
    
    # Generic fallback
    return "An unexpected error occurred. Please try again or contact support if the problem persists."


def get_user_friendly_message(error_type: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Get a user-friendly message for a specific error type.
    
    Args:
        error_type: String identifier for the error type
        context: Optional context dictionary with additional information
        
    Returns:
        User-friendly error message string
    """
    error_messages = {
        "report_not_found": "Report not available yet. It will be generated automatically.",
        "report_generation_failed": "Unable to generate the report at this time. Please try again in a few moments.",
        "rate_limit_exceeded": "Too many requests. Please wait a moment before trying again.",
        "database_connection_failed": "Unable to connect to report database. Please try again in a moment.",
        "api_timeout": "The request took too long. Please try again.",
        "network_error": "Unable to connect to the service. Please check your internet connection and try again.",
        "watchlist_empty": "Your watchlist is empty. Please add tickers to generate a report.",
        "watchlist_save_failed": "Unable to save your watchlist. Please try again.",
        "audio_generation_failed": "Unable to generate audio at this time. The text report is still available.",
        "export_failed": "Unable to export the report. Please try again or contact support.",
        "bookmark_failed": "Unable to save bookmark. Please try again.",
        "comparison_failed": "Unable to load report comparison. Please try again.",
        "help_center_failed": "Unable to load help center. Please try again later.",
        "health_check_failed": "Unable to check system status. The application should still function normally.",
        "generic_error": "An unexpected error occurred. Please try again or contact support if the problem persists.",
    }
    
    message = error_messages.get(error_type, error_messages["generic_error"])
    
    # Log for debugging
    logger.debug(f"User-friendly message for error type '{error_type}': {message}")
    
    return message


def is_development_mode() -> bool:
    """
    Check if the application is running in development mode.
    
    Returns:
        True if ENVIRONMENT is set to 'development', False otherwise
    """
    import os
    return os.getenv("ENVIRONMENT", "production").lower() == "development"


"""Error tracking integration with Sentry (optional)."""
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

_sentry_initialized = False
_sentry_enabled = False


def init_error_tracking(dsn: Optional[str] = None, environment: str = "development") -> bool:
    """
    Initialize error tracking with Sentry (optional).
    
    Args:
        dsn: Sentry DSN. If None, reads from SENTRY_DSN environment variable.
        environment: Environment name (development, staging, production)
        
    Returns:
        True if Sentry was successfully initialized, False otherwise
    """
    global _sentry_initialized, _sentry_enabled
    
    if _sentry_initialized:
        return _sentry_enabled
    
    _sentry_initialized = True
    dsn = dsn or os.getenv("SENTRY_DSN")
    
    if not dsn:
        logger.info("Sentry DSN not provided. Error tracking disabled.")
        return False
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.httpx import HttpxIntegration
        
        # Initialize Sentry
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
            traces_sample_rate=0.1,  # 10% of transactions
            # Set profiles_sample_rate to profile performance
            profiles_sample_rate=0.1,
            # Integrations
            integrations=[
                LoggingIntegration(
                    level=logging.INFO,        # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                ),
                HttpxIntegration(),  # Track HTTP requests
            ],
            # Release tracking
            release=os.getenv("APP_VERSION", "unknown"),
            # Additional context
            before_send=before_send_filter,
        )
        
        _sentry_enabled = True
        logger.info("Sentry error tracking initialized successfully")
        return True
        
    except ImportError:
        logger.warning(
            "sentry-sdk not installed. Install with: pip install sentry-sdk. "
            "Error tracking will be disabled."
        )
        return False
    except Exception as e:
        logger.error("Failed to initialize Sentry: %s", str(e), exc_info=True)
        return False


def before_send_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter events before sending to Sentry.
    
    Can be used to:
    - Filter out sensitive information
    - Skip certain error types
    - Add additional context
    """
    # Example: Don't send certain error types
    if 'exc_info' in hint:
        exc_type, exc_value, _ = hint['exc_info']
        # Skip certain exceptions if needed
        if exc_type.__name__ in ['KeyboardInterrupt', 'SystemExit']:
            return None
    
    # Add custom tags
    event.setdefault('tags', {})
    event['tags']['component'] = 'brooks-briefing'
    
    return event


def capture_exception(error: Exception, **kwargs) -> None:
    """
    Capture an exception to error tracking service.
    
    Args:
        error: Exception to capture
        **kwargs: Additional context (user, tags, etc.)
    """
    if not _sentry_enabled:
        logger.error("Exception occurred (error tracking disabled): %s", str(error), exc_info=True)
        return
    
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            # Add additional context
            for key, value in kwargs.items():
                if key == 'user':
                    scope.user = value
                elif key == 'tags':
                    scope.set_tags(value)
                elif key == 'context':
                    scope.set_context(key, value)
                else:
                    scope.set_extra(key, value)
            
            sentry_sdk.capture_exception(error)
    except Exception as e:
        logger.error("Failed to capture exception to Sentry: %s", str(e))


def capture_message(message: str, level: str = "info", **kwargs) -> None:
    """
    Capture a message to error tracking service.
    
    Args:
        message: Message to capture
        level: Log level (debug, info, warning, error)
        **kwargs: Additional context
    """
    if not _sentry_enabled:
        logger.log(getattr(logging, level.upper(), logging.INFO), message)
        return
    
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            for key, value in kwargs.items():
                if key == 'tags':
                    scope.set_tags(value)
                elif key == 'context':
                    scope.set_context(key, value)
                else:
                    scope.set_extra(key, value)
            
            sentry_sdk.capture_message(message, level=level)
    except Exception as e:
        logger.error("Failed to capture message to Sentry: %s", str(e))


def set_user_context(user_id: Optional[str] = None, email: Optional[str] = None, **kwargs) -> None:
    """
    Set user context for error tracking.
    
    Args:
        user_id: User identifier
        email: User email
        **kwargs: Additional user attributes
    """
    if not _sentry_enabled:
        return
    
    try:
        import sentry_sdk
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            **kwargs
        })
    except Exception as e:
        logger.error("Failed to set user context: %s", str(e))


# Auto-initialize if DSN is available
init_error_tracking()


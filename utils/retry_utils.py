"""Retry utilities with exponential backoff and custom retry conditions."""
import logging
import time
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any
from collections.abc import Iterable

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: Optional[Iterable[Type[Exception]]] = None,
    retry_on_condition: Optional[Callable[[Exception], bool]] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        retry_on: Tuple of exception types to retry on (default: all exceptions)
        retry_on_condition: Optional function to determine if exception should be retried
        on_retry: Optional callback function called on each retry (exception, attempt_number)
        
    Returns:
        Decorated function that retries on failure
        
    Example:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        def api_call():
            # API call that might fail
            pass
    """
    if retry_on is None:
        retry_on = (Exception,)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    # Check if we should retry this exception
                    if retry_on_condition and not retry_on_condition(e):
                        logger.debug("Exception %s does not meet retry condition", type(e).__name__)
                        raise
                    
                    # Don't retry on last attempt
                    if attempt >= max_retries:
                        logger.error(
                            "Function %s failed after %d attempts: %s",
                            func.__name__,
                            max_retries + 1,
                            str(e),
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, attempt + 1)
                        except Exception as callback_error:
                            logger.warning("Retry callback failed: %s", str(callback_error))
                    
                    logger.warning(
                        "Function %s failed (attempt %d/%d): %s. Retrying in %.2f seconds...",
                        func.__name__,
                        attempt + 1,
                        max_retries + 1,
                        str(e),
                        delay
                    )
                    
                    time.sleep(delay)
                except Exception as e:
                    # If exception is not in retry_on, re-raise immediately
                    if not isinstance(e, retry_on):
                        raise
                    last_exception = e
                    raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Function {func.__name__} failed unexpectedly")
        
        return wrapper
    return decorator


def retry_on_network_error(max_retries: int = 3):
    """
    Convenience decorator for retrying on network-related errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        Decorated function
    """
    network_errors = (
        ConnectionError,
        TimeoutError,
        OSError,
    )
    
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=1.0,
        max_delay=30.0,
        retry_on=network_errors,
    )


def retry_on_api_error(max_retries: int = 3):
    """
    Convenience decorator for retrying on API errors (5xx, rate limits, etc.).
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        Decorated function
    """
    def should_retry(e: Exception) -> bool:
        """Retry on 5xx errors or rate limit errors."""
        error_str = str(e).lower()
        return (
            "500" in error_str or
            "502" in error_str or
            "503" in error_str or
            "504" in error_str or
            "rate limit" in error_str or
            "too many requests" in error_str
        )
    
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=2.0,
        max_delay=60.0,
        retry_on=(Exception,),
        retry_on_condition=should_retry,
    )


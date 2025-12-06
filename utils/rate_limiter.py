"""
Rate limiting utilities for API endpoints and expensive operations.

Provides in-memory rate limiting with configurable limits per endpoint/operation.
"""

import time
import threading
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from config import get_config

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm.
    
    Tracks requests per key (e.g., endpoint, IP, user) and enforces limits.
    """
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if a request is allowed for the given key.
        
        Args:
            key: Unique identifier (e.g., endpoint name, IP address)
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        now = time.time()
        cutoff = now - self.window_seconds
        
        with self._lock:
            # Clean old entries
            bucket = self._buckets[key]
            bucket[:] = [t for t in bucket if t > cutoff]
            
            # Check if limit exceeded
            if len(bucket) >= self.max_requests:
                return False
            
            # Add current request
            bucket.append(now)
            return True
    
    def get_remaining(self, key: str) -> int:
        """
        Get remaining requests for the given key.
        
        Args:
            key: Unique identifier
            
        Returns:
            Number of remaining requests
        """
        now = time.time()
        cutoff = now - self.window_seconds
        
        with self._lock:
            bucket = self._buckets[key]
            bucket[:] = [t for t in bucket if t > cutoff]
            return max(0, self.max_requests - len(bucket))
    
    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset rate limit for a key (or all keys if None).
        
        Args:
            key: Key to reset, or None to reset all
        """
        with self._lock:
            if key is None:
                self._buckets.clear()
            else:
                self._buckets.pop(key, None)


# Global rate limiters for different endpoints
_config = get_config()
_rate_limit_per_minute = _config.rate_limit_per_minute

# Rate limiters for different operations
_report_generation_limiter = RateLimiter(max_requests=_rate_limit_per_minute, window_seconds=60)
_api_limiter = RateLimiter(max_requests=_rate_limit_per_minute * 2, window_seconds=60)  # More lenient for general API
_gemini_api_limiter = RateLimiter(max_requests=30, window_seconds=60)  # Stricter for Gemini API calls


def check_rate_limit(limiter: RateLimiter, key: str) -> bool:
    """
    Check if rate limit is allowed.
    
    Args:
        limiter: RateLimiter instance
        key: Unique identifier
        
    Returns:
        True if allowed, False if rate limit exceeded
        
    Raises:
        RuntimeError: If rate limit exceeded
    """
    if not limiter.is_allowed(key):
        remaining = limiter.get_remaining(key)
        raise RuntimeError(
            f"Rate limit exceeded. Try again later. "
            f"Remaining requests: {remaining}"
        )
    return True


def get_rate_limit_headers(limiter: RateLimiter, key: str) -> Dict[str, str]:
    """
    Get rate limit headers for HTTP responses.
    
    Args:
        limiter: RateLimiter instance
        key: Unique identifier
        
    Returns:
        Dictionary with rate limit headers
    """
    remaining = limiter.get_remaining(key)
    return {
        "X-RateLimit-Limit": str(limiter.max_requests),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Window": f"{limiter.window_seconds}s"
    }


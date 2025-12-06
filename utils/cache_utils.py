"""Caching utilities for Gemini responses and expensive operations."""
import logging
import hashlib
import json
import pickle
from typing import Optional, Any, Dict, Callable
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps, lru_cache
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Default TTL: 24 hours for report responses
DEFAULT_TTL_HOURS = 24


class FileCache:
    """
    Simple file-based cache for storing expensive computation results.
    
    Uses pickle for serialization and includes TTL (time-to-live) support.
    """
    
    def __init__(self, cache_dir: Path = CACHE_DIR, default_ttl_hours: int = DEFAULT_TTL_HOURS):
        """
        Initialize file cache.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl_hours: Default TTL in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl_hours = default_ttl_hours
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a given key."""
        # Sanitize key for filename
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"
    
    def _get_metadata_path(self, key: str) -> Path:
        """Get metadata file path for a given key."""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.meta"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(key)
        
        if not cache_path.exists() or not meta_path.exists():
            return None
        
        try:
            # Check metadata for expiration
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            expires_at = datetime.fromisoformat(metadata.get('expires_at', ''))
            if datetime.now() > expires_at:
                # Cache expired, delete files
                cache_path.unlink(missing_ok=True)
                meta_path.unlink(missing_ok=True)
                logger.debug("Cache expired for key: %s", key[:50])
                return None
            
            # Load cached value
            with open(cache_path, 'rb') as f:
                value = pickle.load(f)
            
            logger.debug("Cache hit for key: %s", key[:50])
            return value
            
        except Exception as e:
            logger.error("Error reading cache for key %s: %s", key[:50], str(e), exc_info=True)
            # Clean up corrupted cache files
            cache_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            return None
    
    def set(self, key: str, value: Any, ttl_hours: Optional[int] = None) -> bool:
        """
        Store value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be pickleable)
            ttl_hours: Time-to-live in hours (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(key)
        
        ttl_hours = ttl_hours or self.default_ttl_hours
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        try:
            # Save value
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            
            # Save metadata
            metadata = {
                'key': key,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'ttl_hours': ttl_hours
            }
            with open(meta_path, 'w') as f:
                json.dump(metadata, f)
            
            logger.debug("Cached value for key: %s (expires: %s)", key[:50], expires_at.isoformat())
            return True
            
        except Exception as e:
            logger.error("Error writing cache for key %s: %s", key[:50], str(e), exc_info=True)
            # Clean up on error
            cache_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cached value."""
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(key)
        
        try:
            cache_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error("Error deleting cache for key %s: %s", key[:50], str(e))
            return False
    
    def clear(self) -> int:
        """
        Clear all cache files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
                count += 1
            for meta_file in self.cache_dir.glob("*.meta"):
                meta_file.unlink()
            logger.info("Cleared %d cache files", count)
        except Exception as e:
            logger.error("Error clearing cache: %s", str(e), exc_info=True)
        return count


# Global cache instances
_file_cache = FileCache()
_memory_cache: Dict[str, Any] = {}
_memory_cache_ttl: Dict[str, datetime] = {}
_memory_cache_lock = threading.Lock()
_memory_cache_max_size = 100  # Maximum number of items in memory cache
_cache_stats = {
    "file_hits": 0,
    "file_misses": 0,
    "memory_hits": 0,
    "memory_misses": 0,
}


class LRUCache:
    """
    Thread-safe LRU (Least Recently Used) in-memory cache with TTL support.
    
    Provides fast access to frequently used data while limiting memory usage.
    """
    
    def __init__(self, max_size: int = 100, default_ttl_seconds: int = 3600):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to store
            default_ttl_seconds: Default TTL in seconds (1 hour default)
        """
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._ttl: Dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            if key in self._ttl:
                if datetime.now() > self._ttl[key]:
                    # Expired, remove it
                    del self._cache[key]
                    del self._ttl[key]
                    return None
            
            # Move to end (most recently used)
            value = self._cache.pop(key)
            self._cache[key] = value
            return value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Store value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (uses default if None)
        """
        with self._lock:
            # Remove oldest if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Remove least recently used (first item)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                if oldest_key in self._ttl:
                    del self._ttl[oldest_key]
            
            ttl_seconds = ttl_seconds or self.default_ttl_seconds
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
            self._cache[key] = value
            self._ttl[key] = expires_at
    
    def delete(self, key: str) -> None:
        """Delete cached value."""
        with self._lock:
            self._cache.pop(key, None)
            self._ttl.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            self._ttl.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


# Global memory cache instance
_memory_cache_instance = LRUCache(max_size=_memory_cache_max_size, default_ttl_seconds=3600)


def _generate_cache_key(func_name: str, *args, **kwargs) -> str:
    """Generate a cache key from function name and arguments."""
    cache_key_parts = [func_name]
    
    # Add args (skip self if method)
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            cache_key_parts.append(str(arg))
        elif isinstance(arg, dict):
            cache_key_parts.append(json.dumps(arg, sort_keys=True))
        elif hasattr(arg, '__dict__'):
            cache_key_parts.append(str(arg))
    
    # Add kwargs
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            cache_key_parts.append(f"{k}:{v}")
        elif isinstance(v, dict):
            cache_key_parts.append(f"{k}:{json.dumps(v, sort_keys=True)}")
    
    cache_key = "|".join(cache_key_parts)
    return hashlib.sha256(cache_key.encode()).hexdigest()


def cache_gemini_response(ttl_hours: int = DEFAULT_TTL_HOURS, use_memory_cache: bool = True):
    """
    Decorator to cache Gemini API responses with two-level caching.
    
    Uses in-memory LRU cache for fast access, falls back to file cache for persistence.
    
    Args:
        ttl_hours: Time-to-live in hours
        use_memory_cache: If True, use in-memory cache first (faster)
        
    Usage:
        @cache_gemini_response(ttl_hours=24)
        def generate_report(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key_hash = _generate_cache_key(func.__name__, *args, **kwargs)
            
            # Try memory cache first (if enabled)
            if use_memory_cache:
                cached_result = _memory_cache_instance.get(cache_key_hash)
                if cached_result is not None:
                    _cache_stats["memory_hits"] += 1
                    logger.debug("Memory cache hit for %s", func.__name__)
                    return cached_result
                _cache_stats["memory_misses"] += 1
            
            # Try file cache
            cached_result = _file_cache.get(cache_key_hash)
            if cached_result is not None:
                _cache_stats["file_hits"] += 1
                logger.info("File cache hit for %s", func.__name__)
                # Also store in memory cache for faster future access
                if use_memory_cache:
                    _memory_cache_instance.set(cache_key_hash, cached_result, ttl_seconds=ttl_hours * 3600)
                return cached_result
            _cache_stats["file_misses"] += 1
            
            # Call function and cache result
            try:
                result = func(*args, **kwargs)
                # Store in both caches
                _file_cache.set(cache_key_hash, result, ttl_hours=ttl_hours)
                if use_memory_cache:
                    _memory_cache_instance.set(cache_key_hash, result, ttl_seconds=ttl_hours * 3600)
                return result
            except Exception as e:
                logger.error("Error in cached function %s: %s", func.__name__, str(e), exc_info=True)
                raise
        
        return wrapper
    return decorator


def cache_firestore_query(ttl_seconds: int = 300):
    """
    Decorator to cache Firestore query results in memory.
    
    Args:
        ttl_seconds: Time-to-live in seconds (5 minutes default)
        
    Usage:
        @cache_firestore_query(ttl_seconds=300)
        def get_daily_report(trading_date: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key_hash = _generate_cache_key(f"firestore_{func.__name__}", *args, **kwargs)
            
            # Try memory cache
            cached_result = _memory_cache_instance.get(cache_key_hash)
            if cached_result is not None:
                _cache_stats["memory_hits"] += 1
                logger.debug("Firestore query cache hit for %s", func.__name__)
                return cached_result
            _cache_stats["memory_misses"] += 1
            
            # Execute query
            try:
                result = func(*args, **kwargs)
                # Store in memory cache
                _memory_cache_instance.set(cache_key_hash, result, ttl_seconds=ttl_seconds)
                return result
            except Exception as e:
                logger.error("Error in cached Firestore query %s: %s", func.__name__, str(e), exc_info=True)
                raise
        
        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Any]:
    """
    Get comprehensive cache statistics including hit rates.
    
    Returns:
        Dictionary with cache statistics
    """
    try:
        cache_files = list(CACHE_DIR.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files if f.exists())
        
        # Calculate hit rates
        total_file_requests = _cache_stats["file_hits"] + _cache_stats["file_misses"]
        total_memory_requests = _cache_stats["memory_hits"] + _cache_stats["memory_misses"]
        
        file_hit_rate = (
            _cache_stats["file_hits"] / total_file_requests * 100
            if total_file_requests > 0 else 0
        )
        memory_hit_rate = (
            _cache_stats["memory_hits"] / total_memory_requests * 100
            if total_memory_requests > 0 else 0
        )
        
        return {
            "file_cache": {
                "cache_dir": str(CACHE_DIR),
                "file_count": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "hits": _cache_stats["file_hits"],
                "misses": _cache_stats["file_misses"],
                "hit_rate_percent": round(file_hit_rate, 2)
            },
            "memory_cache": {
                "size": _memory_cache_instance.size(),
                "max_size": _memory_cache_instance.max_size,
                "hits": _cache_stats["memory_hits"],
                "misses": _cache_stats["memory_misses"],
                "hit_rate_percent": round(memory_hit_rate, 2)
            }
        }
    except Exception as e:
        logger.error("Error getting cache stats: %s", str(e))
        return {"error": str(e)}


def clear_all_caches() -> Dict[str, int]:
    """
    Clear both file and memory caches.
    
    Returns:
        Dictionary with counts of cleared items
    """
    file_count = _file_cache.clear()
    _memory_cache_instance.clear()
    
    # Reset stats
    _cache_stats["file_hits"] = 0
    _cache_stats["file_misses"] = 0
    _cache_stats["memory_hits"] = 0
    _cache_stats["memory_misses"] = 0
    
    return {
        "file_cache_cleared": file_count,
        "memory_cache_cleared": _memory_cache_instance.size()
    }


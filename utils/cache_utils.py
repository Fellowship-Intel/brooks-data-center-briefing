"""Caching utilities for Gemini responses and expensive operations."""
import logging
import hashlib
import json
import pickle
from typing import Optional, Any, Dict
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps

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


# Global cache instance
_cache = FileCache()


def cache_gemini_response(ttl_hours: int = DEFAULT_TTL_HOURS):
    """
    Decorator to cache Gemini API responses.
    
    Args:
        ttl_hours: Time-to-live in hours
        
    Usage:
        @cache_gemini_response(ttl_hours=24)
        def generate_report(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key_parts = [func.__name__]
            
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
            cache_key_hash = hashlib.sha256(cache_key.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = _cache.get(cache_key_hash)
            if cached_result is not None:
                logger.info("Using cached result for %s", func.__name__)
                return cached_result
            
            # Call function and cache result
            try:
                result = func(*args, **kwargs)
                _cache.set(cache_key_hash, result, ttl_hours=ttl_hours)
                return result
            except Exception as e:
                logger.error("Error in cached function %s: %s", func.__name__, str(e), exc_info=True)
                raise
        
        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    try:
        cache_files = list(CACHE_DIR.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files if f.exists())
        
        return {
            "cache_dir": str(CACHE_DIR),
            "file_count": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    except Exception as e:
        logger.error("Error getting cache stats: %s", str(e))
        return {"error": str(e)}


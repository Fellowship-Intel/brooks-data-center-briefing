"""Tests for cache utilities."""
import pytest
import tempfile
import shutil
from pathlib import Path
from utils.cache_utils import FileCache, cache_gemini_response, get_cache_stats


class TestFileCache:
    """Test FileCache functionality."""
    
    @pytest.fixture
    def cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cache(self, cache_dir):
        """Create cache instance."""
        return FileCache(cache_dir=cache_dir, default_ttl_hours=1)
    
    def test_set_and_get(self, cache):
        """Test setting and getting cache values."""
        cache.set("test_key", {"data": "value"})
        result = cache.get("test_key")
        assert result == {"data": "value"}
    
    def test_cache_miss(self, cache):
        """Test cache miss returns None."""
        result = cache.get("nonexistent_key")
        assert result is None
    
    def test_cache_delete(self, cache):
        """Test cache deletion."""
        cache.set("test_key", "value")
        assert cache.get("test_key") == "value"
        cache.delete("test_key")
        assert cache.get("test_key") is None
    
    def test_cache_clear(self, cache):
        """Test clearing all cache."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        count = cache.clear()
        assert count >= 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestCacheDecorator:
    """Test cache decorator."""
    
    def test_cache_decorator(self, tmp_path):
        """Test caching decorator."""
        from utils.cache_utils import FileCache, cache_gemini_response
        
        cache = FileCache(cache_dir=tmp_path)
        
        call_count = 0
        
        @cache_gemini_response(ttl_hours=1)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call - should execute
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call - should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment


class TestCacheStats:
    """Test cache statistics."""
    
    def test_get_cache_stats(self, tmp_path):
        """Test getting cache statistics."""
        cache = FileCache(cache_dir=tmp_path)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        stats = get_cache_stats()
        assert "file_count" in stats
        assert "total_size_bytes" in stats


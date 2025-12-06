"""Tests for retry utilities."""
import pytest
import time
from unittest.mock import Mock, patch
from utils.retry_utils import retry_with_backoff, retry_on_network_error, retry_on_api_error


class TestRetryUtils:
    """Test retry utilities."""
    
    def test_retry_success_on_first_attempt(self):
        """Test that successful function doesn't retry."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure(self):
        """Test retry on failure."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, initial_delay=0.1)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = failing_func()
        assert result == "success"
        assert call_count == 2
    
    def test_retry_exhausted(self):
        """Test that exception is raised when retries exhausted."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, initial_delay=0.1)
        def always_failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            always_failing_func()
        
        assert call_count == 3  # Initial + 2 retries
    
    def test_retry_on_network_error(self):
        """Test network error retry decorator."""
        call_count = 0
        
        @retry_on_network_error(max_retries=2)
        def network_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return "success"
        
        result = network_func()
        assert result == "success"
        assert call_count == 2
    
    def test_retry_on_api_error(self):
        """Test API error retry decorator."""
        call_count = 0
        
        @retry_on_api_error(max_retries=2)
        def api_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("500 Internal Server Error")
            return "success"
        
        result = api_func()
        assert result == "success"
        assert call_count == 2


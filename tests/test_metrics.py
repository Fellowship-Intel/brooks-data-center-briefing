"""Tests for metrics collection."""
import pytest
import time
from utils.metrics import MetricsCollector, get_metrics_collector, time_operation


class TestMetricsCollector:
    """Test metrics collector."""
    
    def test_record_timing(self):
        """Test recording timing metrics."""
        collector = MetricsCollector()
        collector.record_timing("test_operation", 1.5, tags={"component": "test"})
        
        stats = collector.get_stats()
        assert "test_operation" in stats["timers"]
        assert stats["timers"]["test_operation"]["avg"] == 1.5
    
    def test_increment_counter(self):
        """Test incrementing counters."""
        collector = MetricsCollector()
        collector.increment_counter("test_counter", value=5)
        collector.increment_counter("test_counter", value=3)
        
        stats = collector.get_stats()
        assert stats["counters"]["test_counter"] == 8
    
    def test_time_operation_context(self):
        """Test timing operation with context manager."""
        collector = MetricsCollector()
        
        with collector.time_operation("test_op"):
            time.sleep(0.1)
        
        stats = collector.get_stats()
        assert "test_op" in stats["timers"]
        assert stats["timers"]["test_op"]["count"] == 1
        assert stats["timers"]["test_op"]["avg"] > 0
    
    def test_get_metrics_collector_singleton(self):
        """Test that get_metrics_collector returns singleton."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2


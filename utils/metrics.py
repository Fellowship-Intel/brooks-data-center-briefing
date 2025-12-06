"""Performance metrics collection and tracking."""
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Single metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None


class MetricsCollector:
    """
    Collects and tracks performance metrics.
    
    Thread-safe metric collection for tracking:
    - Report generation times
    - API response times
    - Cache hit/miss rates
    - Error rates by component
    """
    
    def __init__(self):
        self.metrics: list[Metric] = []
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, list[float]] = defaultdict(list)
        self.lock = Lock()
        self.max_metrics = 1000  # Limit stored metrics
    
    def record_timing(
        self,
        name: str,
        duration: float,
        tags: Optional[Dict[str, str]] = None,
        unit: str = "seconds",
    ) -> None:
        """
        Record a timing metric.
        
        Args:
            name: Metric name
            duration: Duration in seconds
            tags: Optional tags for filtering
            unit: Unit of measurement
        """
        with self.lock:
            metric = Metric(
                name=name,
                value=duration,
                timestamp=datetime.now(),
                tags=tags or {},
                unit=unit,
            )
            self.metrics.append(metric)
            self.timers[name].append(duration)
            
            # Trim metrics if too many
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]
    
    def increment_counter(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Counter name
            value: Increment value (default: 1)
            tags: Optional tags (used for counter key)
        """
        with self.lock:
            key = name
            if tags:
                # Include tags in counter key
                tag_str = "_".join(f"{k}:{v}" for k, v in sorted(tags.items()))
                key = f"{name}_{tag_str}"
            self.counters[key] += value
    
    def time_operation(self, name: str, tags: Optional[Dict[str, str]] = None):
        """
        Context manager for timing operations.
        
        Args:
            name: Operation name
            tags: Optional tags
            
        Example:
            with metrics.time_operation("report_generation"):
                # operation code
        """
        return _TimingContext(self, name, tags)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics.
        
        Returns:
            Dictionary with metric statistics
        """
        with self.lock:
            stats = {
                "counters": dict(self.counters),
                "timers": {},
            }
            
            # Calculate timer statistics
            for name, durations in self.timers.items():
                if durations:
                    stats["timers"][name] = {
                        "count": len(durations),
                        "min": min(durations),
                        "max": max(durations),
                        "avg": sum(durations) / len(durations),
                        "total": sum(durations),
                    }
            
            return stats
    
    def export_metrics(self) -> list[Dict[str, Any]]:
        """
        Export metrics in structured format for logging/monitoring.
        
        Returns:
            List of metric dictionaries
        """
        with self.lock:
            exported = []
            for metric in self.metrics[-100:]:  # Last 100 metrics
                exported.append({
                    "name": metric.name,
                    "value": metric.value,
                    "timestamp": metric.timestamp.isoformat(),
                    "tags": metric.tags,
                    "unit": metric.unit,
                })
            return exported


class _TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: Optional[Dict[str, str]]):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.collector.record_timing(self.name, duration, self.tags)


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_timing(name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
    """Convenience function to record timing."""
    get_metrics_collector().record_timing(name, duration, tags)


def increment_counter(name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
    """Convenience function to increment counter."""
    get_metrics_collector().increment_counter(name, value, tags)


def time_operation(name: str, tags: Optional[Dict[str, str]] = None):
    """Convenience function for timing operations."""
    return get_metrics_collector().time_operation(name, tags)


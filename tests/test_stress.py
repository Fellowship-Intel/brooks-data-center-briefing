"""
Comprehensive stress testing suite for the Brooks Data Center application.

Tests API endpoints, report generation, database queries, UI components, and integration
workflows under various load conditions.

Usage:
    # Run all stress tests
    pytest tests/test_stress.py -v
    
    # Run specific test category
    pytest tests/test_stress.py::TestAPIStress -v
    
    # Run with custom concurrency
    CONCURRENT_REQUESTS=50 pytest tests/test_stress.py::TestAPIStress::test_concurrent_report_generation -v
"""

import os
import sys
import time
import asyncio
import concurrent.futures
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from report_service import generate_watchlist_daily_report
from report_repository import get_daily_report, list_daily_reports

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", "10"))
MAX_REQUESTS = int(os.getenv("MAX_REQUESTS", "100"))
LARGE_WATCHLIST_SIZE = int(os.getenv("LARGE_WATCHLIST_SIZE", "100"))


class TestAPIStress:
    """Stress tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_concurrent_health_checks(self, client):
        """Test health check endpoint under concurrent load."""
        num_requests = CONCURRENT_REQUESTS
        results = []
        
        def make_request():
            start = time.time()
            try:
                response = client.get("/health")
                elapsed = time.time() - start
                return {
                    "status": response.status_code,
                    "elapsed": elapsed,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "status": None,
                    "elapsed": time.time() - start,
                    "success": False,
                    "error": str(e)
                }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(1 for r in results if r["success"])
        avg_time = sum(r["elapsed"] for r in results) / len(results)
        max_time = max(r["elapsed"] for r in results)
        
        assert success_count == num_requests, f"Only {success_count}/{num_requests} requests succeeded"
        assert avg_time < 1.0, f"Average response time {avg_time:.2f}s exceeds 1s"
        assert max_time < 5.0, f"Max response time {max_time:.2f}s exceeds 5s"
    
    @pytest.mark.slow
    def test_concurrent_report_generation(self, client):
        """Test report generation endpoint under concurrent load."""
        num_requests = min(CONCURRENT_REQUESTS, 5)  # Limit to 5 for report generation
        
        test_data = {
            "trading_date": date.today().isoformat(),
            "client_id": "test_client",
            "market_data": {
                "tickers": ["AAPL", "MSFT"],
                "prices": {
                    "AAPL": {"close": 150.0, "change_percent": 1.0},
                    "MSFT": {"close": 300.0, "change_percent": -0.5}
                }
            }
        }
        
        results = []
        
        def make_request():
            start = time.time()
            try:
                with patch('report_service.generate_and_store_daily_report') as mock_gen:
                    mock_gen.return_value = {"trading_date": test_data["trading_date"]}
                    response = client.post("/reports/generate", json=test_data)
                    elapsed = time.time() - start
                    return {
                        "status": response.status_code,
                        "elapsed": elapsed,
                        "success": response.status_code in [200, 201]
                    }
            except Exception as e:
                return {
                    "status": None,
                    "elapsed": time.time() - start,
                    "success": False,
                    "error": str(e)
                }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(1 for r in results if r["success"])
        avg_time = sum(r["elapsed"] for r in results) / len(results) if results else 0
        
        # Report generation is slower, so we allow some failures under load
        assert success_count >= num_requests * 0.8, f"Only {success_count}/{num_requests} requests succeeded"
        assert avg_time < 30.0, f"Average response time {avg_time:.2f}s exceeds 30s"
    
    def test_rate_limiting_under_load(self, client):
        """Test that rate limiting works correctly under load."""
        num_requests = CONCURRENT_REQUESTS * 2
        
        def make_request():
            try:
                response = client.get("/health")
                return response.status_code
            except Exception:
                return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All health checks should succeed (they're not rate limited)
        success_count = sum(1 for r in results if r == 200)
        assert success_count == num_requests, f"Rate limiting blocked {num_requests - success_count} requests"


class TestReportGenerationStress:
    """Stress tests for report generation."""
    
    def test_large_watchlist_processing(self):
        """Test report generation with a large watchlist."""
        large_watchlist = [f"TICKER{i:03d}" for i in range(LARGE_WATCHLIST_SIZE)]
        trading_date = date.today()
        
        with patch('report_service.generate_and_store_daily_report') as mock_gen:
            mock_gen.return_value = {"trading_date": trading_date.isoformat()}
            
            start = time.time()
            try:
                result = generate_watchlist_daily_report(
                    trading_date=trading_date,
                    client_id="test_client",
                    watchlist=large_watchlist
                )
                elapsed = time.time() - start
                
                assert result is not None
                assert elapsed < 60.0, f"Large watchlist processing took {elapsed:.2f}s (exceeds 60s)"
            except Exception as e:
                pytest.fail(f"Large watchlist processing failed: {e}")
    
    def test_concurrent_report_generations(self):
        """Test multiple simultaneous report generations."""
        num_generations = min(CONCURRENT_REQUESTS, 3)  # Limit to 3 for actual generation
        watchlist = ["AAPL", "MSFT", "GOOGL"]
        trading_date = date.today()
        
        results = []
        
        def generate_report():
            start = time.time()
            try:
                with patch('report_service.generate_and_store_daily_report') as mock_gen:
                    mock_gen.return_value = {"trading_date": trading_date.isoformat()}
                    result = generate_watchlist_daily_report(
                        trading_date=trading_date,
                        client_id="test_client",
                        watchlist=watchlist
                    )
                    elapsed = time.time() - start
                    return {
                        "success": result is not None,
                        "elapsed": elapsed
                    }
            except Exception as e:
                return {
                    "success": False,
                    "elapsed": time.time() - start,
                    "error": str(e)
                }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_generations) as executor:
            futures = [executor.submit(generate_report) for _ in range(num_generations)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(1 for r in results if r["success"])
        assert success_count == num_generations, f"Only {success_count}/{num_generations} generations succeeded"


class TestDatabaseStress:
    """Stress tests for database queries."""
    
    @pytest.fixture
    def mock_firestore(self):
        """Mock Firestore client."""
        with patch('gcp_clients.get_firestore_client') as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            yield mock_client
    
    def test_concurrent_firestore_reads(self, mock_firestore):
        """Test concurrent Firestore read operations."""
        num_reads = CONCURRENT_REQUESTS
        
        # Mock Firestore document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "trading_date": date.today().isoformat(),
            "summary_text": "Test summary"
        }
        mock_doc.id = date.today().isoformat()
        
        mock_collection = MagicMock()
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore.collection.return_value = mock_collection
        
        results = []
        
        def read_report():
            start = time.time()
            try:
                report = get_daily_report(date.today().isoformat())
                elapsed = time.time() - start
                return {
                    "success": report is not None,
                    "elapsed": elapsed
                }
            except Exception as e:
                return {
                    "success": False,
                    "elapsed": time.time() - start,
                    "error": str(e)
                }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_reads) as executor:
            futures = [executor.submit(read_report) for _ in range(num_reads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(1 for r in results if r["success"])
        avg_time = sum(r["elapsed"] for r in results) / len(results) if results else 0
        
        assert success_count == num_reads, f"Only {success_count}/{num_reads} reads succeeded"
        assert avg_time < 1.0, f"Average read time {avg_time:.2f}s exceeds 1s"
    
    def test_large_dataset_query_performance(self, mock_firestore):
        """Test query performance with large datasets."""
        # Mock large result set
        mock_reports = [
            {
                "id": f"2025-01-{i:02d}",
                "trading_date": f"2025-01-{i:02d}",
                "summary_text": f"Report {i}"
            }
            for i in range(1, 1001)  # 1000 reports
        ]
        
        mock_collection = MagicMock()
        mock_query = MagicMock()
        mock_query.limit.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.stream.return_value = [
            MagicMock(id=r["id"], to_dict=lambda: r) for r in mock_reports[:50]
        ]
        mock_collection.where.return_value = mock_query
        mock_firestore.collection.return_value = mock_collection
        
        start = time.time()
        try:
            result = list_daily_reports(limit=50, order_by="trading_date", descending=True)
            elapsed = time.time() - start
            
            assert result is not None
            assert elapsed < 2.0, f"Large dataset query took {elapsed:.2f}s (exceeds 2s)"
        except Exception as e:
            pytest.fail(f"Large dataset query failed: {e}")


class TestIntegrationStress:
    """Stress tests for integration workflows."""
    
    def test_full_workflow_under_load(self):
        """Test complete workflow (generate → save → retrieve) under load."""
        num_workflows = min(CONCURRENT_REQUESTS, 3)
        watchlist = ["AAPL", "MSFT"]
        trading_date = date.today()
        
        results = []
        
        def run_workflow():
            start = time.time()
            try:
                with patch('report_service.generate_and_store_daily_report') as mock_gen, \
                     patch('report_repository.get_daily_report') as mock_get:
                    
                    mock_gen.return_value = {
                        "trading_date": trading_date.isoformat(),
                        "summary_text": "Test summary"
                    }
                    mock_get.return_value = {
                        "trading_date": trading_date.isoformat(),
                        "summary_text": "Test summary"
                    }
                    
                    # Generate
                    result = generate_watchlist_daily_report(
                        trading_date=trading_date,
                        client_id="test_client",
                        watchlist=watchlist
                    )
                    
                    # Retrieve
                    report = get_daily_report(trading_date.isoformat())
                    
                    elapsed = time.time() - start
                    return {
                        "success": result is not None and report is not None,
                        "elapsed": elapsed
                    }
            except Exception as e:
                return {
                    "success": False,
                    "elapsed": time.time() - start,
                    "error": str(e)
                }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workflows) as executor:
            futures = [executor.submit(run_workflow) for _ in range(num_workflows)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(1 for r in results if r["success"])
        assert success_count == num_workflows, f"Only {success_count}/{num_workflows} workflows succeeded"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


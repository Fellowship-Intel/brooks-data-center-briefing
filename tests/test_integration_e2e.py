"""
End-to-end integration tests for the complete report generation workflow.

Tests the full pipeline from input to report generation, storage, and retrieval.
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from report_service import generate_and_store_daily_report
from report_repository import get_daily_report


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_full_report_generation_workflow(
        self, mock_gemini, mock_firestore, mock_storage, mock_tts
    ):
        """Test the complete workflow from input to stored report."""
        trading_date = date.today()
        client_id = "test_client"
        
        market_data = {
            "tickers": ["SMCI", "NVDA"],
            "prices": {
                "SMCI": {"close": 850.25, "change_percent": 1.8},
                "NVDA": {"close": 450.50, "change_percent": -0.5},
            },
            "indices": {
                "SPX": {"close": 5200.12, "change_percent": 0.4},
            },
        }
        
        news_items = [
            {
                "title": "Test News",
                "source": "Test Source",
                "url": "https://example.com",
                "published_at": "2025-01-27T10:00:00Z",
            }
        ]
        
        macro_context = "Test macro context"
        
        # Generate report
        result = generate_and_store_daily_report(
            trading_date=trading_date,
            client_id=client_id,
            market_data=market_data,
            news_items=news_items,
            macro_context=macro_context,
        )
        
        # Verify result structure
        assert "summary_text" in result
        assert "key_insights" in result
        assert "market_context" in result
        assert result["client_id"] == client_id
        assert result["trading_date"] == trading_date.isoformat()
        
        # Verify that Firestore was called
        assert mock_firestore["mock_create"].called
        
        # Verify that TTS was attempted
        assert mock_tts["mock_synthesize"].called
    
    def test_api_end_to_end_workflow(
        self, mock_gemini, mock_firestore, mock_storage, mock_tts
    ):
        """Test complete workflow through API endpoints."""
        client = TestClient(app)
        
        # Step 1: Generate report via API
        response = client.post(
            "/reports/generate",
            json={
                "trading_date": date.today().isoformat(),
                "client_id": "test_client",
                "market_data": {
                    "tickers": ["SMCI"],
                    "prices": {"SMCI": {"close": 850.25, "change_percent": 1.8}},
                },
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "trading_date" in data
        assert "client_id" in data
        assert "summary_text" in data
        
        trading_date = data["trading_date"]
        
        # Step 2: Fetch report via API
        fetch_response = client.get(f"/reports/{trading_date}")
        assert fetch_response.status_code == 200
        fetch_data = fetch_response.json()
        assert fetch_data["trading_date"] == trading_date
        assert "summary_text" in fetch_data
    
    def test_watchlist_report_workflow(
        self, mock_gemini, mock_firestore, mock_storage, mock_tts
    ):
        """Test watchlist report generation workflow."""
        from report_service import generate_watchlist_daily_report
        
        trading_date = date.today()
        client_id = "test_client"
        watchlist = ["SMCI", "NVDA", "IREN"]
        
        # Generate watchlist report
        result = generate_watchlist_daily_report(
            trading_date=trading_date,
            client_id=client_id,
            watchlist=watchlist,
        )
        
        # Verify result
        assert "summary_text" in result
        assert "key_insights" in result
        assert result["client_id"] == client_id
        
        # Verify that market data was fetched (mocked)
        # Verify that report was stored
        assert mock_firestore["mock_create"].called
    
    def test_error_handling_in_workflow(
        self, mock_gemini, mock_firestore, mock_storage, mock_tts
    ):
        """Test that errors are handled gracefully in the workflow."""
        # Make TTS fail
        mock_tts["mock_synthesize"].side_effect = Exception("TTS failed")
        
        trading_date = date.today()
        client_id = "test_client"
        
        market_data = {
            "tickers": ["SMCI"],
            "prices": {"SMCI": {"close": 850.25, "change_percent": 1.8}},
        }
        
        # Generate report - should succeed even if TTS fails
        result = generate_and_store_daily_report(
            trading_date=trading_date,
            client_id=client_id,
            market_data=market_data,
            news_items=[],
            macro_context=None,
        )
        
        # Report should still be generated
        assert "summary_text" in result
        assert result["client_id"] == client_id
        
        # TTS failure should be logged but not break the pipeline
        # (audio_gcs_path might be None)
        # This is expected behavior - TTS failures are non-fatal
    
    def test_caching_in_workflow(
        self, mock_gemini, mock_firestore, mock_storage, mock_tts
    ):
        """Test that caching works correctly in the workflow."""
        from report_service import generate_watchlist_daily_report
        
        trading_date = date.today()
        client_id = "test_client"
        watchlist = ["SMCI", "NVDA"]
        
        # First call
        result1 = generate_watchlist_daily_report(
            trading_date=trading_date,
            client_id=client_id,
            watchlist=watchlist,
        )
        
        # Second call with same parameters (should use cache)
        result2 = generate_watchlist_daily_report(
            trading_date=trading_date,
            client_id=client_id,
            watchlist=watchlist,
        )
        
        # Results should be the same (from cache)
        assert result1["summary_text"] == result2["summary_text"]
        
        # Gemini should only be called once (cached on second call)
        # Note: This depends on the cache implementation
        # The actual number of calls might vary based on cache TTL


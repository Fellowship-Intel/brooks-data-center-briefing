"""
Pytest tests for FastAPI report endpoints.

Uses TestClient so no running server is required.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_report_repository():
    """Mock report_repository.get_daily_report."""
    # Patch where it's used in app.main, not where it's defined
    with patch("app.main.get_daily_report") as mock_get_report:
        # Return None by default (report not found)
        mock_get_report.return_value = None
        yield mock_get_report


def test_generate_report(
    client: TestClient,
    mock_gemini,
    mock_firestore,
    mock_storage,
    mock_tts,
) -> None:
    """Test generating a report using dummy data."""
    response = client.post(
        "/reports/generate",
        json={},
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "trading_date" in result
    assert "client_id" in result
    assert result["client_id"] == "michael_brooks"


def test_fetch_report(
    client: TestClient,
    mock_gemini,
    mock_firestore,
    mock_storage,
    mock_tts,
    mock_report_repository,
) -> None:
    """Test fetching a previously generated report."""
    # First generate a report
    generate_response = client.post("/reports/generate", json={})
    assert generate_response.status_code == 200
    trading_date = generate_response.json().get("trading_date")
    
    if trading_date:
        # Mock the repository to return a report
        mock_report_repository.return_value = {
            "client_id": "michael_brooks",
            "trading_date": trading_date,
            "summary_text": "Test summary",
        }
        
        response = client.get(f"/reports/{trading_date}")
        # Should succeed with mocked repository
        assert response.status_code == 200
        result = response.json()
        assert result["trading_date"] == trading_date or result.get("trading_date") == trading_date


def test_fetch_audio_metadata(
    client: TestClient,
    mock_gemini,
    mock_firestore,
    mock_storage,
    mock_tts,
    mock_report_repository,
) -> None:
    """Test fetching audio metadata for a report."""
    # First generate a report
    generate_response = client.post("/reports/generate", json={})
    assert generate_response.status_code == 200
    trading_date = generate_response.json().get("trading_date")
    
    if trading_date:
        # Mock the repository to return a report with audio
        mock_report_repository.return_value = {
            "client_id": "michael_brooks",
            "trading_date": trading_date,
            "audio_gcs_path": "gs://bucket/reports/michael_brooks/2025-01-02/report.wav",
        }
        
        response = client.get(f"/reports/{trading_date}/audio")
        # Should succeed with mocked repository
        assert response.status_code == 200
        result = response.json()
        assert "audio_gcs_path" in result
        assert result["audio_gcs_path"] == "gs://bucket/reports/michael_brooks/2025-01-02/report.wav"


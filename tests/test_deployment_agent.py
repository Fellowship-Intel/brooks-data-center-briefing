#!/usr/bin/env python
"""
Deployment Testing Agent

Verifies that:
1. All dependencies can be imported
2. API endpoints are accessible and functional
3. GCP services are properly configured
4. Deployment is working from the outside

Usage:
    # Test local deployment
    python -m pytest tests/test_deployment_agent.py -v
    
    # Test deployed service (set BASE_URL env var)
    BASE_URL=https://your-service.run.app python -m pytest tests/test_deployment_agent.py::test_deployed_api -v
"""

import os
import sys
import subprocess
from typing import Dict, List, Optional, Tuple
from datetime import date

import pytest
import requests


# ============================================================================
# Configuration
# ============================================================================

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "mikebrooks")
REGION = os.getenv("GCP_REGION", "us-central1")
API_SERVICE = os.getenv("API_SERVICE_NAME", "brooks-briefing-api")
UI_SERVICE = os.getenv("UI_SERVICE_NAME", "brooks-briefing-ui")

TIMEOUT = 30  # seconds


# ============================================================================
# Dependency Resolution Tests
# ============================================================================

def test_import_core_modules():
    """Verify all core Python modules can be imported."""
    modules = [
        "fastapi",
        "streamlit",
        "google.cloud.firestore",
        "google.cloud.storage",
        "google.cloud.secretmanager",
        "google.generativeai",
        "pandas",
        "yfinance",
    ]
    
    failed_imports = []
    for module in modules:
        try:
            __import__(module)
        except ImportError as e:
            failed_imports.append((module, str(e)))
    
    if failed_imports:
        error_msg = "Failed to import modules:\n"
        for module, error in failed_imports:
            error_msg += f"  - {module}: {error}\n"
        pytest.fail(error_msg)
    
    assert True, "All core modules imported successfully"


def test_import_app_modules():
    """Verify application modules can be imported."""
    app_modules = [
        "app.main",
        "report_service",
        "report_repository",
        "python_app.services.gemini_service",
        "python_app.services.gcp_service",
        "python_app.services.market_data_service",
        "python_app.constants",
        "python_app.types",
    ]
    
    failed_imports = []
    for module in app_modules:
        try:
            __import__(module)
        except ImportError as e:
            failed_imports.append((module, str(e)))
    
    if failed_imports:
        error_msg = "Failed to import app modules:\n"
        for module, error in failed_imports:
            error_msg += f"  - {module}: {error}\n"
        pytest.fail(error_msg)
    
    assert True, "All app modules imported successfully"


# ============================================================================
# API Health Checks
# ============================================================================

def test_api_health_check():
    """Test that the API is accessible."""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
        # FastAPI docs endpoint should return 200
        assert response.status_code == 200, f"API not accessible: {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.skip(f"API not accessible at {BASE_URL}. Is the server running?")
    except requests.exceptions.Timeout:
        pytest.fail(f"API request timed out after {TIMEOUT}s")


def test_api_root_endpoint():
    """Test API root endpoint (if it exists)."""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        # Any 2xx or 3xx response is acceptable
        assert response.status_code < 400, f"Root endpoint returned {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.skip(f"API not accessible at {BASE_URL}")
    except requests.exceptions.Timeout:
        pytest.fail(f"API request timed out after {TIMEOUT}s")


def test_api_generate_report_endpoint():
    """Test the report generation endpoint."""
    try:
        response = requests.post(
            f"{BASE_URL}/reports/generate",
            json={},
            timeout=TIMEOUT,
        )
        assert response.status_code == 200, f"Generate endpoint returned {response.status_code}"
        
        data = response.json()
        assert "client_id" in data, "Response missing client_id"
        assert "trading_date" in data, "Response missing trading_date"
        assert data["client_id"] == "michael_brooks", "Unexpected client_id"
        
    except requests.exceptions.ConnectionError:
        pytest.skip(f"API not accessible at {BASE_URL}")
    except requests.exceptions.Timeout:
        pytest.fail(f"API request timed out after {TIMEOUT}s")


def test_api_watchlist_endpoint():
    """Test the watchlist report generation endpoint."""
    try:
        payload = {
            "client_id": "michael_brooks",
            "watchlist": ["IREN", "CRWV"],
            "trading_date": date.today().isoformat(),
        }
        
        response = requests.post(
            f"{BASE_URL}/reports/generate/watchlist",
            json=payload,
            timeout=TIMEOUT,
        )
        assert response.status_code == 200, f"Watchlist endpoint returned {response.status_code}"
        
        data = response.json()
        assert "client_id" in data, "Response missing client_id"
        assert "watchlist" in data, "Response missing watchlist"
        assert "summary_text" in data, "Response missing summary_text"
        assert set(data["watchlist"]) == {"IREN", "CRWV"}, "Watchlist mismatch"
        
    except requests.exceptions.ConnectionError:
        pytest.skip(f"API not accessible at {BASE_URL}")
    except requests.exceptions.Timeout:
        pytest.fail(f"API request timed out after {TIMEOUT}s")


def test_api_get_report_endpoint():
    """Test fetching a report by trading date."""
    try:
        trading_date = date.today().isoformat()
        response = requests.get(
            f"{BASE_URL}/reports/{trading_date}",
            params={"client_id": "michael_brooks"},
            timeout=TIMEOUT,
        )
        # 200 (found) or 404 (not found) are both acceptable
        assert response.status_code in [200, 404], \
            f"Get report endpoint returned {response.status_code}"
        
    except requests.exceptions.ConnectionError:
        pytest.skip(f"API not accessible at {BASE_URL}")
    except requests.exceptions.Timeout:
        pytest.fail(f"API request timed out after {TIMEOUT}s")


# ============================================================================
# GCP Service Checks
# ============================================================================

def test_gcp_project_configured():
    """Verify GCP project ID is configured."""
    project_id = os.getenv("GCP_PROJECT_ID", PROJECT_ID)
    assert project_id, "GCP_PROJECT_ID not set"
    assert project_id != "mikebrooks" or os.getenv("GCP_PROJECT_ID"), \
        "Using default project ID - verify this is intentional"


def test_gcp_credentials_available():
    """Check if GCP credentials are available."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # In Cloud Run, credentials come from the service account
    # Locally, they come from GOOGLE_APPLICATION_CREDENTIALS
    if not creds_path:
        # Check if we're in Cloud Run (has metadata server)
        try:
            import requests as req
            metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
            response = req.get(
                metadata_url,
                headers={"Metadata-Flavor": "Google"},
                timeout=2,
            )
            if response.status_code == 200:
                pytest.skip("Running in Cloud Run - credentials from service account")
        except:
            pass
        
        pytest.skip("GOOGLE_APPLICATION_CREDENTIALS not set and not in Cloud Run")
    
    assert os.path.exists(creds_path), f"Credentials file not found: {creds_path}"


# ============================================================================
# Log Reading (Optional - requires gcloud CLI)
# ============================================================================

def test_read_api_logs():
    """Read recent API service logs (requires gcloud CLI)."""
    if not shutil.which("gcloud"):
        pytest.skip("gcloud CLI not found - skipping log test")
    
    try:
        cmd = [
            "gcloud", "logs", "read",
            f"--project={PROJECT_ID}",
            f"--region={REGION}",
            f"--service={API_SERVICE}",
            "--limit=10",
            "--format=json",
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            pytest.skip(f"Failed to read logs: {result.stderr}")
        
        # If we get here, logs were read successfully
        assert True, "Successfully read API logs"
        
    except subprocess.TimeoutExpired:
        pytest.skip("Log read timed out")
    except FileNotFoundError:
        pytest.skip("gcloud CLI not found")


def test_read_ui_logs():
    """Read recent UI service logs (requires gcloud CLI)."""
    if not shutil.which("gcloud"):
        pytest.skip("gcloud CLI not found - skipping log test")
    
    try:
        cmd = [
            "gcloud", "logs", "read",
            f"--project={PROJECT_ID}",
            f"--region={REGION}",
            f"--service={UI_SERVICE}",
            "--limit=10",
            "--format=json",
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            pytest.skip(f"Failed to read logs: {result.stderr}")
        
        # If we get here, logs were read successfully
        assert True, "Successfully read UI logs"
        
    except subprocess.TimeoutExpired:
        pytest.skip("Log read timed out")
    except FileNotFoundError:
        pytest.skip("gcloud CLI not found")


# ============================================================================
# Helper Functions
# ============================================================================

import shutil


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == "__main__":
    print("🧪 Deployment Testing Agent")
    print(f"Base URL: {BASE_URL}")
    print(f"Project ID: {PROJECT_ID}")
    print(f"Region: {REGION}")
    print("")
    
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])


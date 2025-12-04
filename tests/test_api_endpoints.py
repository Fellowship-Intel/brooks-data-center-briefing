"""
Test script for FastAPI report endpoints.

Prerequisites: FastAPI server must be running on http://localhost:8000

Run with:
    python tests/test_api_endpoints.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from typing import Any, Dict

import requests


BASE_URL = "http://localhost:8000"


def test_generate_report() -> Dict[str, Any]:
    """Test 1: Generate a report using dummy data."""
    print("1️⃣  Generating report with dummy data...")
    try:
        response = requests.post(
            f"{BASE_URL}/reports/generate",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=300,  # 5 minute timeout for report generation
        )
        
        # Check if request was successful
        if response.status_code != 200:
            print(f"   ❌ Request failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error detail: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"   Error response: {response.text[:500]}")
            print()
            print("💡 Make sure the FastAPI server is running:")
            print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
            sys.exit(1)
        
        response.raise_for_status()
        result = response.json()
        trading_date = result.get("trading_date")
        print(f"   ✅ Report generated successfully!")
        print(f"   📅 Trading Date: {trading_date}")
        print(f"   📊 Client ID: {result.get('client_id')}")
        if result.get("audio_gcs_path"):
            print(f"   🎵 Audio path: {result.get('audio_gcs_path')}")
        print()
        return result
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection failed: {e}")
        print()
        print("💡 Make sure the FastAPI server is running:")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        sys.exit(1)
    except requests.exceptions.Timeout as e:
        print(f"   ❌ Request timed out: {e}")
        print("   Report generation may be taking longer than expected.")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Failed to generate report: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Error detail: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"   Error response: {e.response.text[:500]}")
        print()
        print("💡 Make sure the FastAPI server is running:")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        sys.exit(1)
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_fetch_report(trading_date: str) -> None:
    """Test 2: Fetch a previously generated report."""
    print(f"2️⃣  Fetching report for {trading_date}...")
    try:
        response = requests.get(f"{BASE_URL}/reports/{trading_date}")
        response.raise_for_status()
        result = response.json()
        print("   ✅ Report fetched successfully!")
        summary = result.get("summary_text", "")
        if summary:
            preview = summary[:100] + "..." if len(summary) > 100 else summary
            print(f"   📝 Summary (first 100 chars): {preview}")
        print()
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Failed to fetch report: {e}")
        print()


def test_fetch_audio_metadata(trading_date: str) -> None:
    """Test 3: Fetch audio metadata for a report."""
    print(f"3️⃣  Fetching audio metadata for {trading_date}...")
    try:
        response = requests.get(f"{BASE_URL}/reports/{trading_date}/audio")
        response.raise_for_status()
        result = response.json()
        print("   ✅ Audio metadata fetched successfully!")
        print(f"   🎵 Audio GCS Path: {result.get('audio_gcs_path')}")
        print()
    except requests.exceptions.RequestException as e:
        print("   ⚠️  Audio metadata not available (this is OK if audio generation is still in progress)")
        print(f"   Error: {e}")
        print()


def main() -> None:
    """Run all API endpoint tests."""
    print("🧪 Testing FastAPI Report Endpoints")
    print("====================================")
    print()

    # Test 1: Generate report
    generate_result = test_generate_report()
    trading_date = generate_result.get("trading_date")

    if not trading_date:
        print("❌ No trading_date in generate response")
        sys.exit(1)

    # Test 2: Fetch report
    test_fetch_report(trading_date)

    # Test 3: Fetch audio metadata
    test_fetch_audio_metadata(trading_date)

    print("✅ All tests completed!")


if __name__ == "__main__":
    main()


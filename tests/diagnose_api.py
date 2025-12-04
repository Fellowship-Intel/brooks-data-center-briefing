"""
Diagnostic script to check if the API server is ready and identify common issues.

Run this before running the API tests to ensure everything is set up correctly.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict

try:
    import requests
except ImportError:
    print("❌ 'requests' library not installed. Install it with:")
    print("   pip install requests")
    sys.exit(1)


BASE_URL = "http://localhost:8000"


def check_server_running() -> bool:
    """Check if the FastAPI server is running."""
    print("🔍 Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=2)
        if response.status_code == 200:
            print("   ✅ Server is running")
            return True
    except requests.exceptions.ConnectionError:
        print("   ❌ Server is not running")
        print()
        print("💡 Start the server with:")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return False
    except Exception as e:
        print(f"   ⚠️  Unexpected error checking server: {e}")
        return False
    return False


def check_environment_variables() -> None:
    """Check if required environment variables are set."""
    print("\n🔍 Checking environment variables...")
    
    required_vars = [
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",  # Alternative name
        "GOOGLE_APPLICATION_CREDENTIALS",
    ]
    
    optional_vars = [
        "GCP_PROJECT_ID",
        "REPORTS_BUCKET_NAME",
    ]
    
    all_good = True
    
    # Check for at least one API key
    has_api_key = (
        os.getenv("GOOGLE_API_KEY") is not None or
        os.getenv("GEMINI_API_KEY") is not None
    )
    
    if not has_api_key:
        print("   ❌ No Gemini API key found (GOOGLE_API_KEY or GEMINI_API_KEY)")
        all_good = False
    else:
        print("   ✅ Gemini API key found")
    
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("   ⚠️  GOOGLE_APPLICATION_CREDENTIALS not set (needed for GCP services)")
        print("      This is required for Firestore and Cloud Storage")
        all_good = False
    else:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if os.path.exists(creds_path):
            print(f"   ✅ GCP credentials file found: {creds_path}")
        else:
            print(f"   ❌ GCP credentials file not found: {creds_path}")
            all_good = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var} = {value}")
        else:
            print(f"   ⚠️  {var} not set (will use default)")
    
    return all_good


def test_health_endpoint() -> None:
    """Test if we can reach the API."""
    print("\n🔍 Testing API connectivity...")
    try:
        # Try to get the OpenAPI docs
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            print("   ✅ API is accessible")
            return
    except Exception as e:
        print(f"   ❌ Cannot reach API: {e}")
        return


def main() -> None:
    """Run all diagnostic checks."""
    print("🔧 API Diagnostic Tool")
    print("=" * 50)
    print()
    
    server_ok = check_server_running()
    
    if not server_ok:
        print("\n❌ Server is not running. Please start it first.")
        sys.exit(1)
    
    env_ok = check_environment_variables()
    test_health_endpoint()
    
    print("\n" + "=" * 50)
    if env_ok:
        print("✅ Basic checks passed. You can try running the API tests now.")
    else:
        print("⚠️  Some environment variables are missing.")
        print("   The API might still work if defaults are configured.")
    print()
    print("Run the tests with:")
    print("   python tests/test_api_endpoints.py")


if __name__ == "__main__":
    main()


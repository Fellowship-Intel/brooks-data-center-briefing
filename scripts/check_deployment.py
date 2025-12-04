#!/usr/bin/env python
"""
Deployment Check Script

Quick script to verify deployment and check logs.
Can be run standalone or as part of CI/CD.

Usage:
    # Check local deployment
    python scripts/check_deployment.py
    
    # Check deployed service
    BASE_URL=https://your-service.run.app python scripts/check_deployment.py
    
    # Check logs
    python scripts/check_deployment.py --logs
"""

import os
import sys
import subprocess
import argparse
from typing import Optional

import requests


PROJECT_ID = os.getenv("GCP_PROJECT_ID", "mikebrooks")
REGION = os.getenv("GCP_REGION", "us-central1")
API_SERVICE = os.getenv("API_SERVICE_NAME", "brooks-briefing-api")
UI_SERVICE = os.getenv("UI_SERVICE_NAME", "brooks-briefing-ui")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def check_dependencies():
    """Check if all required dependencies can be imported."""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        "fastapi",
        "streamlit",
        "google.cloud.firestore",
        "google.cloud.storage",
        "google.cloud.secretmanager",
        "google.generativeai",
        "pandas",
        "yfinance",
    ]
    
    failed = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module}: {e}")
            failed.append(module)
    
    if failed:
        print(f"\n❌ Failed to import {len(failed)} module(s)")
        return False
    
    print("✅ All dependencies resolved\n")
    return True


def check_api_health():
    """Check if API is accessible."""
    print(f"🔍 Checking API health at {BASE_URL}...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("  ✓ API is accessible")
            return True
        else:
            print(f"  ✗ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Cannot connect to {BASE_URL}")
        print("     Is the server running?")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def check_api_endpoints():
    """Test key API endpoints."""
    print("🔍 Testing API endpoints...")
    
    endpoints = [
        ("POST", "/reports/generate", {}),
        ("POST", "/reports/generate/watchlist", {
            "client_id": "michael_brooks",
            "watchlist": ["IREN", "CRWV"],
            "trading_date": "2025-01-02",
        }),
    ]
    
    all_passed = True
    for method, path, payload in endpoints:
        try:
            if method == "POST":
                response = requests.post(
                    f"{BASE_URL}{path}",
                    json=payload,
                    timeout=30,
                )
            else:
                response = requests.get(f"{BASE_URL}{path}", timeout=10)
            
            if response.status_code == 200:
                print(f"  ✓ {method} {path}")
            else:
                print(f"  ✗ {method} {path} - Status {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"  ✗ {method} {path} - Error: {e}")
            all_passed = False
    
    if all_passed:
        print("✅ All endpoints working\n")
    else:
        print("❌ Some endpoints failed\n")
    
    return all_passed


def read_logs(service_name: str, limit: int = 50):
    """Read logs from Cloud Run service."""
    import shutil
    
    if not shutil.which("gcloud"):
        print("⚠️  gcloud CLI not found - cannot read logs")
        return False
    
    print(f"📋 Reading logs for {service_name}...")
    
    cmd = [
        "gcloud", "logs", "read",
        f"--project={PROJECT_ID}",
        f"--region={REGION}",
        f"--service={service_name}",
        f"--limit={limit}",
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully read logs ({len(result.stdout)} bytes)")
            # Print last few lines
            lines = result.stdout.strip().split('\n')
            if lines:
                print("\nLast 5 log entries:")
                for line in lines[-5:]:
                    print(f"  {line}")
            return True
        else:
            print(f"❌ Failed to read logs: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Log read timed out")
        return False
    except Exception as e:
        print(f"❌ Error reading logs: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Check deployment health")
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Also read Cloud Run logs",
    )
    parser.add_argument(
        "--api-service",
        default=API_SERVICE,
        help=f"API service name (default: {API_SERVICE})",
    )
    parser.add_argument(
        "--ui-service",
        default=UI_SERVICE,
        help=f"UI service name (default: {UI_SERVICE})",
    )
    
    args = parser.parse_args()
    
    print("🧪 Deployment Check Script")
    print(f"Base URL: {BASE_URL}")
    print(f"Project: {PROJECT_ID}")
    print(f"Region: {REGION}")
    print("")
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Check API health
    health_ok = check_api_health()
    
    # Test endpoints
    endpoints_ok = check_api_endpoints()
    
    # Read logs if requested
    logs_ok = True
    if args.logs:
        print("📋 Reading logs...")
        api_logs_ok = read_logs(args.api_service)
        ui_logs_ok = read_logs(args.ui_service)
        logs_ok = api_logs_ok and ui_logs_ok
        print("")
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"API Health: {'✅' if health_ok else '❌'}")
    print(f"Endpoints: {'✅' if endpoints_ok else '❌'}")
    if args.logs:
        print(f"Logs: {'✅' if logs_ok else '❌'}")
    print("")
    
    if all([deps_ok, health_ok, endpoints_ok]):
        if args.logs:
            if logs_ok:
                print("✅ All checks passed!")
                return 0
            else:
                print("⚠️  Checks passed but log reading had issues")
                return 0
        else:
            print("✅ All checks passed!")
            return 0
    else:
        print("❌ Some checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())


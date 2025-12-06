#!/usr/bin/env python
"""
Standalone stress testing script for the Brooks Data Center application.

This script provides a command-line interface for running stress tests with
configurable concurrency levels, performance metrics collection, and report generation.

Usage:
    # Run all stress tests
    python scripts/stress_test.py
    
    # Run specific test suite
    python scripts/stress_test.py --suite api
    
    # Run with custom concurrency
    python scripts/stress_test.py --concurrent 50
    
    # Generate JSON report
    python scripts/stress_test.py --output report.json --format json
    
    # Generate CSV report
    python scripts/stress_test.py --output report.csv --format csv
"""

import argparse
import json
import csv
import sys
import time
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from fastapi.testclient import TestClient

from app.main import app


class StressTestRunner:
    """Stress test runner with metrics collection."""
    
    def __init__(self, base_url: str = "http://localhost:8000", concurrent: int = 10):
        self.base_url = base_url
        self.concurrent = concurrent
        self.metrics: List[Dict[str, Any]] = []
    
    def test_health_endpoint(self, num_requests: int) -> Dict[str, Any]:
        """Test health endpoint under load."""
        print(f"Testing health endpoint with {num_requests} concurrent requests...")
        
        results = []
        start_time = time.time()
        
        def make_request():
            req_start = time.time()
            try:
                response = requests.get(f"{self.base_url}/health", timeout=10)
                elapsed = time.time() - req_start
                return {
                    "status": response.status_code,
                    "elapsed": elapsed,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "status": None,
                    "elapsed": time.time() - req_start,
                    "success": False,
                    "error": str(e)
                }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r["success"])
        avg_time = sum(r["elapsed"] for r in results) / len(results) if results else 0
        min_time = min(r["elapsed"] for r in results) if results else 0
        max_time = max(r["elapsed"] for r in results) if results else 0
        
        metrics = {
            "test": "health_endpoint",
            "total_requests": num_requests,
            "successful_requests": success_count,
            "failed_requests": num_requests - success_count,
            "success_rate": success_count / num_requests if num_requests > 0 else 0,
            "total_time": total_time,
            "avg_response_time": avg_time,
            "min_response_time": min_time,
            "max_response_time": max_time,
            "requests_per_second": num_requests / total_time if total_time > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        self.metrics.append(metrics)
        return metrics
    
    def test_api_endpoints(self, num_requests: int) -> Dict[str, Any]:
        """Test multiple API endpoints under load."""
        print(f"Testing API endpoints with {num_requests} concurrent requests...")
        
        endpoints = [
            ("/health", "GET", None),
            ("/", "GET", None),
        ]
        
        all_results = []
        start_time = time.time()
        
        def make_request(endpoint, method, data):
            req_start = time.time()
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", json=data, timeout=10)
                elapsed = time.time() - req_start
                return {
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "elapsed": elapsed,
                    "success": response.status_code in [200, 201]
                }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "status": None,
                    "elapsed": time.time() - req_start,
                    "success": False,
                    "error": str(e)
                }
        
        for endpoint, method, data in endpoints:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent) as executor:
                futures = [executor.submit(make_request, endpoint, method, data) 
                          for _ in range(num_requests)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
                all_results.extend(results)
        
        total_time = time.time() - start_time
        total_requests = len(all_results)
        success_count = sum(1 for r in all_results if r["success"])
        avg_time = sum(r["elapsed"] for r in all_results) / len(all_results) if all_results else 0
        
        metrics = {
            "test": "api_endpoints",
            "total_requests": total_requests,
            "successful_requests": success_count,
            "failed_requests": total_requests - success_count,
            "success_rate": success_count / total_requests if total_requests > 0 else 0,
            "total_time": total_time,
            "avg_response_time": avg_time,
            "requests_per_second": total_requests / total_time if total_time > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        self.metrics.append(metrics)
        return metrics
    
    def run_all_tests(self, num_requests: int = 10) -> List[Dict[str, Any]]:
        """Run all stress tests."""
        print("=" * 60)
        print("Running Stress Tests")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Concurrent requests: {self.concurrent}")
        print(f"Requests per test: {num_requests}")
        print()
        
        self.test_health_endpoint(num_requests)
        self.test_api_endpoints(num_requests)
        
        return self.metrics
    
    def generate_report(self, output_path: Optional[str] = None, format: str = "json") -> str:
        """Generate a report from collected metrics."""
        if not self.metrics:
            return "No metrics collected. Run tests first."
        
        if output_path:
            output_file = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(f"stress_test_report_{timestamp}.{format}")
        
        if format == "json":
            with open(output_file, "w") as f:
                json.dump({
                    "summary": {
                        "total_tests": len(self.metrics),
                        "timestamp": datetime.now().isoformat()
                    },
                    "metrics": self.metrics
                }, f, indent=2)
        elif format == "csv":
            with open(output_file, "w", newline="") as f:
                if self.metrics:
                    writer = csv.DictWriter(f, fieldnames=self.metrics[0].keys())
                    writer.writeheader()
                    writer.writerows(self.metrics)
        else:
            return f"Unsupported format: {format}"
        
        return f"Report saved to {output_file}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Stress test runner for Brooks Data Center")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL for API (default: http://localhost:8000)")
    parser.add_argument("--concurrent", type=int, default=10,
                       help="Number of concurrent requests (default: 10)")
    parser.add_argument("--requests", type=int, default=10,
                       help="Number of requests per test (default: 10)")
    parser.add_argument("--suite", choices=["api", "all"], default="all",
                       help="Test suite to run (default: all)")
    parser.add_argument("--output", help="Output file path for report")
    parser.add_argument("--format", choices=["json", "csv"], default="json",
                       help="Report format (default: json)")
    
    args = parser.parse_args()
    
    runner = StressTestRunner(base_url=args.base_url, concurrent=args.concurrent)
    
    try:
        if args.suite == "all":
            runner.run_all_tests(num_requests=args.requests)
        elif args.suite == "api":
            runner.test_health_endpoint(args.requests)
            runner.test_api_endpoints(args.requests)
        
        # Print summary
        print()
        print("=" * 60)
        print("Test Summary")
        print("=" * 60)
        for metric in runner.metrics:
            print(f"\n{metric['test']}:")
            print(f"  Success Rate: {metric['success_rate']:.2%}")
            print(f"  Avg Response Time: {metric['avg_response_time']:.3f}s")
            print(f"  Requests/Second: {metric['requests_per_second']:.2f}")
        
        # Generate report
        if args.output or args.format:
            report_path = runner.generate_report(args.output, args.format)
            print(f"\n{report_path}")
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


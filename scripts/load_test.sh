#!/bin/bash
# Load testing script for Brooks Data Center application
# 
# Usage:
#   ./scripts/load_test.sh [options]
#
# Options:
#   --base-url URL        Base URL for API (default: http://localhost:8000)
#   --concurrent N       Number of concurrent requests (default: 10)
#   --requests N          Number of requests per test (default: 10)
#   --suite SUITE         Test suite: api, all (default: all)
#   --output FILE         Output file for report
#   --format FORMAT       Report format: json, csv (default: json)

set -e

# Default values
BASE_URL="${BASE_URL:-http://localhost:8000}"
CONCURRENT="${CONCURRENT:-10}"
REQUESTS="${REQUESTS:-10}"
SUITE="${SUITE:-all}"
OUTPUT="${OUTPUT:-}"
FORMAT="${FORMAT:-json}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --concurrent)
            CONCURRENT="$2"
            shift 2
            ;;
        --requests)
            REQUESTS="$2"
            shift 2
            ;;
        --suite)
            SUITE="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --base-url URL        Base URL for API (default: http://localhost:8000)"
            echo "  --concurrent N        Number of concurrent requests (default: 10)"
            echo "  --requests N           Number of requests per test (default: 10)"
            echo "  --suite SUITE          Test suite: api, all (default: all)"
            echo "  --output FILE          Output file for report"
            echo "  --format FORMAT        Report format: json, csv (default: json)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check if stress_test.py exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STRESS_TEST_SCRIPT="${SCRIPT_DIR}/stress_test.py"

if [[ ! -f "$STRESS_TEST_SCRIPT" ]]; then
    echo "Error: stress_test.py not found at $STRESS_TEST_SCRIPT"
    exit 1
fi

# Build command
CMD="python \"$STRESS_TEST_SCRIPT\" --base-url \"$BASE_URL\" --concurrent $CONCURRENT --requests $REQUESTS --suite $SUITE --format $FORMAT"

if [[ -n "$OUTPUT" ]]; then
    CMD="$CMD --output \"$OUTPUT\""
fi

# Run the stress test
echo "Running stress tests..."
echo "Base URL: $BASE_URL"
echo "Concurrent: $CONCURRENT"
echo "Requests: $REQUESTS"
echo "Suite: $SUITE"
echo ""

eval $CMD

exit_code=$?

if [[ $exit_code -eq 0 ]]; then
    echo ""
    echo "Stress tests completed successfully"
else
    echo ""
    echo "Stress tests failed with exit code: $exit_code"
fi

exit $exit_code


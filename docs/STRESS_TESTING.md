# Stress Testing Guide

This document provides a comprehensive guide to stress testing the Brooks Data Center application.

## Overview

The stress testing suite is designed to test the application under various load conditions, including:
- API endpoint performance
- Report generation under load
- Database query performance
- Integration workflow resilience

## Quick Start

### Run All Stress Tests

```bash
# Using pytest
pytest tests/test_stress.py -v

# Using the standalone script
python scripts/stress_test.py

# Using shell scripts
./scripts/load_test.sh
# or on Windows
.\scripts\load_test.ps1
```

### Run Specific Test Suite

```bash
# API stress tests only
pytest tests/test_stress.py::TestAPIStress -v

# Report generation stress tests
pytest tests/test_stress.py::TestReportGenerationStress -v

# Database stress tests
pytest tests/test_stress.py::TestDatabaseStress -v

# Integration stress tests
pytest tests/test_stress.py::TestIntegrationStress -v
```

## Test Categories

### 1. API Endpoint Stress Tests

Tests the FastAPI endpoints under concurrent load:

- **Concurrent Health Checks**: Tests `/health` endpoint with multiple simultaneous requests
- **Concurrent Report Generation**: Tests report generation endpoint under load
- **Rate Limiting**: Validates rate limiting behavior under load

**Example:**
```bash
pytest tests/test_stress.py::TestAPIStress::test_concurrent_health_checks -v
```

### 2. Report Generation Stress Tests

Tests report generation functionality:

- **Large Watchlist Processing**: Tests with 100+ tickers
- **Concurrent Report Generations**: Multiple simultaneous report generations

**Example:**
```bash
pytest tests/test_stress.py::TestReportGenerationStress::test_large_watchlist_processing -v
```

### 3. Database Query Stress Tests

Tests Firestore database operations:

- **Concurrent Firestore Reads**: Multiple simultaneous read operations
- **Large Dataset Query Performance**: Query performance with 1000+ reports

**Example:**
```bash
pytest tests/test_stress.py::TestDatabaseStress::test_concurrent_firestore_reads -v
```

### 4. Integration Stress Tests

Tests complete workflows:

- **Full Workflow Under Load**: Complete generate → save → retrieve workflow

**Example:**
```bash
pytest tests/test_stress.py::TestIntegrationStress::test_full_workflow_under_load -v
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:8000` | API base URL |
| `CONCURRENT_REQUESTS` | `10` | Number of concurrent requests |
| `MAX_REQUESTS` | `100` | Maximum number of requests |
| `LARGE_WATCHLIST_SIZE` | `100` | Size of large watchlist for testing |

### Command Line Options

The standalone stress test script (`scripts/stress_test.py`) supports:

```bash
python scripts/stress_test.py \
    --base-url http://localhost:8000 \
    --concurrent 50 \
    --requests 100 \
    --suite all \
    --output report.json \
    --format json
```

Options:
- `--base-url`: Base URL for API (default: http://localhost:8000)
- `--concurrent`: Number of concurrent requests (default: 10)
- `--requests`: Number of requests per test (default: 10)
- `--suite`: Test suite to run: `api` or `all` (default: all)
- `--output`: Output file path for report
- `--format`: Report format: `json` or `csv` (default: json)

## Using Shell Scripts

### Bash (Linux/Mac)

```bash
# Basic usage
./scripts/load_test.sh

# With custom options
./scripts/load_test.sh \
    --base-url http://localhost:8000 \
    --concurrent 50 \
    --requests 100 \
    --suite api \
    --output report.json \
    --format json
```

### PowerShell (Windows)

```powershell
# Basic usage
.\scripts\load_test.ps1

# With custom options
.\scripts\load_test.ps1 `
    -BaseUrl http://localhost:8000 `
    -Concurrent 50 `
    -Requests 100 `
    -Suite api `
    -Output report.json `
    -Format json
```

## Performance Metrics

The stress tests collect the following metrics:

- **Total Requests**: Number of requests made
- **Successful Requests**: Number of successful responses
- **Failed Requests**: Number of failed responses
- **Success Rate**: Percentage of successful requests
- **Total Time**: Total time for all requests
- **Average Response Time**: Average response time
- **Min/Max Response Time**: Minimum and maximum response times
- **Requests Per Second**: Throughput metric

## Report Generation

### JSON Report

```bash
python scripts/stress_test.py --output report.json --format json
```

The JSON report includes:
- Summary information
- Timestamp
- Detailed metrics for each test

### CSV Report

```bash
python scripts/stress_test.py --output report.csv --format csv
```

The CSV report includes a row for each test with all metrics.

## Best Practices

1. **Start Small**: Begin with low concurrency (10-20 requests) and gradually increase**
2. **Monitor Resources**: Watch CPU, memory, and network usage during tests**
3. **Test Incrementally**: Test individual components before full integration tests**
4. **Use Production-like Data**: Use realistic data sizes and patterns**
5. **Set Timeouts**: Configure appropriate timeouts for long-running operations**

## Troubleshooting

### Tests Failing Due to Rate Limiting

If tests fail due to rate limiting, reduce the concurrency:

```bash
CONCURRENT_REQUESTS=5 pytest tests/test_stress.py -v
```

### API Not Responding

Ensure the API server is running:

```bash
# Check if API is running
curl http://localhost:8000/health

# Start API server if needed
uvicorn app.main:app --reload
```

### Memory Issues

If you encounter memory issues with large tests, reduce the number of concurrent requests or use smaller datasets.

## Continuous Integration

To integrate stress tests into CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run Stress Tests
  run: |
    pytest tests/test_stress.py -v --tb=short
    python scripts/stress_test.py --suite api --output ci_report.json
```

## Performance Benchmarks

Expected performance metrics (may vary based on hardware):

- **Health Check**: < 100ms average response time
- **Report Generation**: < 30s for standard watchlist
- **Database Reads**: < 1s average response time
- **Concurrent Requests**: 80%+ success rate at 50 concurrent requests

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python Concurrent Futures](https://docs.python.org/3/library/concurrent.futures.html)


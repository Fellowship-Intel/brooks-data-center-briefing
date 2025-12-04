#!/bin/bash

# Run the FastAPI app locally
# Prerequisites:
# - Virtual environment activated
# - Environment variables set:
#   - GOOGLE_API_KEY or GEMINI_API_KEY
#   - GOOGLE_APPLICATION_CREDENTIALS
#   - GCP_PROJECT_ID (optional, defaults to "mikebrooks")
#   - REPORTS_BUCKET_NAME

echo "🚀 Starting FastAPI server locally..."
echo ""

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found. Installing from requirements.txt..."
    pip install -r requirements.txt
fi

# Run the FastAPI app
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

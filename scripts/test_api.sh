#!/bin/bash

# Test script for FastAPI endpoints
# Prerequisites: API should be running on http://localhost:8000

API_URL="http://localhost:8000"
TRADING_DATE=$(date +%Y-%m-%d)

echo "🧪 Testing FastAPI endpoints"
echo "================================"
echo ""

# Test 1: Generate a report using dummy data
echo "1️⃣  Generating report with dummy data (POST /reports/generate)..."
echo ""
RESPONSE=$(curl -s -X POST "${API_URL}/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{}')

if [ $? -eq 0 ]; then
    echo "✅ Report generated successfully!"
    echo "Response:"
    echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
    echo ""
    
    # Extract trading_date from response if available
    EXTRACTED_DATE=$(echo "$RESPONSE" | grep -o '"trading_date":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$EXTRACTED_DATE" ]; then
        TRADING_DATE="$EXTRACTED_DATE"
        echo "📅 Using trading_date from response: $TRADING_DATE"
    else
        echo "📅 Using today's date: $TRADING_DATE"
    fi
else
    echo "❌ Failed to generate report"
    exit 1
fi

echo ""
echo "================================"
echo ""

# Test 2: Fetch the report
echo "2️⃣  Fetching report for $TRADING_DATE (GET /reports/{trading_date})..."
echo ""
curl -s "${API_URL}/reports/${TRADING_DATE}" | python -m json.tool 2>/dev/null || curl -s "${API_URL}/reports/${TRADING_DATE}"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Report fetched successfully!"
else
    echo ""
    echo "❌ Failed to fetch report"
fi

echo ""
echo "================================"
echo ""

# Test 3: Fetch audio metadata
echo "3️⃣  Fetching audio metadata for $TRADING_DATE (GET /reports/{trading_date}/audio)..."
echo ""
curl -s "${API_URL}/reports/${TRADING_DATE}/audio" | python -m json.tool 2>/dev/null || curl -s "${API_URL}/reports/${TRADING_DATE}/audio"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Audio metadata fetched successfully!"
else
    echo ""
    echo "❌ Failed to fetch audio metadata (this is OK if audio hasn't been generated yet)"
fi

echo ""
echo "================================"
echo "✅ Testing complete!"


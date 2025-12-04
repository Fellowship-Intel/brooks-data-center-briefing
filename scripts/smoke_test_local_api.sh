#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "🔍 Hitting POST /reports/generate..."

curl -sS -X POST "${BASE_URL}/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.' || {
    echo "❌ /reports/generate failed"
    exit 1
  }

TODAY="$(date +%F)"

echo
echo "🔍 Hitting GET /reports/${TODAY}..."

curl -sS "${BASE_URL}/reports/${TODAY}" | jq '.' || {
  echo "❌ /reports/{trading_date} failed"
  exit 1
}

echo
echo "🔍 Hitting GET /reports/${TODAY}/audio..."

curl -sS "${BASE_URL}/reports/${TODAY}/audio" | jq '.' || {
  echo "❌ /reports/{trading_date}/audio failed (might be fine if TTS failed)"
  exit 1
}

echo
echo "✅ Local API smoke test complete."


#!/usr/bin/env bash

set -euo pipefail

BASE="${BASE:-https://michael-brooks-report-api-XXXXX-uc.a.run.app}"

if [ "${BASE}" = "https://michael-brooks-report-api-XXXXX-uc.a.run.app" ]; then
    echo "⚠️  Warning: BASE URL is still set to placeholder value"
    echo "   Set it with: export BASE=https://your-actual-url.a.run.app"
    echo "   Or pass it as: BASE=https://your-url ./scripts/smoke_test_cloud_run.sh"
    echo ""
    read -p "Continue with placeholder? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🔍 Testing Cloud Run deployment at: ${BASE}"
echo ""

echo "🔍 Hitting POST /reports/generate..."

curl -sS -X POST "${BASE}/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.' || {
    echo "❌ /reports/generate failed"
    exit 1
  }

TODAY="$(date +%F)"

echo
echo "🔍 Hitting GET /reports/${TODAY}..."

curl -sS "${BASE}/reports/${TODAY}" | jq '.' || {
    echo "❌ /reports/{trading_date} failed"
    exit 1
  }

echo
echo "🔍 Hitting GET /reports/${TODAY}/audio..."

curl -sS "${BASE}/reports/${TODAY}/audio" | jq '.' || {
    echo "❌ /reports/{trading_date}/audio failed (might be fine if TTS failed)"
    exit 1
  }

echo
echo "✅ Cloud Run smoke test complete."


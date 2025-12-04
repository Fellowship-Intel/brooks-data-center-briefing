#!/usr/bin/env bash

# Check Cloud Run service logs
# Usage: ./scripts/check_logs.sh [api|ui|both]

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-mikebrooks}"
REGION="${GCP_REGION:-us-central1}"
API_SERVICE="${API_SERVICE_NAME:-brooks-briefing-api}"
UI_SERVICE="${UI_SERVICE_NAME:-brooks-briefing-ui}"
LIMIT="${LOG_LIMIT:-50}"

SERVICE="${1:-both}"

echo "📋 Reading Cloud Run logs"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Limit: ${LIMIT} entries"
echo ""

if [ "${SERVICE}" = "api" ] || [ "${SERVICE}" = "both" ]; then
    echo "🔍 Reading API service logs (${API_SERVICE})..."
    gcloud logs read \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --service="${API_SERVICE}" \
        --limit="${LIMIT}" || {
        echo "❌ Failed to read API logs"
        exit 1
    }
    echo ""
fi

if [ "${SERVICE}" = "ui" ] || [ "${SERVICE}" = "both" ]; then
    echo "🔍 Reading UI service logs (${UI_SERVICE})..."
    gcloud logs read \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --service="${UI_SERVICE}" \
        --limit="${LIMIT}" || {
        echo "❌ Failed to read UI logs"
        exit 1
    }
    echo ""
fi

echo "✅ Log check complete"


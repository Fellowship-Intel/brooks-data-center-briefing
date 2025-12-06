#!/bin/bash
# scripts/deploy-config.sh
# Syncs local secrets to GCP Secret Manager

set -e

PROJECT_ID=""
REGION="us-central1"

# Check dependencies
if ! command -v gcloud &> /dev/null; then
    echo "gcloud CLI is required."
    exit 1
fi

if [ -z "$PROJECT_ID" ]; then
    echo "Please set PROJECT_ID in the script or pass as env var."
    exit 1
fi

echo "Syncing secrets to GCP Secret Manager for project $PROJECT_ID..."

# Function to create or update a secret
sync_secret() {
    local key=$1
    local value=$2
    
    # Check if secret exists
    if ! gcloud secrets describe "$key" --project="$PROJECT_ID" &>/dev/null; then
        echo "Creating secret $key..."
        gcloud secrets create "$key" --replication-policy="automatic" --project="$PROJECT_ID"
    fi
    
    echo "Updating secret $key..."
    # Add new version
    echo -n "$value" | gcloud secrets versions add "$key" --data-file=- --project="$PROJECT_ID"
}

# Example usage: Read from .env.production if it exists
if [ -f .env.production ]; then
    echo "Reading from .env.production..."
    while IFS='=' read -r key value; do
        # Ignore comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        
        sync_secret "$key" "$value"
    done < .env.production
else
    echo "No .env.production file found. Skipping bulk sync."
    echo "Usage hint: Create .env.production with KEY=VALUE pairs."
fi

echo "Done."

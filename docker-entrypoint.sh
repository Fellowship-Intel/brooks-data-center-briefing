#!/bin/bash
set -e

# Get port from environment variable, default to 8080
PORT=${PORT:-8080}

# Run Streamlit with the specified port and address
exec streamlit run app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.headless=true


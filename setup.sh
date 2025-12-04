#!/bin/bash
# Setup script for web deployment

echo "Setting up Brooks Data Center Briefing for web deployment..."

# Create .streamlit directory if it doesn't exist
mkdir -p .streamlit

# Copy secrets example if secrets.toml doesn't exist
if [ ! -f .streamlit/secrets.toml ]; then
    if [ -f .streamlit/secrets.toml.example ]; then
        cp .streamlit/secrets.toml.example .streamlit/secrets.toml
        echo "Created .streamlit/secrets.toml from example"
        echo "Please edit .streamlit/secrets.toml and add your GEMINI_API_KEY"
    fi
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Add your GEMINI_API_KEY to .streamlit/secrets.toml (for local) or platform secrets (for deployment)"
echo "2. Test locally: streamlit run app.py"
echo "3. Deploy to Streamlit Cloud: https://share.streamlit.io"


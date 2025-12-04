FROM python:3.11-slim

# Install system deps (optional but handy for many libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Cloud Run expects the service to listen on $PORT (default 8080)
ENV PORT=8080

# Default command: start FastAPI with uvicorn
# Use shell form to allow PORT env var expansion
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}

# Setup Guide

This guide will help you get the Brooks Data Center Daily Briefing application up and running.

## Prerequisites

- **Git** - [Download Git](https://git-scm.com/downloads)
- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Google Cloud SDK** (for deployment) - [Install gcloud CLI](https://cloud.google.com/sdk/docs/install)
- **Google Gemini API Key** - [Get one here](https://ai.google.dev/)

## Step 1: Clone the Repository

```bash
# Navigate to your development folder
cd C:\Dev

# Clone the repository
git clone https://github.com/Fellowship-Intel/brooks-data-center-briefing.git brooks

# Navigate into the new folder
cd brooks
```

**Alternative locations:**
```bash
# Or clone to a different location
cd ~/projects  # Linux/Mac
git clone https://github.com/Fellowship-Intel/brooks-data-center-briefing.git brooks
cd brooks
```

## Step 2: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Or use a virtual environment (recommended):**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Set Up Authentication

### Option 1: GCP Service Account (Recommended for Production)

1. Download your service account JSON key file
2. Place it at `.secrets/app-backend-sa.json`
3. Set environment variables:

**Windows (PowerShell):**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="$PWD\.secrets\app-backend-sa.json"
$env:GCP_PROJECT_ID="mikebrooks"
```

**Linux/Mac:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/.secrets/app-backend-sa.json"
export GCP_PROJECT_ID="mikebrooks"
```

### Option 2: API Key (Simpler for Development)

**Create a `.env` file:**
```bash
# Create .env file
echo GEMINI_API_KEY=your_api_key_here > .env
```

**Or set as environment variable:**

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY=your_api_key_here
```

## Step 4: Run the Application

### Streamlit Web App (Recommended)

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501` (or port 8080 if configured).

### Local Terminal Version (No Browser)

```bash
python run_local.py
```

Runs entirely in the terminal - no ports or browser needed.

### FastAPI Backend Only

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or use the script
.\scripts\run_api_locally.ps1  # Windows
./scripts/run_api_locally.sh    # Linux/Mac
```

## Step 5: Verify Installation

1. ✅ App starts without errors
2. ✅ Can generate a report
3. ✅ Market data loads correctly
4. ✅ Chat interface works

## Next Steps

- **Deploy to Cloud Run**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Configure Watchlist**: Edit `python_app/constants.py` to customize your watchlist
- **Set Up Scheduled Reports**: See [SCHEDULER_SETUP.md](SCHEDULER_SETUP.md)

## Troubleshooting

### "Module not found" errors
- Make sure you've activated your virtual environment
- Run `pip install -r requirements.txt` again

### "GEMINI_API_KEY not found"
- Check your `.env` file exists and contains the key
- Or verify environment variables are set correctly

### Port already in use
- Streamlit: Change port in `.streamlit/config.toml` or use `--server.port=8502`
- FastAPI: Use `--port 8001` or another available port

### GCP Authentication Issues
- Verify service account file path is correct
- Check that `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set
- Ensure service account has necessary permissions

## Additional Resources

- [Python Setup Guide](SETUP_PYTHON.md)
- [Installation Guide](INSTALL_AND_RUN.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [GitHub Setup](GITHUB_SETUP.md)


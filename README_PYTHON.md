# Brooks Data Center Daily Briefing - Python Version

This is a Python port of the TypeScript/React application that generates daily trading reports for data center sector stocks using Google's Gemini AI.

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Google Gemini API Key ([Get one here](https://ai.google.dev/))

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up authentication:**
   
   The app supports two authentication methods (in priority order):
   
   **Option 1: GCP Service Account** (Recommended for production)
   ```powershell
   # Windows (PowerShell):
   $env:GOOGLE_APPLICATION_CREDENTIALS="$PWD\.secrets\app-backend-sa.json"
   $env:GCP_PROJECT_ID="mikebrooks"
   
   # Linux/Mac:
   export GOOGLE_APPLICATION_CREDENTIALS="$PWD/.secrets/app-backend-sa.json"
   export GCP_PROJECT_ID="mikebrooks"
   ```
   
   Place your service account JSON file at `.secrets/app-backend-sa.json`
   
   **Option 2: API Key** (Simpler for development)
   ```bash
   # Linux/Mac:
   export GEMINI_API_KEY=your_api_key_here
   
   # Windows (PowerShell):
   $env:GEMINI_API_KEY="your_api_key_here"
   
   # Windows (Command Prompt):
   set GEMINI_API_KEY=your_api_key_here
   ```
   
   **Option 3: Create a .env file** (for API key)
   ```bash
   echo GEMINI_API_KEY=your_api_key_here > .env
   ```
   
   **Note**: If using `run.ps1` on Windows, it will automatically set up GCP credentials if the service account file exists.

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

The app will automatically open in your browser at `http://localhost:8501`

## Features

- 📊 **Automated Daily Reports**: Generate comprehensive trading reports with AI
- 📈 **Market Data Visualization**: Interactive charts for top movers
- 💬 **Interactive Q&A**: Chat with the AI analyst about your reports
- 🔍 **Auto Data Fetching**: Automatically fetches market data via Google Search
- 🎧 **Audio Reports**: TTS-ready audio briefing scripts
- 🎨 **Modern UI**: Clean, dark-themed interface built with Streamlit

## Project Structure

```
python_app/
├── __init__.py
├── types.py              # Data models (dataclasses)
├── constants.py          # System instructions and configuration
├── services/
│   ├── __init__.py
│   └── gemini_service.py # Gemini AI integration
└── README.md

app.py                    # Main Streamlit application
requirements.txt          # Python dependencies
README_PYTHON.md         # This file
```

## Usage Guide

### Generating a Report

1. **Auto-Generated on Start**: The app automatically generates a report using default settings when you first launch it.

2. **Create Custom Report**: 
   - Click "🔄 New Report" button
   - Fill in the form:
     - Trading Date
     - Tickers Tracked (comma-separated, must include SMCI, CRVW, NBIS, IREN)
     - Market Data JSON (optional - leave empty `[]` to auto-fetch)
     - News JSON (optional - leave empty `[]` to auto-fetch)
     - Macro Context
     - Constraints/Notes
   - Click "Generate Daily Briefing Package"

### Report Sections

- **Top Movers Tab**: View charts and mini-reports for the top 3 movers
- **Deep Dive Tab**: In-depth analysis of core tickers (SMCI, CRVW, NBIS, IREN)
- **Full Narrative Tab**: Complete written report

### Chat Interface

The sidebar chat allows you to:
- Ask follow-up questions about the report
- Inquire about specific tickers
- Get more context on market movements

## Configuration

### Core Tickers

The app always tracks these four core tickers (defined in `python_app/constants.py`):
- SMCI
- CRVW
- NBIS
- IREN

You can modify the default ticker list in `python_app/constants.py`:

```python
tickers_tracked=[
    "EQIX", "DLR", "AMZN", "MSFT", "NVDA", "SMCI", 
    "IRM", "GDS", "CRVW", "NBIS", "IREN"
]
```

### System Instructions

The AI behavior is controlled by system instructions in `python_app/constants.py`. This defines how the AI analyzes data and generates reports.

## Troubleshooting

### Authentication Issues
- **Error**: "GEMINI_API_KEY or API_KEY must be set, or GOOGLE_APPLICATION_CREDENTIALS must point to a valid service account JSON file"
- **Solution**: 
  - For service account: Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account JSON file at `.secrets/app-backend-sa.json`
  - For API key: Make sure your API key is set correctly (see Installation step 2)
  - The app will try service account first, then fall back to API key

### Import Errors
- **Error**: "No module named 'python_app'"
- **Solution**: Run the app from the project root directory:
  ```bash
  cd /path/to/project
  streamlit run app.py
  ```

### Missing Dependencies
- **Error**: "No module named 'streamlit'" or similar
- **Solution**: Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### JSON Parsing Errors
- **Error**: "Invalid JSON in Market Data JSON"
- **Solution**: 
  - Leave Market Data and News JSON fields empty (`[]`) to auto-fetch
  - Or ensure your JSON is valid - use `[]` for empty arrays

### Model/API Errors
- **Error**: API rate limits or model not found
- **Solution**: 
  - Check your Gemini API key is valid
  - Ensure you have API quota remaining
  - The model name may need adjustment in `python_app/services/gemini_service.py`

## Advanced Usage

### Custom Data Format

Market Data JSON format:
```json
[
  {
    "ticker": "NVDA",
    "company_name": "NVIDIA Corporation",
    "previous_close": 125.50,
    "open": 126.00,
    "high": 128.50,
    "low": 125.00,
    "close": 127.25,
    "volume": 50000000,
    "average_volume": 40000000,
    "percent_change": 1.39,
    "intraday_range": "$125.00 - $128.50",
    "market_cap": "3.1T"
  }
]
```

News JSON format:
```json
[
  {
    "ticker": "NVDA",
    "headline": "NVIDIA Announces New AI Chip",
    "summary": "NVIDIA unveiled its latest AI accelerator...",
    "source": "TechCrunch",
    "time": "2025-01-15T10:00:00Z",
    "sentiment": "positive"
  }
]
```

## Differences from TypeScript Version

1. **UI Framework**: Uses Streamlit instead of React
2. **Audio Player**: Text display only (no built-in TTS)
3. **Package Management**: Uses pip/requirements.txt instead of npm/package.json
4. **Type System**: Uses Python dataclasses instead of TypeScript interfaces

## Requirements

- `streamlit>=1.28.0` - Web UI framework
- `google-generativeai>=0.3.0` - Gemini AI SDK
- `google-auth>=2.0.0` - GCP service account authentication
- `pandas>=2.0.0` - Data processing for charts
- `python-dotenv>=1.0.0` - Environment variable loading (optional)

## License

Same as the original TypeScript/React version.

## Support

For issues or questions, refer to the original TypeScript version's documentation or create an issue in the repository.




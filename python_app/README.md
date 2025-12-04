# Brooks Data Center Daily Briefing - Python Version

A Python application that generates daily trading reports for data center sector stocks using Google's Gemini AI.

## Features

- 📊 **Daily Report Generation**: Automated daily briefing with market data analysis
- 🤖 **AI-Powered Analysis**: Uses Google Gemini AI to analyze market data and news
- 💬 **Interactive Q&A**: Chat interface for follow-up questions about the reports
- 📈 **Market Data Visualization**: Charts and graphs for top movers
- 🎧 **Audio Reports**: Text-to-speech ready audio briefing scripts
- 🔍 **Auto Data Fetching**: Automatically fetches market data via Google Search if not provided

## Prerequisites

- Python 3.8 or higher
- Google Gemini API Key ([Get one here](https://ai.google.dev/))

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up authentication (choose one method):
   
   **Method 1: GCP Service Account** (Recommended)
   ```powershell
   # Windows (PowerShell):
   $env:GOOGLE_APPLICATION_CREDENTIALS="$PWD\.secrets\app-backend-sa.json"
   $env:GCP_PROJECT_ID="mikebrooks"
   
   # Linux/Mac:
   export GOOGLE_APPLICATION_CREDENTIALS="$PWD/.secrets/app-backend-sa.json"
   export GCP_PROJECT_ID="mikebrooks"
   ```
   Place your service account JSON file at `.secrets/app-backend-sa.json`
   
   **Method 2: API Key**
   ```bash
   # On Linux/Mac:
   export GEMINI_API_KEY=your_api_key_here
   
   # On Windows:
   set GEMINI_API_KEY=your_api_key_here
   
   # Or create a .env file:
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```
   
   The app will automatically use service account if available, otherwise fall back to API key.

## Usage

Run the Streamlit application:

```bash
streamlit run app.py
```

The app will open in your default web browser. It will automatically generate a report on startup, or you can create a new one using the input form.

## Project Structure

```
python_app/
├── __init__.py
├── types.py              # Data models and type definitions
├── constants.py          # System instructions and sample data
├── services/
│   ├── __init__.py
│   └── gemini_service.py # Gemini AI integration
└── README.md

app.py                    # Main Streamlit application
requirements.txt          # Python dependencies
```

## Configuration

The app uses default tickers that must always include: SMCI, CRVW, NBIS, IREN. You can modify these in `python_app/constants.py`.

## Features in Detail

### Input Form
- Enter trading date
- Specify tickers to track
- Provide market data JSON (optional - will auto-fetch if empty)
- Provide news JSON (optional - will auto-fetch if empty)
- Add macro context and constraints

### Report View
- **Top Movers**: Charts and mini-reports for top 3 movers
- **Deep Dive**: In-depth analysis of core tickers (SMCI, CRVW, NBIS, IREN)
- **Full Narrative**: Complete written report

### Chat Interface
- Ask follow-up questions about the generated report
- Maintains context from the original report generation

## Notes

- The app requires an internet connection for AI processing and optional data fetching
- Audio reports are provided as text scripts - you'll need to use a TTS service separately
- Market data charts require pandas for data processing

## Troubleshooting

**Authentication Error**: 
- For service account: Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid JSON file
- For API key: Make sure `GEMINI_API_KEY` is set correctly in your environment
- The app supports both methods and will automatically choose the best available option

**Import Errors**: Ensure you're running the app from the project root directory.

**Missing Dependencies**: Run `pip install -r requirements.txt` to install all required packages.

## License

Same as the original TypeScript/React version.




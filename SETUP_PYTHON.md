# Python Version Setup Guide

This directory contains a Python port of the TypeScript/React Brooks Data Center Daily Briefing application.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key:**
   ```bash
   # Create a .env file
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   
   # Or set as environment variable
   export GEMINI_API_KEY=your_api_key_here
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

## Project Structure

```
python_app/
├── __init__.py
├── types.py              # Data models (dataclasses)
├── constants.py          # System instructions and config
├── utils.py              # Helper functions for data conversion
└── services/
    ├── __init__.py
    └── gemini_service.py # Gemini AI integration

app.py                    # Main Streamlit application
requirements.txt          # Python dependencies
README_PYTHON.md         # Detailed documentation
```

## Key Differences from TypeScript Version

1. **UI Framework**: Streamlit instead of React
2. **Type System**: Python dataclasses instead of TypeScript interfaces  
3. **Package Management**: pip/requirements.txt instead of npm/package.json
4. **Audio**: Text display only (no built-in TTS player)

## Features

- ✅ Daily report generation with AI
- ✅ Market data visualization  
- ✅ Interactive Q&A chat
- ✅ Auto data fetching via Google Search
- ✅ Three report views (Top Movers, Deep Dive, Full Narrative)

For detailed documentation, see [README_PYTHON.md](README_PYTHON.md).






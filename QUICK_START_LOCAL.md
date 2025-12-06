# Quick Start - Run Locally (No Port, No Browser)

## The Problem
If you're seeing "port 8080" errors, you're trying to run the React/Vite web app which requires a web server. 

## The Solution
Use the **Python command-line version** instead - it runs completely locally with no ports or browsers needed.

## How to Run

### Option 1: Use the Batch File (Easiest)
Just double-click:
```
run.bat
```

### Option 2: Use PowerShell Script
Right-click `run.ps1` and select "Run with PowerShell"

### Option 3: Manual Command
```powershell
# If you have a virtual environment:
.\venv\Scripts\python.exe run_local.py

# Or use system Python:
python run_local.py
```

## What You'll See

The app will:
1. ✅ Generate the report in your terminal (no browser)
2. ✅ Display it formatted in the console
3. ✅ Save it to `output.txt`
4. ✅ Let you chat with the AI analyst

**No ports, no URLs, no browser needed!**

## Troubleshooting

### "Module not found" error
Install dependencies:
```powershell
.\venv\Scripts\python.exe -m pip install google-generativeai streamlit pandas python-dotenv
```

### "GEMINI_API_KEY not found"
Make sure your `.env` file exists with:
```
GEMINI_API_KEY=your_api_key_here
```

## Key Difference

| Command | What It Does | Port Needed? |
|---------|-------------|--------------|
| `npm run dev` | React web app | ✅ Yes (port 8080) |
| `streamlit run app.py` | Streamlit web app | ✅ Yes (port 8501) |
| `python run_local.py` | **Command-line app** | ❌ **No port!** |

Use `python run_local.py` or `run.bat` for the local version!


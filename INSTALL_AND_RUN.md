# Install and Run the Local Terminal Version

## The Problem
The full `requirements.txt` includes `streamlit` and `pyarrow` which require build tools. The **local terminal version doesn't need these**.

## Solution: Install Only What's Needed

### Step 1: Install Minimal Requirements

Run this command (it will skip the problematic packages):

```powershell
python -m pip install google-generativeai python-dotenv
```

Or use the minimal requirements file:

```powershell
python -m pip install -r requirements_local.txt
```

### Step 2: Verify Installation

Check if it installed:

```powershell
python -c "import google.generativeai; print('✓ Package installed')"
```

### Step 3: Run the App

```powershell
python run_local.py
```

## If Installation Still Fails

### Option 1: Try with --user flag
```powershell
python -m pip install --user google-generativeai python-dotenv
```

### Option 2: Try upgrading pip first
```powershell
python -m pip install --upgrade pip
python -m pip install google-generativeai python-dotenv
```

### Option 3: Use a Virtual Environment
```powershell
# Create venv
python -m venv venv_local

# Activate (if execution policy allows)
.\venv_local\Scripts\activate.ps1

# Or use directly
.\venv_local\Scripts\python.exe -m pip install google-generativeai python-dotenv
.\venv_local\Scripts\python.exe run_local.py
```

## What You Need

For the **local terminal version** (`run_local.py`), you only need:
- ✅ `google-generativeai` - For AI functionality
- ✅ `python-dotenv` - For .env file support (optional)

You do **NOT** need:
- ❌ `streamlit` - Only for web version
- ❌ `pyarrow` - Only for streamlit charts
- ❌ `pandas` - Only for streamlit charts

## Quick Test

After installing, test it:

```powershell
python -c "import google.generativeai; print('Ready to run!')"
python run_local.py
```

The app will run entirely in your terminal - no ports, no browser needed!


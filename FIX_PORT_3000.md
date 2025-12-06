# Fix "Connection Refused" on Port 8080

## The Problem

Port 8080 is used by the **React/Vite web app**, which requires:
- Node.js installed
- Dev server running (`npm run dev`)

## Solutions

### Option 1: Run the React App (If you have Node.js)

**Step 1: Install Node.js**
- Download from https://nodejs.org/ (LTS version)
- Install and restart terminal

**Step 2: Install dependencies**
```bash
npm install
```

**Step 3: Start the dev server**
```bash
npm run dev
```

**Step 4: Open browser**
- Go to `http://localhost:8080`

### Option 2: Use Flask App Instead (No Node.js needed!)

The Flask app runs on **port 5000** (not 3000) and doesn't need Node.js:

**Step 1: Install Python dependencies**
```bash
pip install -r requirements_flask.txt
```

**Step 2: Run Flask app**
```bash
python app_flask.py
```

**Step 3: Open browser**
- Go to `http://localhost:5000` (NOT 8080!)

### Option 3: Use Streamlit App

**Step 1: Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 2: Run Streamlit**
```bash
streamlit run app.py
```

**Step 3: Open browser**
- Go to `http://localhost:8501` (NOT 8080!)

### Option 4: Use Local Terminal Version

No ports needed at all:

```bash
python run_local.py
```

Runs entirely in terminal - no browser, no ports!

## Which App Should You Use?

| App | Port | Needs Node.js? | Command |
|-----|------|----------------|---------|
| React/Vite | 8080 | ✅ Yes | `npm run dev` |
| Flask | 5000 | ❌ No | `python app_flask.py` |
| Streamlit | 8501 | ❌ No | `streamlit run app.py` |
| Local Terminal | None | ❌ No | `python run_local.py` |

## Quick Fix

**If you don't have Node.js**, use one of these instead:

1. **Flask (Recommended for web):**
   ```bash
   python app_flask.py
   # Then visit http://localhost:5000
   ```

2. **Streamlit:**
   ```bash
   streamlit run app.py
   # Then visit http://localhost:8501
   ```

3. **Terminal (No browser):**
   ```bash
   python run_local.py
   ```

## Troubleshooting Port 8080

**If you want to use the React app:**

1. **Check if Node.js is installed:**
   ```bash
   node --version
   ```
   If not installed, download from nodejs.org

2. **Check if dev server is running:**
   - Look for a terminal running `npm run dev`
   - If not running, start it: `npm run dev`

3. **Check if port 8080 is in use:**
   ```powershell
   netstat -ano | findstr :8080
   ```
   If something else is using it (e.g., Streamlit backend), either:
   - Stop that process
   - Or change port in `vite.config.ts` (change `port: 8080` to another port)

## Recommended Solution

Since you don't have Node.js installed, **use the Flask app**:

```bash
pip install -r requirements_flask.txt
python app_flask.py
```

Then visit: **http://localhost:5000** (not 8080!)


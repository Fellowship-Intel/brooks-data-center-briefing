# How to Start the App

## The Error You're Seeing

**ERR_CONNECTION_REFUSED** means the development server isn't running. You need to start it first.

## Step 1: Install Node.js and npm

You need to install Node.js (which includes npm) to run the development server.

### Option A: Download from Official Website (Recommended)

1. **Download Node.js:**
   - Go to: https://nodejs.org/
   - Download the **LTS version** (Long Term Support)
   - Choose the Windows Installer (.msi) for your system (64-bit recommended)

2. **Install Node.js:**
   - Run the installer
   - Follow the installation wizard
   - **Important:** Make sure to check "Add to PATH" during installation
   - Restart your terminal/command prompt after installation

3. **Verify Installation:**
   Open a new terminal/PowerShell and run:
   ```powershell
   node --version
   npm --version
   ```
   You should see version numbers (e.g., `v20.10.0` and `10.2.3`)

### Option B: Using Chocolatey (If you have it)

```powershell
choco install nodejs
```

### Option C: Using Winget (Windows 10/11)

```powershell
winget install OpenJS.NodeJS.LTS
```

## Step 2: Install Project Dependencies

Once Node.js is installed, open a terminal in this project folder and run:

```powershell
npm install
```

This will install all required packages (React, Vite, etc.)

## Step 3: Start the Development Server

After dependencies are installed, start the server:

```powershell
npm run dev
```

You should see output like:
```
  VITE v6.2.0  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.x.x:3000/
```

## Step 4: Open in Browser

Once you see "Local: http://localhost:3000/", open your browser and go to:
```
http://localhost:3000
```

The app should now load!

## Troubleshooting

### "npm is not recognized"
- Node.js isn't installed or not in PATH
- Restart your terminal after installing Node.js
- Or restart your computer

### "Port 3000 is already in use"
- Another application is using port 3000
- Either stop that application or change the port in `vite.config.ts`

### "Cannot find module"
- Dependencies aren't installed
- Run `npm install` again

### Still having issues?
- Make sure you're in the project directory: `G:\My Drive\Cursor\Brooks`
- Check that `package.json` exists
- Verify Node.js is installed: `node --version`

## Quick Start Checklist

- [ ] Node.js installed (check with `node --version`)
- [ ] npm installed (check with `npm --version`)
- [ ] Dependencies installed (`npm install`)
- [ ] Dev server running (`npm run dev`)
- [ ] Browser open to `http://localhost:3000`

## Alternative: Use the Python Version

If you prefer not to install Node.js, you can use the Python/Streamlit version instead:

```powershell
# Make sure Python is installed
python --version

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

This will start on `http://localhost:8501` instead.


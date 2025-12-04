# Migration Guide: Moving from Google Drive to Local Folder

This guide will help you move the project from Google Drive (`G:\My Drive\Cursor\Brooks`) to a local folder (`C:\Dev\brooks`).

## Quick Migration (Automated)

Run the PowerShell migration script:

```powershell
.\migrate-to-local.ps1
```

This script will:
- ✅ Copy all project files to `C:\Dev\brooks`
- ✅ Exclude unnecessary files (venv, node_modules, __pycache__, etc.)
- ✅ Preserve important folders (.secrets, .streamlit, .vscode)
- ✅ Provide next steps

## Manual Migration

If you prefer to do it manually:

### Step 1: Create Target Directory

```powershell
# Create the Dev folder if it doesn't exist
New-Item -ItemType Directory -Path "C:\Dev" -Force

# Create the brooks folder
New-Item -ItemType Directory -Path "C:\Dev\brooks" -Force
```

### Step 2: Copy Project Files

**Option A: Using PowerShell (Recommended)**
```powershell
# Copy all files except large folders
Copy-Item -Path "G:\My Drive\Cursor\Brooks\*" -Destination "C:\Dev\brooks" -Recurse -Exclude "venv","node_modules","__pycache__",".git","dist","build"
```

**Option B: Using Robocopy (More Control)**
```powershell
robocopy "G:\My Drive\Cursor\Brooks" "C:\Dev\brooks" /E /XD venv node_modules __pycache__ .git dist build /XF *.pyc .DS_Store Thumbs.db
```

**Option C: Using Git Clone (If Repository Exists)**
```powershell
cd C:\Dev
git clone https://github.com/Fellowship-Intel/brooks-data-center-briefing.git brooks
cd brooks
```

### Step 3: Copy Important Folders

Make sure these folders are copied:
- `.secrets/` - Contains service account credentials
- `.streamlit/` - Streamlit configuration
- `.vscode/` - VS Code settings (optional)
- `.env` - Environment variables (if exists)

```powershell
# Copy .secrets folder (important!)
Copy-Item -Path "G:\My Drive\Cursor\Brooks\.secrets" -Destination "C:\Dev\brooks\.secrets" -Recurse -Force

# Copy .streamlit folder
Copy-Item -Path "G:\My Drive\Cursor\Brooks\.streamlit" -Destination "C:\Dev\brooks\.streamlit" -Recurse -Force

# Copy .env if it exists
if (Test-Path "G:\My Drive\Cursor\Brooks\.env") {
    Copy-Item -Path "G:\My Drive\Cursor\Brooks\.env" -Destination "C:\Dev\brooks\.env" -Force
}
```

### Step 4: Navigate to New Location

```powershell
cd C:\Dev\brooks
```

### Step 5: Verify Setup

```powershell
# Check that important files exist
Test-Path .secrets\app-backend-sa.json
Test-Path app.py
Test-Path requirements.txt
```

### Step 6: Set Up Environment Variables

```powershell
# Set GCP credentials path (relative to new location)
$env:GOOGLE_APPLICATION_CREDENTIALS="$PWD\.secrets\app-backend-sa.json"
$env:GCP_PROJECT_ID="mikebrooks"

# Or create a setup script
@"
`$env:GOOGLE_APPLICATION_CREDENTIALS="`$PWD\.secrets\app-backend-sa.json"
`$env:GCP_PROJECT_ID="mikebrooks"
"@ | Out-File -FilePath "setup-env.ps1" -Encoding UTF8
```

### Step 7: Install Dependencies (If Needed)

```powershell
# Create new virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 8: Test the Application

```powershell
# Run Streamlit
streamlit run app.py

# Or run terminal version
python run_local.py
```

## Update VS Code Workspace

If you use VS Code:

1. **Open the new folder:**
   - File → Open Folder → Select `C:\Dev\brooks`

2. **Update launch.json** (if needed):
   - The `${workspaceFolder}` variable will automatically point to the new location
   - No changes needed if using relative paths

## Verify Everything Works

Run the setup check script:

```powershell
.\setup-check.ps1
```

## Important Notes

- **Service Account File**: Make sure `.secrets/app-backend-sa.json` is copied - this is critical!
- **Environment Variables**: Update any scripts that reference the old Google Drive path
- **Git Repository**: If you have a git repo, you may want to re-clone it in the new location
- **Virtual Environment**: Consider creating a fresh venv in the new location

## Troubleshooting

### "Module not found" errors
- Make sure you're in the correct directory: `cd C:\Dev\brooks`
- Reinstall dependencies: `pip install -r requirements.txt`

### "Credentials not found" errors
- Verify `.secrets/app-backend-sa.json` exists
- Check environment variable: `$env:GOOGLE_APPLICATION_CREDENTIALS`

### Port conflicts
- The app should work the same way in the new location
- Check `.streamlit/config.toml` for port settings

## After Migration

Once everything is working in the new location:

1. ✅ Test the app: `streamlit run app.py`
2. ✅ Verify reports generate correctly
3. ✅ Check that GCP connections work
4. ✅ Update any shortcuts or scripts that reference the old path

You can now safely delete the old Google Drive folder if desired (after verifying everything works).


# GitHub Repository Setup Guide

This guide will help you create and set up a GitHub repository for the Brooks Data Center Daily Briefing application.

## Quick Setup (Automated)

Run the PowerShell script:

```powershell
.\setup-github-repo.ps1
```

This script will:
- ✅ Check if Git is installed
- ✅ Initialize git repository (if needed)
- ✅ Stage all files
- ✅ Guide you through creating the GitHub repository
- ✅ Help you connect the remote

## Manual Setup Steps

### Step 1: Install Git (if not installed)

**Windows:**
- Download from: https://git-scm.com/download/win
- Or use winget: `winget install Git.Git`

**Verify installation:**
```powershell
git --version
```

### Step 2: Create Repository on GitHub

1. **Go to GitHub:** https://github.com/new
2. **Repository Settings:**
   - **Repository name:** `brooks-data-center-briefing` (or your preferred name)
   - **Description:** `Daily trading briefing for data center sector stocks using Google Gemini AI`
   - **Visibility:** Choose Public or Private
   - **⚠️ Important:** Do NOT check:
     - ❌ Add a README file
     - ❌ Add .gitignore
     - ❌ Choose a license
   - Click **"Create repository"**

### Step 3: Initialize Local Git Repository

```powershell
# Navigate to project directory (if not already there)
cd "G:\My Drive\Cursor\Brooks"

# Initialize git
git init

# Create main branch
git checkout -b main
# Or rename existing branch: git branch -M main
```

### Step 4: Stage and Commit Files

```powershell
# Stage all files
git add .

# Create initial commit
git commit -m "Initial commit: Brooks Data Center Daily Briefing"
```

### Step 5: Connect to GitHub

```powershell
# Add remote (replace with your actual repository URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Verify remote
git remote -v
```

### Step 6: Push to GitHub

```powershell
# Push to GitHub
git push -u origin main
```

You may be prompted for GitHub credentials. Use a Personal Access Token (not your password).

## Update Package.json

After creating the repository, update `package.json` with the repository URL:

```json
{
  "repository": {
    "type": "git",
    "url": "https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
  }
}
```

## GitHub Personal Access Token

If you need to authenticate:

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (full control of private repositories)
4. Generate and copy the token
5. Use this token as your password when pushing

## Recommended Repository Settings

After creating the repository:

1. **Add topics/tags:**
   - `streamlit`
   - `python`
   - `trading`
   - `data-center`
   - `gemini-ai`
   - `market-analysis`

2. **Add description:**
   ```
   Daily trading briefing application for data center sector stocks. 
   Generates AI-powered reports using Google Gemini, with market data 
   visualization and interactive Q&A.
   ```

3. **Enable GitHub Pages** (optional, for documentation):
   - Settings → Pages
   - Source: `main` branch, `/docs` folder

## Troubleshooting

### "Git is not recognized"
- Install Git from https://git-scm.com/download/win
- Restart your terminal after installation

### "Authentication failed"
- Use a Personal Access Token instead of password
- Or set up SSH keys for authentication

### "Remote origin already exists"
```powershell
# Remove existing remote
git remote remove origin

# Add new remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### "Failed to push some refs"
```powershell
# If GitHub repo was initialized with files, pull first
git pull origin main --allow-unrelated-histories

# Then push
git push -u origin main
```

## Next Steps

After setting up the repository:

1. ✅ Update `DEPLOY_NOW.md` with your actual repository URL
2. ✅ Update `README_DEPLOYMENT.md` if needed
3. ✅ Consider adding a LICENSE file
4. ✅ Set up GitHub Actions for CI/CD (optional)
5. ✅ Configure branch protection rules (optional)

## Repository URL Template

Once created, your repository URL will be:
```
https://github.com/YOUR_USERNAME/brooks-data-center-briefing
```

Replace `YOUR_USERNAME` with your GitHub username.


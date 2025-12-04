# Create GitHub Repository - Quick Start

## 🚀 Fastest Way: Use GitHub Web Interface

### Step 1: Create Repository on GitHub

**Click this link to create a new repository:**
👉 **[Create New Repository on GitHub](https://github.com/new)**

### Step 2: Fill in Repository Details

**Repository Name:** `brooks-data-center-briefing`

**Description:** 
```
Daily trading briefing for data center sector stocks using Google Gemini AI
```

**Visibility:**
- ☑️ Public (recommended for open source)
- ☐ Private (if you want to keep it private)

**⚠️ IMPORTANT - Do NOT check any of these:**
- ❌ Add a README file
- ❌ Add .gitignore  
- ❌ Choose a license

**Click:** "Create repository"

### Step 3: Copy Your Repository URL

After creating, GitHub will show you a URL like:
```
https://github.com/YOUR_USERNAME/brooks-data-center-briefing.git
```

**Copy this URL** - you'll need it in the next step!

### Step 4: Run the Setup Script

Open PowerShell in this directory and run:

```powershell
.\setup-github-repo.ps1
```

When prompted, paste your repository URL.

### Step 5: Push Your Code

The script will guide you, or run manually:

```powershell
git push -u origin main
```

## ✅ Done!

Your code is now on GitHub! 🎉

## Alternative: Manual Setup

If you prefer to do it manually, see [GITHUB_SETUP.md](GITHUB_SETUP.md) for detailed instructions.


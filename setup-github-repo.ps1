# Setup GitHub Repository for Brooks Data Center Daily Briefing
# This script helps you initialize git and prepare for GitHub

Write-Host "🚀 Setting up GitHub repository for Brooks Data Center Daily Briefing" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "✅ Git is installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Git first:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "  2. Or install via winget: winget install Git.Git" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Check if already a git repository
if (Test-Path ".git") {
    Write-Host "⚠️  Git repository already initialized" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 0
    }
} else {
    Write-Host "📦 Initializing git repository..." -ForegroundColor Cyan
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
}

# Check current branch
$currentBranch = git branch --show-current 2>$null
if (-not $currentBranch) {
    Write-Host "🌿 Creating main branch..." -ForegroundColor Cyan
    git checkout -b main
} elseif ($currentBranch -ne "main") {
    Write-Host "🌿 Renaming branch to main..." -ForegroundColor Cyan
    git branch -M main
}

# Check for existing remote
$remoteUrl = git remote get-url origin 2>$null
if ($remoteUrl) {
    Write-Host "📡 Found existing remote: $remoteUrl" -ForegroundColor Yellow
    $change = Read-Host "Change remote URL? (y/n)"
    if ($change -eq "y") {
        $newUrl = Read-Host "Enter new GitHub repository URL (e.g., https://github.com/username/repo-name.git)"
        git remote set-url origin $newUrl
        Write-Host "✅ Remote URL updated" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "📡 No remote repository configured" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Create a new repository on GitHub:" -ForegroundColor White
    Write-Host "     - Go to https://github.com/new" -ForegroundColor Gray
    Write-Host "     - Repository name: brooks-data-center-briefing (or your preferred name)" -ForegroundColor Gray
    Write-Host "     - Description: Daily trading briefing for data center sector stocks" -ForegroundColor Gray
    Write-Host "     - Choose Public or Private" -ForegroundColor Gray
    Write-Host "     - DO NOT initialize with README, .gitignore, or license" -ForegroundColor Gray
    Write-Host "     - Click 'Create repository'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. After creating the repository, run:" -ForegroundColor White
    Write-Host "     git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git" -ForegroundColor Gray
    Write-Host ""
}

# Stage all files
Write-Host ""
Write-Host "📝 Staging files..." -ForegroundColor Cyan
git add .

# Check if there are changes to commit
$status = git status --porcelain
if ($status) {
    Write-Host "✅ Files staged" -ForegroundColor Green
    Write-Host ""
    $commit = Read-Host "Create initial commit? (y/n)"
    if ($commit -eq "y") {
        $message = Read-Host "Commit message (press Enter for default)"
        if (-not $message) {
            $message = "Initial commit: Brooks Data Center Daily Briefing"
        }
        git commit -m $message
        Write-Host "✅ Initial commit created" -ForegroundColor Green
    }
} else {
    Write-Host "ℹ️  No changes to commit" -ForegroundColor Yellow
}

# Check remote and provide push instructions
$remoteUrl = git remote get-url origin 2>$null
if ($remoteUrl) {
    Write-Host ""
    Write-Host "🎯 Ready to push to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Run the following command to push:" -ForegroundColor Cyan
    Write-Host "  git push -u origin main" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "📋 Summary:" -ForegroundColor Cyan
    Write-Host "  ✅ Git repository initialized" -ForegroundColor Green
    Write-Host "  ✅ Files staged" -ForegroundColor Green
    if ($commit -eq "y") {
        Write-Host "  ✅ Initial commit created" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "Next: Create repository on GitHub and add remote, then push!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✨ Setup complete!" -ForegroundColor Green


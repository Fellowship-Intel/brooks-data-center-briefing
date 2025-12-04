# Web App Deployment Guide

This guide covers deploying the Brooks Data Center Briefing app as a web application using Streamlit.

## Quick Deploy Options

### Option 1: Streamlit Cloud (Recommended - Easiest & Free)

Streamlit Cloud is the easiest way to deploy your Streamlit app for free.

#### Steps:

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository and branch
   - Set Main file path: `app.py`
   - Click "Deploy!"

3. **Add Secrets (API Key):**
   - In your app settings, go to "Secrets"
   - Add:
     ```toml
     GEMINI_API_KEY = "your_api_key_here"
     ```
   - Save and the app will automatically redeploy

4. **Your app is live!** 🎉
   - You'll get a URL like: `https://your-app-name.streamlit.app`

#### Requirements:
- ✅ GitHub account (free)
- ✅ Code pushed to GitHub
- ✅ `.streamlit/config.toml` file (already created)
- ✅ `requirements.txt` file (already exists)

### Option 2: Heroku

1. **Install Heroku CLI:**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create `Procfile`:**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

3. **Deploy:**
   ```bash
   heroku login
   heroku create your-app-name
   heroku config:set GEMINI_API_KEY=your_api_key_here
   git push heroku main
   ```

### Option 3: Railway

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   ```

2. **Deploy:**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Set environment variable:**
   - In Railway dashboard, add `GEMINI_API_KEY`

### Option 4: Render

1. **Create account at [render.com](https://render.com)**

2. **Create new Web Service:**
   - Connect your GitHub repository
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - Add environment variable: `GEMINI_API_KEY`

3. **Deploy!**

### Option 5: Docker (Self-Hosted)

Use the existing Dockerfile for containerized deployment:

```bash
docker build -t brooks-briefing:latest .
docker run -d -p 8501:8501 -e GEMINI_API_KEY=your_key brooks-briefing:latest
```

## Pre-Deployment Checklist

- [ ] Code is pushed to GitHub (for Streamlit Cloud)
- [ ] `requirements.txt` is up to date
- [ ] `.streamlit/config.toml` exists
- [ ] API key is ready to add as secret/environment variable
- [ ] Tested locally: `streamlit run app.py`

## Environment Variables

All platforms require the `GEMINI_API_KEY` environment variable:

- **Streamlit Cloud**: Add in dashboard under "Secrets"
- **Heroku**: `heroku config:set GEMINI_API_KEY=your_key`
- **Railway**: Add in dashboard under "Variables"
- **Render**: Add in dashboard under "Environment"
- **Docker**: `-e GEMINI_API_KEY=your_key`

## Post-Deployment

1. ✅ Test the deployed app
2. ✅ Verify report generation works
3. ✅ Test chat interface
4. ✅ Check API usage in Google Cloud Console
5. ✅ Set up monitoring/alerts

## Troubleshooting

### App won't start
- Check logs in platform dashboard
- Verify `GEMINI_API_KEY` is set correctly
- Ensure `requirements.txt` has all dependencies

### Import errors
- Make sure all files are in the repository
- Check that `python_app/` directory structure is correct

### API errors
- Verify API key is valid
- Check API quota in Google Cloud Console
- Ensure API key has proper permissions

## Recommended: Streamlit Cloud

**Why Streamlit Cloud?**
- ✅ Free tier available
- ✅ Automatic deployments from GitHub
- ✅ Easy secret management
- ✅ Built for Streamlit apps
- ✅ No credit card required
- ✅ HTTPS by default

Get started: [share.streamlit.io](https://share.streamlit.io)


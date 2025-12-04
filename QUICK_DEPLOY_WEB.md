# Quick Web Deployment - Streamlit Cloud

Deploy your app to the web in 5 minutes!

## Step 1: Push to GitHub

If you haven't already:

```bash
git init
git add .
git commit -m "Ready for deployment"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Step 2: Deploy to Streamlit Cloud

1. **Go to [share.streamlit.io](https://share.streamlit.io)**
2. **Sign in with GitHub**
3. **Click "New app"**
4. **Fill in:**
   - Repository: Select your repo
   - Branch: `main`
   - Main file path: `app.py`
5. **Click "Deploy!"**

## Step 3: Add Your API Key

1. **In your app dashboard, click "Settings"**
2. **Go to "Secrets" tab**
3. **Add:**
   ```toml
   GEMINI_API_KEY = "your_api_key_here"
   ```
4. **Click "Save"** - App will auto-redeploy!

## Done! 🎉

Your app is now live at: `https://your-app-name.streamlit.app`

## What You Get

- ✅ Free hosting
- ✅ Automatic HTTPS
- ✅ Auto-deploy on git push
- ✅ Easy secret management
- ✅ No credit card needed

## Troubleshooting

**App won't start?**
- Check the logs in Streamlit Cloud dashboard
- Verify `GEMINI_API_KEY` is set in Secrets
- Make sure `requirements.txt` has all packages

**Import errors?**
- Ensure all files are committed to GitHub
- Check that `python_app/` directory is in the repo

That's it! Your app is now on the web! 🌐


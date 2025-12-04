# Deployment Guide - Web App

Your app is ready to deploy as a web application! Here are your options:

## 🚀 Recommended: Streamlit Cloud (Easiest)

**Free, automatic deployments, perfect for Streamlit apps**

### Quick Steps:

1. **Push code to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push
   ```

2. **Deploy:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repo → `app.py` as main file
   - Click "Deploy!"

3. **Add API Key:**
   - In app settings → "Secrets"
   - Add: `GEMINI_API_KEY = "your_key_here"`
   - Save (auto-redeploys)

**Done!** Your app is live at `https://your-app.streamlit.app`

See [QUICK_DEPLOY_WEB.md](QUICK_DEPLOY_WEB.md) for detailed steps.

## 📋 Files Created for Deployment

✅ `.streamlit/config.toml` - Streamlit configuration  
✅ `Procfile` - For Heroku/Railway  
✅ `runtime.txt` - Python version for Heroku  
✅ `packages.txt` - System packages (if needed)  
✅ `WEB_DEPLOYMENT.md` - Full deployment guide  
✅ `requirements.txt` - Python dependencies  

## 🌐 Other Deployment Options

### Heroku
```bash
heroku create your-app-name
heroku config:set GEMINI_API_KEY=your_key
git push heroku main
```

### Railway
```bash
railway login
railway init
railway up
# Add GEMINI_API_KEY in dashboard
```

### Render
- Connect GitHub repo
- Set build: `pip install -r requirements.txt`
- Set start: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
- Add `GEMINI_API_KEY` in environment variables

### Docker
```bash
docker build -t brooks-briefing .
docker run -d -p 8501:8501 -e GEMINI_API_KEY=your_key brooks-briefing
```

## ✅ Pre-Deployment Checklist

- [x] `requirements.txt` is ready
- [x] `.streamlit/config.toml` created
- [x] App handles secrets properly
- [ ] Code pushed to GitHub (for Streamlit Cloud)
- [ ] API key ready to add as secret

## 🔐 Security Notes

- API key is stored securely in platform secrets (not in code)
- Never commit `.env` or `.streamlit/secrets.toml` to git
- Set API key restrictions in Google Cloud Console
- Monitor API usage regularly

## 📚 Documentation

- **Quick Start**: [QUICK_DEPLOY_WEB.md](QUICK_DEPLOY_WEB.md)
- **Full Guide**: [WEB_DEPLOYMENT.md](WEB_DEPLOYMENT.md)
- **Troubleshooting**: Check platform logs if issues occur

## 🎯 Next Steps

1. Choose your platform (Streamlit Cloud recommended)
2. Follow the deployment steps
3. Add your API key as a secret
4. Test your deployed app!

Your app is production-ready! 🎉


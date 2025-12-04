# Flask Web App - Quick Reference

## Files Created

✅ `app_flask.py` - Main Flask application  
✅ `templates/` - HTML templates (base, input, report)  
✅ `static/` - CSS and JavaScript files  
✅ `requirements_flask.txt` - Flask dependencies  
✅ `FLASK_DEPLOYMENT.md` - Full deployment guide  
✅ `RUN_FLASK.md` - Quick start guide  

## Run Locally

```bash
# Install dependencies
pip install -r requirements_flask.txt

# Set environment variables (or use .env file)
export GEMINI_API_KEY=your_key_here
export FLASK_SECRET_KEY=your_secret_here

# Run the app
python app_flask.py
```

Visit: **http://localhost:5000**

## Features

- ✅ Full web interface (HTML/CSS/JS)
- ✅ Dark theme matching original design
- ✅ Report generation
- ✅ Interactive chat
- ✅ Tabbed report view (Top Movers, Deep Dive, Full Narrative)
- ✅ Auto-saves to `output.txt`

## Deployment

See [FLASK_DEPLOYMENT.md](FLASK_DEPLOYMENT.md) for:
- Heroku
- Railway  
- Render
- PythonAnywhere
- Docker

## Structure

```
app_flask.py
templates/
  ├── base.html
  ├── input.html
  └── report.html
static/
  ├── style.css
  └── app.js
```

Your Flask web app is ready to deploy! 🚀


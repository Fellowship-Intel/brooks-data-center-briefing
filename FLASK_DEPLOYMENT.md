# Flask Web App Deployment Guide

This guide covers deploying the Flask version of the Brooks Data Center Briefing app.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_flask.txt
```

### 2. Set Environment Variables

Create a `.env` file or set environment variables:

```bash
GEMINI_API_KEY=your_api_key_here
FLASK_SECRET_KEY=your-secret-key-here  # For production, use a strong random key
FLASK_DEBUG=False  # Set to True for development
PORT=5000  # Optional, defaults to 5000
```

### 3. Run Locally

```bash
python app_flask.py
```

The app will be available at `http://localhost:5000`

## Deployment Options

### Option 1: Heroku

1. **Create `Procfile`:**
   ```
   web: gunicorn app_flask:app --bind 0.0.0.0:$PORT
   ```

2. **Deploy:**
   ```bash
   heroku create your-app-name
   heroku config:set GEMINI_API_KEY=your_key
   heroku config:set FLASK_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   git push heroku main
   ```

### Option 2: Railway

1. **Deploy:**
   ```bash
   railway login
   railway init
   railway up
   ```

2. **Set environment variables in Railway dashboard:**
   - `GEMINI_API_KEY`
   - `FLASK_SECRET_KEY`
   - `PORT` (auto-set by Railway)

### Option 3: Render

1. **Create new Web Service:**
   - Connect GitHub repository
   - Build command: `pip install -r requirements_flask.txt`
   - Start command: `gunicorn app_flask:app --bind 0.0.0.0:$PORT`
   - Add environment variables:
     - `GEMINI_API_KEY`
     - `FLASK_SECRET_KEY`
     - `PORT` (auto-set by Render)

### Option 4: PythonAnywhere

1. **Upload files via Files tab**
2. **Set up virtual environment:**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 myenv
   pip install -r requirements_flask.txt
   ```
3. **Create WSGI file:**
   ```python
   import sys
   path = '/home/yourusername/your-app'
   if path not in sys.path:
       sys.path.append(path)
   from app_flask import app as application
   ```
4. **Add environment variables in Web tab**

### Option 5: Docker

Create a `Dockerfile.flask`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements_flask.txt .
RUN pip install --no-cache-dir -r requirements_flask.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "app_flask:app", "--bind", "0.0.0.0:5000"]
```

Build and run:
```bash
docker build -f Dockerfile.flask -t brooks-flask:latest .
docker run -d -p 5000:5000 -e GEMINI_API_KEY=your_key -e FLASK_SECRET_KEY=your_secret brooks-flask:latest
```

## Production Checklist

- [ ] Set `FLASK_DEBUG=False` in production
- [ ] Use a strong `FLASK_SECRET_KEY` (generate with: `python -c 'import secrets; print(secrets.token_hex(32))'`)
- [ ] Set `GEMINI_API_KEY` as environment variable
- [ ] Use `gunicorn` or similar WSGI server (not Flask dev server)
- [ ] Enable HTTPS (most platforms do this automatically)
- [ ] Set up monitoring/logging

## Running with Gunicorn (Production)

```bash
gunicorn app_flask:app --bind 0.0.0.0:5000 --workers 4
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Your Google Gemini API key |
| `FLASK_SECRET_KEY` | Yes (production) | Secret key for session encryption |
| `FLASK_DEBUG` | No | Set to `False` in production |
| `PORT` | No | Port to run on (default: 5000) |

## Features

✅ Same functionality as Streamlit version  
✅ Dark theme matching original design  
✅ Responsive layout  
✅ Interactive chat interface  
✅ Report generation and display  
✅ Auto-saves to `output.txt`  

## Differences from Streamlit Version

- Uses Flask sessions instead of Streamlit session state
- Traditional web app (HTML/CSS/JS) instead of Streamlit components
- More control over styling and behavior
- Can be deployed to any WSGI-compatible platform

## Troubleshooting

### Session not working
- Ensure `FLASK_SECRET_KEY` is set
- Check that cookies are enabled in browser

### Import errors
- Make sure all files are in the correct directory structure
- Verify `python_app/` directory is accessible

### API errors
- Check `GEMINI_API_KEY` is set correctly
- Verify API key is valid and has quota

## Next Steps

1. Test locally: `python app_flask.py`
2. Choose deployment platform
3. Set environment variables
4. Deploy!

Your Flask app is ready! 🚀


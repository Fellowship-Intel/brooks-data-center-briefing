# Run Flask Web App

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_flask.txt
```

### 2. Set Environment Variables

Your `.env` file should have:
```
GEMINI_API_KEY=your_api_key_here
FLASK_SECRET_KEY=your-secret-key-here
```

Or set them in your environment:
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
$env:FLASK_SECRET_KEY="your-secret-key-here"
```

### 3. Run the App

```bash
python app_flask.py
```

The app will be available at: **http://localhost:5000**

## Features

✅ Full web interface (no Streamlit needed)  
✅ Dark theme matching original design  
✅ Interactive report generation  
✅ Chat interface with AI analyst  
✅ Auto-saves reports to `output.txt`  
✅ Responsive design  

## File Structure

```
app_flask.py          # Main Flask application
templates/
  ├── base.html      # Base template
  ├── input.html     # Input form page
  └── report.html    # Report display page
static/
  ├── style.css      # Custom styles
  └── app.js         # JavaScript functionality
```

## Production Deployment

See [FLASK_DEPLOYMENT.md](FLASK_DEPLOYMENT.md) for deployment options:
- Heroku
- Railway
- Render
- PythonAnywhere
- Docker

## Differences from Streamlit

| Feature | Streamlit | Flask |
|---------|-----------|-------|
| Framework | Streamlit | Flask |
| UI | Streamlit components | HTML/CSS/JS |
| Deployment | Streamlit Cloud | Any WSGI server |
| Customization | Limited | Full control |
| Styling | Streamlit theme | Custom CSS |

Both versions have the same functionality - choose based on your preference!


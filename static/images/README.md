# Logo Directory

## Adding Your Logo

1. Save your logo image file as `logo.png` in this directory
2. Supported formats: PNG, JPG, SVG
3. Recommended size: 200-400px width for best display
4. The logo will automatically appear in the Streamlit sidebar

## File Location
```
static/images/logo.png
```

## Alternative Formats
If you have a different format, you can:
- Rename it to `logo.png` (if PNG)
- Or update `app.py` line ~540 to use your filename:
  ```python
  logo_path = Path("static/images/your-logo-name.png")
  ```


# Running the App Locally (Command Line)

This guide shows you how to run the app as a standalone command-line application without needing a web browser or URL.

## Quick Start

1. **Make sure you have Python installed:**
   ```powershell
   python --version
   ```
   Should show Python 3.8 or higher.

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Set your API key** (if not already set):
   ```powershell
   # Check if .env file exists
   Get-Content .env
   ```
   
   If it doesn't exist or doesn't have the key, create/update it:
   ```powershell
   echo GEMINI_API_KEY=your_api_key_here > .env
   ```

4. **Run the local version:**
   ```powershell
   python run_local.py
   ```

## What It Does

The local version:
- ✅ Generates the daily briefing report
- ✅ Displays it in your terminal
- ✅ Saves the full report to `output.txt`
- ✅ Offers an interactive Q&A chat session
- ✅ Runs completely offline (no browser needed)

## Features

### Report Display
The report is displayed in your terminal with:
- Full report markdown
- Top movers analysis
- Core tickers deep dive
- Audio report text

### Interactive Chat
After viewing the report, you can:
- Ask questions about the report
- Get more details on specific tickers
- Continue the conversation
- Type `exit` or `quit` to end

### Output File
The full report is automatically saved to `output.txt` in the project directory.

## Example Session

```
================================================================================
  BROOKS DATA CENTER BRIEFING - LOCAL MODE
================================================================================

Generating daily briefing report...
This may take a minute...

================================================================================
  DAILY BRIEFING REPORT
================================================================================

Generated: 2025-01-15 14:30:00

────────────────────────────────────────────────────────────────────────────────
  FULL REPORT
────────────────────────────────────────────────────────────────────────────────

[Report content here...]

────────────────────────────────────────────────────────────────────────────────
  TOP MOVERS
────────────────────────────────────────────────────────────────────────────────

[1] NVDA - NVIDIA Corporation
    Strong AI Demand Drives Record Volume

    Snapshot: NVIDIA surged 5.2% on record volume...
    ...

✓ Report saved to output.txt

Would you like to ask questions about this report? (y/n): y

================================================================================
  ANALYST Q&A
================================================================================
Ask questions about the report. Type 'exit' or 'quit' to end the chat.

You: What drove NVDA's movement today?
Analyst: NVIDIA's strong performance was driven by...

You: exit

Ending chat session. Goodbye!
```

## Differences from Streamlit Version

| Feature | Streamlit (app.py) | Local (run_local.py) |
|---------|-------------------|---------------------|
| Interface | Web browser | Terminal/Command line |
| URL Required | Yes (localhost:8501) | No |
| Interactive UI | Yes (buttons, forms) | Yes (text-based) |
| Charts/Visualizations | Yes | No (text only) |
| Chat Interface | Sidebar | Terminal input |
| Output File | Yes | Yes |

## Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure your `.env` file exists in the project root
- Or set it as an environment variable:
  ```powershell
  $env:GEMINI_API_KEY="your_key_here"
  ```

### "Module not found"
- Install dependencies: `pip install -r requirements.txt`
- Make sure you're in the project root directory

### Report generation fails
- Check your internet connection (needed for API calls)
- Verify your API key is valid
- Check API quota in Google Cloud Console

## Tips

- The report is automatically saved to `output.txt` - you can view it later
- Use `Ctrl+C` to interrupt if needed
- Chat history is maintained during the session
- All output is also written to `output.txt` for reference

## Next Steps

After running the local version, you can:
1. Review the `output.txt` file for the full report
2. Use the interactive chat to ask follow-up questions
3. Run it again anytime to generate a new report

Enjoy your local briefing!


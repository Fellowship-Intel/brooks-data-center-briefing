import os
import json
import re
from typing import Optional, List, Dict, Any, Union
import google.generativeai as genai
from python_app.types import DailyReportResponse, InputData, MiniReport, MarketData, NewsItem
from python_app.utils import market_data_to_dict, news_item_to_dict
from gcp_clients import get_bucket


# Global chat session to maintain context
_chat_session: Optional[genai.ChatSession] = None
_is_json_mode = False


def initialize_ai() -> None:
    """Initialize the Gemini AI client."""
    # Priority 1: Try service account credentials (for GCP service accounts)
    # Note: Gemini API may require API key even with service accounts
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if google_creds and os.path.exists(google_creds):
        try:
            # Try to use service account authentication
            import google.auth
            from google.auth.transport.requests import Request
            
            credentials, project = google.auth.default()
            
            # Refresh credentials to get a valid token
            credentials.refresh(Request())
            
            # Try to configure with credentials (may not be supported by all Gemini API versions)
            try:
                genai.configure(credentials=credentials)
                return
            except (TypeError, AttributeError):
                # If credentials parameter not supported, fall through to API key
                pass
        except Exception as e:
            # Silently fall back to API key if service account auth fails
            pass
    
    # Priority 2: Try Streamlit secrets first (for Streamlit Cloud), then environment variables
    api_key = None
    try:
        import streamlit as st  # type: ignore
        api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("API_KEY")
    except (ImportError, AttributeError, FileNotFoundError):
        # Streamlit not available, continue to next option
        pass
    
    # Priority 3: Fall back to environment variables
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")
    
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY or API_KEY must be set in Streamlit secrets or environment variables. "
            "Note: Gemini API requires an API key even when using service account credentials for other GCP services."
        )
    
    genai.configure(api_key=api_key)


def generate_daily_report(input_data: InputData) -> DailyReportResponse:
    """Generate a daily report using Gemini AI."""
    global _chat_session, _is_json_mode
    
    initialize_ai()
    
    has_market_data = input_data.market_data_json and len(input_data.market_data_json) > 0
    has_news_data = input_data.news_json and len(input_data.news_json) > 0
    
    prompt = f"""
    Generate today's daily briefing and audio report based on the following context.
    
    Trading Date: {input_data.trading_date} (Use this date or the most recent trading session if today is a weekend/holiday).
    Tickers Tracked: {', '.join(input_data.tickers_tracked)}
    Macro Context Instruction: {input_data.macro_context}
    Constraints/Notes: {input_data.constraints_or_notes}

    Market Data Status: {"Provided in JSON below" if has_market_data else "**MISSING/EMPTY** - You MUST use Google Search to find the latest market data (Open, High, Low, Close, Volume) for the tracked tickers."}
    News Data Status: {"Provided in JSON below" if has_news_data else "**MISSING/EMPTY** - You MUST use Google Search to find the latest relevant news for the tracked tickers."}

    If you perform a Google Search for market data, you MUST populate the 'updated_market_data' field in your JSON response with the values you found, so the dashboard can update its charts.

    Market Data JSON (Input):
    ```json
    {json.dumps([market_data_to_dict(md) for md in input_data.market_data_json])}
    ```

    News JSON (Input):
    ```json
    {json.dumps([news_item_to_dict(n) for n in input_data.news_json])}
    ```

    CRITICAL OUTPUT INSTRUCTION:
    1. You must return a SINGLE valid JSON object.
    2. Do NOT wrap it in markdown code blocks (like ```json ... ```).
    3. Do NOT include any conversational text before or after the JSON.
    4. **IMPORTANT**: Ensure all newlines inside string values (like 'report_markdown' or 'audio_report') are properly escaped as \\n. Do not produce real line breaks inside the JSON string values.
    5. **Return the JSON in a minified format (single line) if possible** to ensure parsing reliability.
    6. **CRITICAL JSON SYNTAX**: Do NOT use unescaped double quotes inside your text string values. Use single quotes (') for emphasis or titles within the text content. (e.g. use 'AI Mega-Deals' instead of "AI Mega-Deals"). If you absolutely must use a double quote inside a string value, you MUST escape it with a backslash (\\").

    The JSON object must strictly adhere to this schema:
    {{
      "report_markdown": "string (The full written report in markdown format)",
      "core_tickers_in_depth_markdown": "string (The deep dive section in markdown format)",
      "reports": [
        {{
          "ticker": "string",
          "company_name": "string",
          "section_title": "string",
          "snapshot": "string",
          "catalyst_and_context": "string",
          "day_trading_lens": "string",
          "watch_next_bullets": ["string"]
        }}
      ],
      "audio_report": "string (The full text for the audio report, written for TTS)",
      "updated_market_data": [
         {{
            "ticker": "string",
            "company_name": "string",
            "previous_close": number,
            "open": number,
            "high": number,
            "low": number,
            "close": number,
            "volume": number,
            "average_volume": number,
            "percent_change": number,
            "intraday_range": "string",
            "market_cap": "string"
         }}
      ]
    }}
    """
    
    from python_app.constants import SYSTEM_INSTRUCTION
    
    # Create a new model with system instruction and tools
    # Note: Google Search tool availability depends on API access and model version
    # Check Google AI Studio for available tools: https://ai.google.dev/
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',  # Update model name as needed
        system_instruction=SYSTEM_INSTRUCTION
        # tools parameter may vary - check latest API docs for Google Search integration
    )
    
    # Start a new chat session
    _chat_session = model.start_chat(history=[])
    _is_json_mode = True
    
    response = _chat_session.send_message(prompt)
    text = response.text
    
    if not text:
        raise ValueError("No response from Gemini")
    
    # CLEANUP: Remove common markdown fences if present
    text = re.sub(r'```json', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```', '', text).strip()
    
    # ROBUST JSON EXTRACTION
    # Find the first '{' and the last '}' to extract the JSON object
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1:
        text = text[start:end + 1]
    else:
        raise ValueError(f"Model response did not contain a valid JSON object: {text[:500]}")
    
    try:
        data = json.loads(text)
        
        # Convert to typed objects
        reports = [
            MiniReport(**r) for r in data.get('reports', [])
        ]
        
        updated_market_data = None
        if 'updated_market_data' in data and data['updated_market_data']:
            updated_market_data = [
                MarketData(**m) for m in data['updated_market_data']
            ]
        
        return DailyReportResponse(
            report_markdown=data.get('report_markdown', ''),
            core_tickers_in_depth_markdown=data.get('core_tickers_in_depth_markdown', ''),
            reports=reports,
            audio_report=data.get('audio_report', ''),
            updated_market_data=updated_market_data
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from model: {str(e)}\nResponse: {text[:500]}")


def _call_gemini_for_report(prompt: str, model_name: str | None = None) -> dict:
    """
    Calls Gemini with the given prompt and returns a structured result dict:
    
    {
      "summary_text": str,
      "key_insights": list[str],
      "market_context": str | None
    }
    
    Args:
        prompt: The prompt to send to Gemini.
        model_name: Optional model name (e.g., "gemini-2.0-flash-exp"). 
                   If None, uses default "gemini-2.0-flash-exp".
    
    Returns:
        A dictionary with keys: "summary_text", "key_insights", "market_context".
    
    Raises:
        ValueError: If Gemini returns an invalid response or JSON parsing fails.
    """
    initialize_ai()
    
    # Use provided model_name or default
    if model_name is None:
        model_name = 'gemini-2.0-flash-exp'
    
    # Enhance prompt to request structured JSON output
    enhanced_prompt = f"""{prompt}

CRITICAL OUTPUT INSTRUCTION:
1. You must return a SINGLE valid JSON object.
2. Do NOT wrap it in markdown code blocks (like ```json ... ```).
3. Do NOT include any conversational text before or after the JSON.
4. **IMPORTANT**: Ensure all newlines inside string values are properly escaped as \\n.
5. **CRITICAL JSON SYNTAX**: Do NOT use unescaped double quotes inside your text string values. 
   Use single quotes (') for emphasis or titles within the text content. 
   If you absolutely must use a double quote inside a string value, you MUST escape it with a backslash (\\").

The JSON object must strictly adhere to this schema:
{{
  "summary_text": "string (The main summary text)",
  "key_insights": ["string", "string", ...],
  "market_context": "string | null (Optional market context summary)"
}}
"""
    
    from python_app.constants import SYSTEM_INSTRUCTION
    
    # Create a model with system instruction
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_INSTRUCTION
    )
    
    # Start a new chat session for this call
    chat_session = model.start_chat(history=[])
    
    response = chat_session.send_message(enhanced_prompt)
    text = response.text
    
    if not text:
        raise ValueError("No response from Gemini")
    
    # CLEANUP: Remove common markdown fences if present
    text = re.sub(r'```json', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```', '', text).strip()
    
    # ROBUST JSON EXTRACTION
    # Find the first '{' and the last '}' to extract the JSON object
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1:
        text = text[start:end + 1]
    else:
        raise ValueError(f"Model response did not contain a valid JSON object: {text[:500]}")
    
    try:
        data = json.loads(text)
        
        # Extract and validate required fields
        summary_text = data.get('summary_text', '')
        key_insights = data.get('key_insights', [])
        market_context = data.get('market_context')
        
        # Ensure key_insights is a list
        if not isinstance(key_insights, list):
            key_insights = []
        
        # Ensure summary_text is a string
        if not isinstance(summary_text, str):
            summary_text = str(summary_text) if summary_text else ''
        
        # market_context can be None, str, or convert to str if not None
        if market_context is not None and not isinstance(market_context, str):
            market_context = str(market_context)
        
        return {
            "summary_text": summary_text,
            "key_insights": key_insights,
            "market_context": market_context
        }
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from model: {str(e)}\nResponse: {text[:500]}")


def _store_report_audio_in_gcs(trading_date: str, audio_bytes: bytes) -> str:
    """
    Stores the audio bytes in the REPORTS_BUCKET_NAME bucket under a path like:
    reports/{trading_date}/daily_report.mp3

    Returns the GCS URI or "gs://bucket/path" string.

    Args:
        trading_date: ISO date format (e.g., "2025-12-03").
        audio_bytes: The audio file bytes to upload.

    Returns:
        The GCS URI string in format "gs://bucket/path/to/file.mp3".

    Raises:
        ValueError: If REPORTS_BUCKET_NAME is not configured.
        RuntimeError: If the upload fails.
    """
    # Get bucket name from environment variable with default
    bucket_name = os.getenv("REPORTS_BUCKET_NAME", "mikebrooks-reports")
    
    if not bucket_name:
        raise ValueError("REPORTS_BUCKET_NAME environment variable must be set")
    
    # Get the bucket
    bucket = get_bucket(bucket_name)
    
    # Create path: reports/{trading_date}/daily_report.mp3
    blob_path = f"reports/{trading_date}/daily_report.mp3"
    blob = bucket.blob(blob_path)
    
    # Upload with content type
    blob.upload_from_string(audio_bytes, content_type="audio/mpeg")
    
    # Return full GCS URI
    return f"gs://{bucket_name}/{blob_path}"


def save_daily_report_to_firestore(
    client_id: str,
    trading_date: str,
    summary_text: str,
    key_insights: List[str],
    market_context: Optional[str],
    market_data: Union[List[Union[MarketData, Dict[str, Any]]], Dict[str, Dict[str, Any]]],
    news_items: List[Union[NewsItem, Dict[str, Any]]],
    tickers: Optional[List[str]] = None,
    email_status: str = "pending"
) -> None:
    """
    Build a report dict matching daily_reports schema and save it to Firestore.
    
    Args:
        client_id: The client document ID (e.g., "michael_brooks").
        trading_date: ISO date format (e.g., "2025-12-03").
        summary_text: The main textual report.
        key_insights: List of key insight strings.
        market_context: Optional market context summary (string or None).
        market_data: Either:
            - List of MarketData objects or dictionaries, OR
            - Dictionary where keys are ticker symbols and values are market data dicts
              (e.g., {"SMCI": {"ticker": "SMCI", ...}, "IREN": {...}})
        news_items: List of NewsItem objects or dictionaries.
        tickers: Optional explicit list of tickers. If None, derives from market_data.
        email_status: Email status (default: "pending").
    
    Raises:
        ValueError: If required fields are missing or invalid.
    """
    from report_repository import create_or_update_daily_report
    
    # Normalize market_data: convert dict-of-dicts to list if needed
    market_data_list: List[Union[MarketData, Dict[str, Any]]]
    if isinstance(market_data, dict):
        # Handle dict format: {"SMCI": {...}, "IREN": {...}}
        market_data_list = []
        for ticker, data in market_data.items():
            if isinstance(data, dict):
                # Ensure ticker field is set in the data dict
                data_with_ticker = data.copy()
                if 'ticker' not in data_with_ticker:
                    data_with_ticker['ticker'] = ticker
                market_data_list.append(data_with_ticker)
            else:
                raise ValueError(f"Invalid market_data value type for ticker {ticker}: {type(data)}")
    else:
        # Already a list
        market_data_list = market_data
    
    # Derive tickers from market_data if not explicitly provided
    if tickers is None:
        tickers = []
        for md in market_data_list:
            if isinstance(md, MarketData):
                ticker = md.ticker
            elif isinstance(md, dict):
                ticker = md.get('ticker')
            else:
                continue
            if ticker and ticker not in tickers:
                tickers.append(ticker)
    
    # Convert market_data and news_items to dictionaries for raw_payload
    market_data_dicts = []
    for md in market_data_list:
        if isinstance(md, MarketData):
            market_data_dicts.append(market_data_to_dict(md))
        elif isinstance(md, dict):
            market_data_dicts.append(md)
        else:
            raise ValueError(f"Invalid market_data item type: {type(md)}")
    
    news_items_dicts = []
    for ni in news_items:
        if isinstance(ni, NewsItem):
            news_items_dicts.append(news_item_to_dict(ni))
        elif isinstance(ni, dict):
            news_items_dicts.append(ni)
        else:
            raise ValueError(f"Invalid news_items item type: {type(ni)}")
    
    # Build the report dict matching daily_reports schema
    report = {
        "client_id": client_id,
        "trading_date": trading_date,
        "summary_text": summary_text,
        "key_insights": key_insights,
        "tickers": tickers,
        "email_status": email_status,
        "raw_payload": {
            "market_data": market_data_dicts,
            "news_items": news_items_dicts
        }
    }
    
    # Add market_context if provided
    if market_context is not None:
        report["market_context"] = market_context
    
    # Save to Firestore
    create_or_update_daily_report(report)


def send_chat_message(message: str) -> str:
    """Send a chat message to the existing session."""
    global _chat_session
    
    if not _chat_session:
        raise ValueError("Please generate a report first to establish context.")
    
    response = _chat_session.send_message(message)
    return response.text or "I couldn't generate a response."


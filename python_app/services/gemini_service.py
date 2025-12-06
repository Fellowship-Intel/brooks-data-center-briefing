import os
import json
import logging
from typing import Optional, List, Dict, Any, Union
import google.generativeai as genai
from datetime import date

# Import types
from python_app.types import (
    DailyReportResponse, 
    InputData, 
    MiniReport, 
    MarketData, 
    NewsItem
)
from utils.error_tracking import capture_exception
from report_service import generate_and_store_daily_report
from python_app.services.gemini_client import create_gemini_model, initialize_gemini

logger = logging.getLogger(__name__)

# Global chat session to maintain context
_chat_session: Optional[genai.ChatSession] = None
_is_json_mode = False

def initialize_ai() -> None:
    """Initialize the Gemini AI client (delegates to shared client)."""
    initialize_gemini()

def _input_data_to_dicts(input_data: InputData) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Helper to convert InputData to dicts expected by report_service."""
    
    # Market Data
    market_data_dict = {}
    if input_data.market_data_json:
        # Convert list of MarketData to dict of dicts or list of dicts
        # report_service expects dict with 'updated_market_data' style or whatever the prompt uses.
        # But wait, report_service prompt expects 'tickers' or 'prices'.
        # Let's map it to a structure that _build_gemini_prompt handles well.
        # _build_gemini_prompt just json.dumps it.
        # So we can pass the list of dicts directly if we wrap it in a dict?
        # Actually _build_gemini_prompt expects 'market_data' as a dict.
        market_data_dict = {
            "tickers": input_data.tickers_tracked,
            "data": [asdict(md) if hasattr(md, 'asdict') else md.__dict__ for md in input_data.market_data_json]
        }
    else:
        # If no market data, pass empty but with tickers
        market_data_dict = {"tickers": input_data.tickers_tracked}

    # News Items
    news_items_list = []
    if input_data.news_json:
        news_items_list = [asdict(n) if hasattr(n, 'asdict') else n.__dict__ for n in input_data.news_json]
    
    # We pass news items as a dict wrapper or list? report_service expects Optional[list[dict]] for news_items argument in _build_gemini_prompt?
    # No, generate_and_store_daily_report declares news_items: Dict[str, Any] but _build_gemini_prompt declares Optional[list[dict]].
    # report_service signatures are a bit inconsistent. 
    # _generate_gemini_text_report takes news_items: Dict[str, Any] but passes to _generate_report_text which takes Optional[list[dict]]?
    # Let's look at report_service.py line 358: "news_items if isinstance(news_items, list) else [news_items] if news_items else None"
    # So we can pass the list directly if we cast it to Any, or wrap it.
    # To be safe and consistent with generate_and_store_daily_report signature (Dict), we'll wrap it.
    news_items_dict = {"items": news_items_list}
    
    # Macro Context
    macro_context_dict = {
        "context": input_data.macro_context,
        "constraints": input_data.constraints_or_notes
    }
    
    return market_data_dict, news_items_dict, macro_context_dict

def generate_daily_report(input_data: InputData) -> DailyReportResponse:
    """
    Generate a daily report using Gemini AI.
    Now delegates to the consolidated report_service.py backend.
    """
    global _chat_session
    
    try:
        trading_date_obj = date.fromisoformat(input_data.trading_date)
    except ValueError:
        trading_date_obj = date.today()
        
    market_data, news_items, macro_context = _input_data_to_dicts(input_data)
    
    # Call the backend service
    # We need to get the user's client_id. Since this is Streamlit, we check session state?
    # But this service might be called from outside. 
    # For now we use a default or assume the caller handles it.
    # But wait, generate_for_michael_brooks uses default.
    # We should try to get it from input_data if it existed, but it doesn't.
    # We will let generate_and_store_daily_report use the default from config if None.
    
    result = generate_and_store_daily_report(
        trading_date=trading_date_obj,
        market_data=market_data,
        news_items=news_items,
        macro_context=macro_context
    )
    
    # Map result back to DailyReportResponse
    reports_data = result.get("reports", [])
    reports_objs = []
    for r in reports_data:
        if isinstance(r, dict):
            reports_objs.append(MiniReport(**r))
            
    updated_market_data_objs = []
    if result.get("updated_market_data"):
       for md in result.get("updated_market_data"):
           if isinstance(md, dict):
               updated_market_data_objs.append(MarketData(**md))

    return DailyReportResponse(
        report_markdown=result.get("report_markdown") or result.get("summary_text", ""),
        core_tickers_in_depth_markdown=result.get("market_context") or "",
        reports=reports_objs,
        audio_report=result.get("audio_report", ""),
        updated_market_data=updated_market_data_objs
    )

def send_chat_message(message: str) -> str:
    """Send a chat message to the existing session."""
    # This logic needs to remain stateful for the Streamlit session.
    # report_service doesn't handle chat state.
    # So we keep this part here or move chat state to a ChatService.
    # For now, keep it here but strictly for chat.
    global _chat_session
    
    initialize_ai()
    
    if _chat_session is None:
         # Start a new session if none exists
         from python_app.constants import SYSTEM_INSTRUCTION
         from config import get_config
         config = get_config()
         model = create_gemini_model(model_name=config.gemini_model_name, system_instruction=SYSTEM_INSTRUCTION)
         _chat_session = model.start_chat(history=[])
    
    try:
        response = _chat_session.send_message(message)
        return response.text
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return f"I'm sorry, I encountered an error: {str(e)}"

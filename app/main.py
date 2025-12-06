from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional, List
import os
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from report_repository import get_daily_report, list_daily_reports
from report_service import generate_and_store_daily_report, generate_watchlist_daily_report
from utils.rate_limiter import (
    _report_generation_limiter,
    _api_limiter,
    _gemini_api_limiter,
    check_rate_limit,
    get_rate_limit_headers,
)
from utils.input_validation import (
    validate_client_id,
    validate_trading_date,
    validate_market_data,
    validate_watchlist_request,
)
from utils.input_validation import (
    validate_client_id,
    validate_trading_date,
    validate_market_data,
    validate_watchlist_request,
)
from utils.exceptions import ValidationError
from app.dependencies import get_current_user
from fastapi import Depends

# Initialize error tracking (optional)
try:
    from utils.error_tracking import init_error_tracking, capture_exception
    init_error_tracking(environment=os.getenv("ENVIRONMENT", "development"))
    _error_tracking_available = True
except ImportError:
    _error_tracking_available = False
    def capture_exception(*args, **kwargs): pass

from app.logging_config import configure_logging

# Initialize logging immediately
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Brooks Data Center Daily Briefing API",
    description="""
    REST API for generating and managing daily trading reports for data center and AI infrastructure equities.
    
    ## Features
    
    - **Report Generation**: Generate AI-powered daily briefings using Google Gemini
    - **Watchlist Reports**: Generate reports for custom watchlists
    - **Audio Reports**: Text-to-speech audio generation (Eleven Labs primary, Gemini fallback)
    - **Report Storage**: Store and retrieve reports from Google Cloud Firestore
    - **Health Monitoring**: Comprehensive health check endpoint
    
    ## Authentication
    
    Currently uses client_id-based identification. Future versions will support API key authentication.
    
    ## Rate Limiting
    
    - Report generation: 5 requests per hour per client
    - API endpoints: 100 requests per hour per IP
    - Gemini API: 60 requests per minute
    
    ## Examples
    
    ### Generate a Report
    
    ```bash
    curl -X POST "http://localhost:8000/reports/generate" \\
      -H "Content-Type: application/json" \\
      -d '{
        "trading_date": "2025-01-27",
        "client_id": "michael_brooks",
        "market_data": {
          "tickers": ["SMCI", "NVDA"],
          "prices": {
            "SMCI": {"close": 850.25, "change_percent": 1.8}
          }
        }
      }'
    ```
    
    ### Generate Watchlist Report
    
    ```bash
    curl -X POST "http://localhost:8000/reports/generate/watchlist" \\
      -H "Content-Type: application/json" \\
      -d '{
        "client_id": "michael_brooks",
        "watchlist": ["SMCI", "NVDA", "IREN"],
        "trading_date": "2025-01-27"
      }'
    ```
    
    ### Get Report
    
    ```bash
    curl "http://localhost:8000/reports/2025-01-27?client_id=michael_brooks"
    ```
    
    ### Health Check
    
    ```bash
    curl "http://localhost:8000/health"
    ```
    """,
    version="0.1.0",
    contact={
        "name": "Brooks Data Center Briefing",
        "email": "support@example.com",
    },
    license_info={
        "name": "Proprietary",
    },
)

# Add CORS middleware to allow frontend requests
# Default to local dev ports if not specified
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080,http://localhost:3002,http://localhost:3003")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

from app.schemas import GenerateReportRequest, DailyReportResponse, WatchlistReportResponse, WatchlistReportRequest, MarketData, NewsItem

# ---------------------------------------------------------------------------
# Internal helpers for dummy data (mirrors manual harness)
# ---------------------------------------------------------------------------

def _dummy_market_data() -> Dict[str, Any]:
    return {
        "tickers": ["SMCI", "IREN"],
        "prices": {
            "SMCI": {"close": 850.25, "change_percent": 1.8},
            "IREN": {"close": 10.42, "change_percent": -0.9},
        },
        "indices": {
            "SPX": {"close": 5200.12, "change_percent": 0.4},
            "NDX": {"close": 18000.55, "change_percent": 0.7},
        },
    }


def _dummy_news_items() -> Dict[str, Any]:
    return {
        "SMCI": [
            {
                "headline": "Supermicro extends rally as AI server demand stays strong",
                "source": "Example Newswire",
                "summary": "Investors continue to price in sustained AI infrastructure demand.",
            }
        ],
        "IREN": [
            {
                "headline": "Bitcoin miner IREN updates on expansion plans",
                "source": "Example Newswire",
                "summary": "Company focuses on energy-efficient capacity additions.",
            }
        ],
        "macro": [
            {
                "headline": "Fed holds rates steady, hints at future cuts",
                "source": "Example Newswire",
                "summary": "Provides a constructive backdrop for risk assets.",
            }
        ],
    }


def _dummy_macro_context() -> Dict[str, Any]:
    return {
        "risk_appetite": "moderate",
        "volatility_regime": "low_to_moderate",
        "key_themes": [
            "AI infrastructure build-out",
            "Bitcoin cycle and miner economics",
            "Rate expectations stabilizing",
        ],
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        Dictionary with status and service health information
    """
    try:
        from utils.health_check import comprehensive_health_check
        
        health_status = comprehensive_health_check()
        
        # Add metrics if available
        try:
            from utils.metrics import get_metrics_collector
            metrics = get_metrics_collector()
            health_status["metrics"] = metrics.get_stats()
        except Exception:
            pass  # Metrics optional
        
        # Determine HTTP status code
        if health_status["status"] == "unhealthy":
            raise HTTPException(
                status_code=503,
                detail=health_status
            )
        
        return health_status
    except Exception as e:
        logger.error("Health check failed: %s", e, exc_info=True)
        if _error_tracking_available:
            capture_exception(e, tags={"endpoint": "health_check"})
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )


@app.post("/reports/generate")
async def generate_report(req: GenerateReportRequest, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Generate a daily report.

    - If client_id is omitted, uses default from configuration.
    - If trading_date is omitted, uses today's date.
    - If market_data / news_items / macro_context are omitted, uses dummy data.

    This calls the SAME backend orchestration you use in your manual harness.
    
    Rate limited to prevent abuse.
    All inputs are validated and sanitized for security.
    """
    from config import get_config
    config = get_config()
    
    # Validate and sanitize inputs
    try:
        # Enforce client_id from token
        client_id_from_auth = user.get("email")
        if not client_id_from_auth:
             raise HTTPException(status_code=400, detail="User email not found in token")
             
        client_id = validate_client_id(client_id_from_auth)
        trading_date = validate_trading_date(req.trading_date)
        
        # Transform MarketData List -> Dict
        market_data: Dict[str, Any] = {}
        if req.market_data_json:
            tickers = [m.ticker for m in req.market_data_json]
            prices = {
                m.ticker: {"close": m.close, "change_percent": m.percent_change} 
                for m in req.market_data_json
            }
            market_data = {"tickers": tickers, "prices": prices}
            # Optional: Call validate_market_data(market_data) if specific logic needed
        else:
            market_data = _dummy_market_data()
        
        # Transform NewsItem List -> Dict
        news_items: Dict[str, Any] = {}
        if req.news_json:
            for item in req.news_json:
                tk = item.ticker or "macro"
                if tk not in news_items:
                    news_items[tk] = []
                news_items[tk].append({
                    "headline": item.headline,
                    "summary": item.summary,
                    "source": item.source,
                    "time": item.time
                })
        else:
            news_items = _dummy_news_items()

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    
    # Rate limit by client_id
    try:
        check_rate_limit(_report_generation_limiter, f"report_gen_{client_id}")
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e
    macro_context = req.macro_context or _dummy_macro_context()

    try:
        result = generate_and_store_daily_report(
            trading_date=trading_date,
            client_id=client_id,
            market_data=market_data,
            news_items=news_items,
            macro_context=macro_context,
        )
    except Exception as exc:
        # Surface a simple 500 with a short message; details remain in logs.
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}") from exc

    # Add rate limit headers
    headers = get_rate_limit_headers(_report_generation_limiter, f"report_gen_{client_id}")
    # Note: FastAPI response headers are set via Response object, but for simplicity
    # we'll just return the result. Headers can be added via middleware if needed.
    
    # Ensure response includes raw_payload for frontend compatibility
    if isinstance(result, dict) and "raw_payload" not in result:
        result["raw_payload"] = result
    
    return result


@app.get("/reports/{trading_date}")
async def get_report(trading_date: str, client_id: Optional[str] = None, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Fetch a previously generated report for a given trading_date and client_id.

    trading_date is ISO format (YYYY-MM-DD).
    """
    from config import get_config
    from config import get_config
    
    # Enforce auth
    auth_client_id = user.get("email")
    if client_id and client_id != auth_client_id:
        raise HTTPException(status_code=403, detail="Cannot access reports for other clients")
    
    if client_id is None:
        client_id = auth_client_id
    try:
        parsed_date = date.fromisoformat(trading_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trading_date format, expected YYYY-MM-DD")

    try:
        doc = get_daily_report(trading_date)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error loading report: {exc}") from exc

    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check if client_id matches (if stored in document)
    if doc.get("client_id") and doc.get("client_id") != client_id:
        raise HTTPException(status_code=404, detail="Report not found for this client")

    return doc


@app.get("/reports/{trading_date}/audio")
async def get_report_audio(
    trading_date: str,
    client_id: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Return audio information for a given report.

    For now returns the GCS path stored in Firestore; you can later extend this
    to return a signed URL or direct audio streaming if you want a richer UX.
    """
    from config import get_config
    auth_client_id = user.get("email")
    if client_id and client_id != auth_client_id:
        raise HTTPException(status_code=403, detail="Cannot access reports for other clients")
    
    if client_id is None:
        client_id = auth_client_id
    try:
        parsed_date = date.fromisoformat(trading_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trading_date format, expected YYYY-MM-DD")

    try:
        doc = get_daily_report(trading_date)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error loading report: {exc}") from exc

    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check if client_id matches (if stored in document)
    if doc.get("client_id") and doc.get("client_id") != client_id:
        raise HTTPException(status_code=404, detail="Report not found for this client")

    audio_gcs_path = doc.get("audio_gcs_path")
    if not audio_gcs_path:
        raise HTTPException(status_code=404, detail="No audio recorded for this report")

    return {
        "client_id": client_id,
        "trading_date": trading_date,
        "audio_gcs_path": audio_gcs_path,
    }


@app.post("/reports/generate/watchlist", response_model=WatchlistReportResponse)
async def generate_watchlist_report_endpoint(payload: WatchlistReportRequest, user: Dict[str, Any] = Depends(get_current_user)):
    trading_date = payload.trading_date or date.today()
    
    # Enforce auth
    client_id = user.get("email")
    if not client_id:
         raise HTTPException(status_code=401, detail="Invalid user")

    logger.info(
        "API /reports/generate/watchlist: client=%s date=%s watchlist=%s",
        client_id,
        trading_date.isoformat(),
        ",".join(payload.watchlist),
    )

    report = generate_watchlist_daily_report(
        trading_date=trading_date,
        client_id=client_id,
        watchlist=payload.watchlist,
    )

    # Fetch raw_payload from Firestore if not in report
    raw_payload = report.get("raw_payload", {})
    if not raw_payload:
        try:
            stored_report = get_daily_report(trading_date.isoformat())
            if stored_report:
                raw_payload = stored_report.get("raw_payload", {})
        except Exception:
            # If fetch fails, use empty dict
            raw_payload = {}

    return WatchlistReportResponse(
        client_id=report.get("client_id", payload.client_id),
        trading_date=trading_date,
        watchlist=payload.watchlist,
        summary_text=report.get("summary_text", ""),
        key_insights=report.get("key_insights", []),
        audio_gcs_path=report.get("audio_gcs_path"),
        raw_payload=raw_payload,
    )


@app.get("/reports")
async def list_reports(
    limit: int = 100, 
    start_after: Optional[str] = None, 
    client_id: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List recent reports with pagination.
    """
    try:
        from config import get_config
        from config import get_config
        
        # Enforce auth
        auth_client_id = user.get("email")
        if client_id and client_id != auth_client_id:
             raise HTTPException(status_code=403, detail="Cannot access reports for other clients")
             
        if client_id is None:
            client_id = auth_client_id
        
        result = list_daily_reports(
            client_id=client_id,
            limit=min(limit, 100),
            order_by="trading_date",
            descending=True,
            start_after=start_after
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error listing reports: {exc}") from exc


@app.post("/chat/message")
async def chat_message(req: Dict[str, Any], user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Send a chat message and get AI response.
    """
    message = req.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        from python_app.services.gemini_service import send_chat_message, initialize_ai
        
        # Initialize AI if not already done
        try:
            initialize_ai()
        except:
            pass  # May already be initialized
        
        response = send_chat_message(message)
        return {"response": response}
    except Exception as exc:
        logger.error(f"Chat error: {exc}", exc_info=True)
        # Return a helpful error message
        return {"response": f"I'm sorry, I couldn't process your message. Please try generating a report first to establish context. Error: {str(exc)}"}


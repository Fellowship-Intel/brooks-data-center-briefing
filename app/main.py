from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from report_repository import get_daily_report
from report_service import generate_and_store_daily_report

app = FastAPI(
    title="Michael Brooks Daily Report API",
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class GenerateReportRequest(BaseModel):
    """
    Request body for generating a new report.

    All fields are optional for now so you can quickly test with an empty body;
    when missing, we fall back to simple dummy data similar to your manual harness.
    """
    trading_date: Optional[date] = None
    client_id: Optional[str] = None
    market_data: Optional[Dict[str, Any]] = None
    news_items: Optional[Dict[str, Any]] = None
    macro_context: Optional[Dict[str, Any]] = None


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

@app.post("/reports/generate")
async def generate_report(req: GenerateReportRequest) -> Dict[str, Any]:
    """
    Generate a daily report.

    - If client_id is omitted, defaults to "michael_brooks".
    - If trading_date is omitted, uses today's date.
    - If market_data / news_items / macro_context are omitted, uses dummy data.

    This calls the SAME backend orchestration you use in your manual harness.
    """
    client_id = req.client_id or "michael_brooks"
    trading_date = req.trading_date or date.today()

    market_data = req.market_data or _dummy_market_data()
    news_items = req.news_items or _dummy_news_items()
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

    return result


@app.get("/reports/{trading_date}")
async def get_report(trading_date: str, client_id: str = "michael_brooks") -> Dict[str, Any]:
    """
    Fetch a previously generated report for a given trading_date and client_id.

    trading_date is ISO format (YYYY-MM-DD).
    """
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
    client_id: str = "michael_brooks",
) -> Dict[str, Any]:
    """
    Return audio information for a given report.

    For now returns the GCS path stored in Firestore; you can later extend this
    to return a signed URL or direct audio streaming if you want a richer UX.
    """
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


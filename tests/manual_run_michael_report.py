from __future__ import annotations

import json
from datetime import date

from report_service import generate_for_michael_brooks


def _build_dummy_market_data() -> dict:
    """
    Minimal stub market data for a single run.

    Replace this with real data later (e.g., pulled from an API or Make.com).
    """
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


def _build_dummy_news_items() -> dict:
    """
    Minimal stub news items for the report.
    """
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


def _build_dummy_macro_context() -> dict:
    """
    Minimal macro context placeholder.
    """
    return {
        "risk_appetite": "moderate",
        "volatility_regime": "low_to_moderate",
        "key_themes": [
            "AI infrastructure build-out",
            "Bitcoin cycle and miner economics",
            "Rate expectations stabilizing",
        ],
    }


def main() -> None:
    """
    Run a single end-to-end report generation for Michael Brooks.

    This will:
    - Call Gemini for text
    - Call Gemini TTS for audio
    - Write to Firestore
    - Upload audio to GCS
    """
    trading_date = date.today()  # You can override to a specific date if you want

    market_data = _build_dummy_market_data()
    news_items = _build_dummy_news_items()
    macro_context = _build_dummy_macro_context()

    print(f"🚀 Running manual daily report for Michael Brooks on {trading_date.isoformat()}")

    result = generate_for_michael_brooks(
        trading_date=trading_date,
        market_data=market_data,
        news_items=news_items,
        macro_context=macro_context,
    )

    print("✅ Report generation complete. Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()


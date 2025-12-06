"""
API client utilities for Streamlit to communicate with Node.js backend.
"""

import os
import requests
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# API base URL - defaults to localhost:8000
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class APIError(Exception):
    """Custom exception for API errors."""
    pass


def _make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Make HTTP request to Node.js API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (e.g., '/reports/generate')
        data: Request body data
        params: Query parameters
        
    Returns:
        JSON response as dictionary
        
    Raises:
        APIError: If request fails
    """
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        response = requests.request(
            method=method,
            url=url,
            json=data,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise APIError(f"API request failed: {str(e)}")


def generate_report(
    trading_date: str,
    client_id: str,
    market_data: Dict[str, Any],
    news_items: Dict[str, Any],
    macro_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a daily report via API."""
    return _make_request(
        "POST",
        "/reports/generate",
        data={
            "trading_date": trading_date,
            "client_id": client_id,
            "market_data": market_data,
            "news_items": news_items,
            "macro_context": macro_context,
        },
    )


def get_report(trading_date: str, client_id: str = "michael_brooks") -> Optional[Dict[str, Any]]:
    """Get an existing report via API."""
    try:
        return _make_request(
            "GET",
            f"/reports/{trading_date}",
            params={"client_id": client_id},
        )
    except APIError:
        return None


def get_report_audio(trading_date: str, client_id: str = "michael_brooks") -> Optional[Dict[str, Any]]:
    """Get audio metadata for a report via API."""
    try:
        return _make_request(
            "GET",
            f"/reports/{trading_date}/audio",
            params={"client_id": client_id},
        )
    except APIError:
        return None


def generate_watchlist_report(
    trading_date: str,
    client_id: str,
    watchlist: List[str],
) -> Dict[str, Any]:
    """Generate a watchlist-based report via API."""
    return _make_request(
        "POST",
        "/reports/generate/watchlist",
        data={
            "trading_date": trading_date,
            "client_id": client_id,
            "watchlist": watchlist,
        },
    )


def send_chat_message(message: str) -> str:
    """Send a chat message via API."""
    response = _make_request(
        "POST",
        "/chat/message",
        data={"message": message},
    )
    return response.get("response", "I couldn't generate a response.")


def get_health_status() -> Dict[str, Any]:
    """Get system health status via API."""
    try:
        return _make_request("GET", "/health")
    except APIError:
        return {"status": "unhealthy", "components": {}}


def list_reports(
    client_id: Optional[str] = None,
    limit: int = 50,
    start_after: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List reports - this would need to be implemented in the API.
    For now, we'll use Firestore directly in Streamlit for listing.
    """
    # This endpoint doesn't exist yet in the API, so we'll handle it differently
    # For now, return empty list - will be handled by direct Firestore access
    return []


"""
Repository module for Firestore data access in the Michael Brooks trading assistant app.

This module provides a clean interface for managing:
- Clients (collection: 'clients')
- Daily reports (collection: 'daily_reports')
- Ticker summaries (collection: 'ticker_summaries')
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict

from google.cloud import firestore
from gcp_clients import get_firestore_client
from utils.cache_utils import cache_firestore_query, _memory_cache_instance, _generate_cache_key


# ---------------------------------------------------------------------------
# Optional Data Models (for type safety)
# ---------------------------------------------------------------------------

@dataclass
class Client:
    """Data model for a client document."""
    email: str
    name: str
    timezone: str
    preferences: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore storage."""
        result = {
            "email": self.email,
            "name": self.name,
            "timezone": self.timezone,
        }
        if self.preferences is not None:
            result["preferences"] = self.preferences
        return result


@dataclass
class DailyReport:
    """Data model for a daily report document."""
    client_id: str
    trading_date: str  # ISO date format: "2025-12-03"
    tickers: List[str]
    summary_text: str
    created_at: Optional[datetime] = None
    key_insights: Optional[List[str]] = None
    market_context: Optional[Dict[str, Any] | str] = None
    audio_gcs_path: Optional[str] = None
    email_status: str = "pending"  # "pending", "sent", "failed"
    raw_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore storage."""
        result = {
            "client_id": self.client_id,
            "trading_date": self.trading_date,
            "tickers": self.tickers,
            "summary_text": self.summary_text,
            "email_status": self.email_status,
        }
        if self.created_at is not None:
            result["created_at"] = self.created_at
        if self.key_insights is not None:
            result["key_insights"] = self.key_insights
        if self.market_context is not None:
            result["market_context"] = self.market_context
        if self.audio_gcs_path is not None:
            result["audio_gcs_path"] = self.audio_gcs_path
        if self.raw_payload is not None:
            result["raw_payload"] = self.raw_payload
        return result


@dataclass
class TickerSummary:
    """Data model for a ticker summary document."""
    ticker: str
    latest_snapshot: Dict[str, Any]
    last_updated: Optional[datetime] = None
    last_report_date: Optional[str] = None  # ISO date format
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore storage."""
        result = {
            "ticker": self.ticker,
            "latest_snapshot": self.latest_snapshot,
        }
        if self.last_updated is not None:
            result["last_updated"] = self.last_updated
        if self.last_report_date is not None:
            result["last_report_date"] = self.last_report_date
        if self.notes is not None:
            result["notes"] = self.notes
        return result


# ---------------------------------------------------------------------------
# Repository Functions
# ---------------------------------------------------------------------------

@cache_firestore_query(ttl_seconds=600)  # Cache for 10 minutes
def get_client(client_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a client document from Firestore.

    Args:
        client_id: The document ID in the 'clients' collection (e.g., "michael_brooks").

    Returns:
        A dictionary containing the client data (including 'id' field), or None if the document doesn't exist.
    """
    db = get_firestore_client()
    doc_ref = db.collection("clients").document(client_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def upsert_client(
    client_id: str,
    email: str,
    name: str,
    timezone: str,
    preferences: Optional[Dict[str, Any]] = None
) -> None:
    """
    Create or update a client document in Firestore.

    Args:
        client_id: The document ID in the 'clients' collection (e.g., "michael_brooks").
        email: The client's email address.
        name: The client's name.
        timezone: The client's timezone (e.g., "America/Los_Angeles").
        preferences: Optional dictionary for future expansion (e.g., delivery time, tickers of interest).
    """
    db = get_firestore_client()
    doc_ref = db.collection("clients").document(client_id)
    
    data = {
        "email": email,
        "name": name,
        "timezone": timezone,
    }
    
    if preferences is not None:
        data["preferences"] = preferences
    
    doc_ref.set(data)
    
    # Invalidate cache for this client_id
    cache_key = _generate_cache_key("firestore_get_client", client_id)
    _memory_cache_instance.delete(cache_key)


def create_or_update_daily_report(report: Dict[str, Any]) -> None:
    """
    Create or update a daily report document in Firestore.

    Uses the 'trading_date' field as the document ID in the 'daily_reports' collection.
    Automatically sets 'created_at' timestamp if not provided.

    Args:
        report: A dictionary containing at least:
            - trading_date (str): ISO date format (e.g., "2025-12-03")
            - client_id (str): Reference to the client document ID
            - summary_text (str): The main textual report
            - tickers (list of str): Tickers covered in this report
            Optional fields:
            - key_insights (list of str)
            - market_context (dict or str)
            - audio_gcs_path (str)
            - email_status (str, default: "pending")
            - raw_payload (dict)
            - created_at (datetime, will be set automatically if not provided)
    """
    db = get_firestore_client()
    trading_date = report.get("trading_date")
    
    if not trading_date:
        raise ValueError("report must contain 'trading_date' field")
    
    doc_ref = db.collection("daily_reports").document(trading_date)
    
    # Prepare data with defaults
    data = {
        "client_id": report.get("client_id"),
        "trading_date": trading_date,
        "tickers": report.get("tickers", []),
        "summary_text": report.get("summary_text", ""),
        "email_status": report.get("email_status", "pending"),
    }
    
    # Set created_at if not provided
    if "created_at" not in report:
        data["created_at"] = datetime.now(timezone.utc)
    else:
        data["created_at"] = report["created_at"]
    
    # Add optional fields if present
    if "key_insights" in report:
        data["key_insights"] = report["key_insights"]
    if "market_context" in report:
        data["market_context"] = report["market_context"]
    if "audio_gcs_path" in report:
        data["audio_gcs_path"] = report["audio_gcs_path"]
    if "raw_payload" in report:
        data["raw_payload"] = report["raw_payload"]
    
    doc_ref.set(data)
    
    # Invalidate cache for this trading_date
    cache_key = _generate_cache_key("firestore_get_daily_report", trading_date)
    _memory_cache_instance.delete(cache_key)


@cache_firestore_query(ttl_seconds=300)  # Cache for 5 minutes
def get_daily_report(trading_date: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a daily report document from Firestore.

    Args:
        trading_date: The ISO date string used as the document ID (e.g., "2025-12-03").

    Returns:
        A dictionary containing the report data (including 'id' field), or None if the document doesn't exist.
    """
    db = get_firestore_client()
    doc_ref = db.collection("daily_reports").document(trading_date)
    doc = doc_ref.get()
    
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    data["id"] = doc.id
    return data


@cache_firestore_query(ttl_seconds=180)  # Cache for 3 minutes (shorter since it's a list)
def list_daily_reports(
    client_id: Optional[str] = None,
    limit: int = 50,
    order_by: str = "trading_date",
    descending: bool = True,
    start_after: Optional[str] = None
) -> Dict[str, Any]:
    """
    List daily reports from Firestore with optional filtering, pagination, and optimization.
    
    Args:
        client_id: Optional client ID to filter by. If None, returns all reports.
        limit: Maximum number of reports to return (default: 50, max: 100)
        order_by: Field to order by (default: "trading_date")
        descending: Whether to sort in descending order (default: True)
        start_after: Trading date to start after (for pagination)
        
    Returns:
        Dictionary with:
            - 'reports': List of report dictionaries
            - 'has_more': Boolean indicating if more results are available
            - 'last_date': Last trading_date in results (for pagination)
            - 'count': Number of reports returned
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Enforce max limit for performance
        limit = min(limit, 100)
        
        db = get_firestore_client()
        query = db.collection("daily_reports")
        
        # Filter by client_id if provided (creates index requirement)
        if client_id:
            query = query.where("client_id", "==", client_id)
        
        # Order by specified field (requires composite index if filtering)
        direction = firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
        
        # Use trading_date as primary sort (it's the document ID, so very efficient)
        if order_by == "trading_date":
            # Document ID ordering is most efficient
            if start_after:
                query = query.start_after({order_by: start_after})
            query = query.order_by(order_by, direction=direction)
        else:
            # For other fields, need to order by that field
            query = query.order_by(order_by, direction=direction)
            if start_after:
                # For non-ID fields, pagination is more complex
                # This is a simplified version
                pass
        
        # Limit results
        query = query.limit(limit + 1)  # Fetch one extra to check if more exists
        
        # Execute query
        docs = list(query.stream())
        
        # Check if there are more results
        has_more = len(docs) > limit
        if has_more:
            docs = docs[:limit]  # Remove the extra one
        
        reports = []
        last_date = None
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            reports.append(data)
            # Track last date for pagination
            if order_by == "trading_date":
                last_date = data.get("trading_date")
        
        logger.info("Listed %d reports (has_more: %s)", len(reports), has_more)
        
        return {
            "reports": reports,
            "has_more": has_more,
            "last_date": last_date,
            "count": len(reports)
        }
        
    except Exception as e:
        # Log error but return empty result to prevent UI crashes
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Error listing daily reports: %s", str(e), exc_info=True)
        return {
            "reports": [],
            "has_more": False,
            "last_date": None,
            "count": 0,
            "error": str(e)
        }


def update_daily_report_email_status(trading_date: str, status: str) -> None:
    """
    Update only the 'email_status' field of a daily report.

    Args:
        trading_date: The ISO date string used as the document ID (e.g., "2025-12-03").
        status: The new email status (e.g., "pending", "sent", "failed").
    """
    db = get_firestore_client()
    doc_ref = db.collection("daily_reports").document(trading_date)
    doc_ref.update({"email_status": status})
    
    # Invalidate cache for this trading_date
    cache_key = _generate_cache_key("firestore_get_daily_report", trading_date)
    _memory_cache_instance.delete(cache_key)


def update_daily_report_audio_path(trading_date: str, audio_gcs_path: str) -> None:
    """
    Update only the 'audio_gcs_path' field of a daily report.

    Args:
        trading_date: The ISO date string used as the document ID (e.g., "2025-12-03").
        audio_gcs_path: The GCS object path for the audio file (e.g., "gs://<bucket>/reports/2025-12-03/audio.mp3").
    """
    db = get_firestore_client()
    doc_ref = db.collection("daily_reports").document(trading_date)
    doc_ref.update({"audio_gcs_path": audio_gcs_path})
    
    # Invalidate cache for this trading_date
    cache_key = _generate_cache_key("firestore_get_daily_report", trading_date)
    _memory_cache_instance.delete(cache_key)


def upsert_ticker_summary(
    ticker: str,
    latest_snapshot: Dict[str, Any],
    notes: Optional[str] = None
) -> None:
    """
    Create or update a ticker summary document in Firestore.

    Args:
        ticker: The ticker symbol (e.g., "SMCI", "NBIS") used as the document ID.
        latest_snapshot: Dictionary containing the latest structured data snapshot (OHLC, volume, etc.).
        notes: Optional free-form notes from analysis.
    """
    db = get_firestore_client()
    doc_ref = db.collection("ticker_summaries").document(ticker)
    
    data = {
        "ticker": ticker,
        "latest_snapshot": latest_snapshot,
        "last_updated": datetime.now(timezone.utc),
    }
    
    if notes is not None:
        data["notes"] = notes
    
    doc_ref.set(data)


def get_ticker_summary(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a ticker summary document from Firestore.

    Args:
        ticker: The ticker symbol used as the document ID (e.g., "SMCI").

    Returns:
        A dictionary containing the ticker summary data (including 'id' field), or None if the document doesn't exist.
    """
    db = get_firestore_client()
    doc_ref = db.collection("ticker_summaries").document(ticker)
    doc = doc_ref.get()
    
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    data["id"] = doc.id
    return data


# ---------------------------------------------------------------------------
# Manual Local Testing Only
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Manual local testing harness.
    
    This block can be used for manual testing in local dev environment.
    It will:
    1. Upsert the clients/michael_brooks document
    2. Create/update a sample daily report
    3. Fetch and print the created daily report
    """
    print("=" * 80)
    print("Manual Local Testing - report_repository.py")
    print("=" * 80)
    print()
    
    # Test 1: Upsert client
    print("1. Upserting client 'michael_brooks'...")
    try:
        upsert_client(
            client_id="michael_brooks",
            email="michael@example.com",
            name="Michael Brooks",
            timezone="America/Los_Angeles",
            preferences={
                "delivery_time": "08:00",
                "tickers_of_interest": ["SMCI", "CRWV", "NBIS", "IREN"]
            }
        )
        print("   ✓ Client upserted successfully")
    except Exception as e:
        print(f"   ✗ Error upserting client: {e}")
    
    # Test 2: Fetch client
    print("\n2. Fetching client 'michael_brooks'...")
    try:
        client = get_client("michael_brooks")
        if client:
            print(f"   ✓ Client found: {client}")
        else:
            print("   ✗ Client not found")
    except Exception as e:
        print(f"   ✗ Error fetching client: {e}")
    
    # Test 3: Create/update daily report
    print("\n3. Creating/updating daily report for '2025-12-03'...")
    try:
        sample_report = {
            "trading_date": "2025-12-03",
            "client_id": "michael_brooks",
            "summary_text": "This is a sample daily report for testing purposes. Market conditions were favorable with strong performance across data center stocks.",
            "tickers": ["SMCI", "CRWV", "NBIS", "IREN"],
            "key_insights": [
                "SMCI showed strong momentum with 5% gains",
                "CRWV experienced volatility but closed positive",
                "NBIS maintained steady performance",
                "IREN saw increased trading volume"
            ],
            "market_context": {
                "overall_sentiment": "bullish",
                "sector_performance": "strong"
            },
            "email_status": "pending"
        }
        create_or_update_daily_report(sample_report)
        print("   ✓ Daily report created/updated successfully")
    except Exception as e:
        print(f"   ✗ Error creating daily report: {e}")
    
    # Test 4: Fetch daily report
    print("\n4. Fetching daily report for '2025-12-03'...")
    try:
        report = get_daily_report("2025-12-03")
        if report:
            print(f"   ✓ Report found:")
            print(f"     - ID: {report.get('id')}")
            print(f"     - Trading Date: {report.get('trading_date')}")
            print(f"     - Client ID: {report.get('client_id')}")
            print(f"     - Tickers: {report.get('tickers')}")
            print(f"     - Email Status: {report.get('email_status')}")
            print(f"     - Summary (first 100 chars): {report.get('summary_text', '')[:100]}...")
        else:
            print("   ✗ Report not found")
    except Exception as e:
        print(f"   ✗ Error fetching report: {e}")
    
    # Test 5: Update email status
    print("\n5. Updating email status to 'sent'...")
    try:
        update_daily_report_email_status("2025-12-03", "sent")
        print("   ✓ Email status updated")
        # Verify
        report = get_daily_report("2025-12-03")
        if report:
            print(f"     Verified: email_status = {report.get('email_status')}")
    except Exception as e:
        print(f"   ✗ Error updating email status: {e}")
    
    # Test 6: Upsert ticker summary
    print("\n6. Upserting ticker summary for 'SMCI'...")
    try:
        upsert_ticker_summary(
            ticker="SMCI",
            latest_snapshot={
                "open": 150.00,
                "high": 157.50,
                "low": 149.00,
                "close": 156.25,
                "volume": 2500000,
                "percent_change": 4.17
            },
            notes="Strong performance driven by data center demand"
        )
        print("   ✓ Ticker summary upserted")
    except Exception as e:
        print(f"   ✗ Error upserting ticker summary: {e}")
    
    # Test 7: Fetch ticker summary
    print("\n7. Fetching ticker summary for 'SMCI'...")
    try:
        ticker_summary = get_ticker_summary("SMCI")
        if ticker_summary:
            print(f"   ✓ Ticker summary found: {ticker_summary}")
        else:
            print("   ✗ Ticker summary not found")
    except Exception as e:
        print(f"   ✗ Error fetching ticker summary: {e}")
    
    print("\n" + "=" * 80)
    print("Manual testing complete.")
    print("=" * 80)


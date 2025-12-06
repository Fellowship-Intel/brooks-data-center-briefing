#!/usr/bin/env python3
"""
Scheduled report generation script for Cloud Scheduler or cron.

This script can be run on a schedule to automatically generate daily reports.
"""
import os
import sys
import logging
from datetime import date, datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from report_service import generate_watchlist_daily_report
from report_repository import get_client, DEFAULT_CLIENT_ID

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Generate scheduled reports for all clients."""
    trading_date = date.today()
    
    logger.info("Starting scheduled report generation for %s", trading_date.isoformat())
    
    # Get all clients (or use default)
    # For now, generate for default client
    # In the future, you could iterate over all clients
    client_id = os.getenv("CLIENT_ID", DEFAULT_CLIENT_ID)
    
    try:
        # Get client watchlist
        client_doc = get_client(client_id)
        if not client_doc:
            logger.error("Client not found: %s", client_id)
            return 1
        
        watchlist = client_doc.get("watchlist", [])
        if not watchlist:
            logger.warning("No watchlist found for client %s. Skipping.", client_id)
            return 0
        
        logger.info("Generating report for client=%s with watchlist=%s", client_id, watchlist)
        
        # Generate report
        result = generate_watchlist_daily_report(
            trading_date=trading_date,
            client_id=client_id,
            watchlist=watchlist,
        )
        
        logger.info(
            "Report generated successfully. client=%s date=%s email_sent=%s",
            client_id,
            trading_date.isoformat(),
            result.get("email_sent", False)
        )
        
        return 0
        
    except Exception as e:
        logger.error("Failed to generate scheduled report: %s", str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())


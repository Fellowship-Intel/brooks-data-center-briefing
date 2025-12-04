#!/usr/bin/env python

"""
Run the default daily watchlist report for Michael Brooks.

Intended to be scheduled daily at 3:00 am America/Los_Angeles (PST/PDT).
"""

from datetime import date

from typing import List

import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from report_service import generate_watchlist_daily_report

from python_app.constants import DEFAULT_CLIENT_ID, DEFAULT_WATCHLIST


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    trading_date = date.today()
    logger.info("Starting scheduled daily watchlist report for %s", trading_date.isoformat())

    try:
        generate_watchlist_daily_report(
            trading_date=trading_date,
            client_id=DEFAULT_CLIENT_ID,
            watchlist=DEFAULT_WATCHLIST,
        )
    except Exception:
        logger.exception("Daily watchlist report failed")
        raise
    else:
        logger.info("Daily watchlist report completed successfully")


if __name__ == "__main__":
    main()


"""
Utility functions for determining which report date should be active based on the report generation schedule.

The report generation schedule determines when a new report becomes "active" for the day.
Reports generated after the cutoff time (e.g., 3:55am) are shown for the rest of the day
until the same time the following day.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Try to use zoneinfo (Python 3.9+) first, fallback to pytz
try:
    from zoneinfo import ZoneInfo
    _HAS_ZONEINFO = True
except ImportError:
    _HAS_ZONEINFO = False
    try:
        import pytz
        _HAS_PYTZ = True
    except ImportError:
        _HAS_PYTZ = False
        logger.warning("No timezone library available. Install pytz or use Python 3.9+ for zoneinfo.")


def _get_timezone(timezone_name: str):
    """Get timezone object, using zoneinfo or pytz."""
    if _HAS_ZONEINFO:
        try:
            return ZoneInfo(timezone_name)
        except Exception as e:
            logger.warning(f"Failed to load timezone {timezone_name} with zoneinfo: {e}")
            if _HAS_PYTZ:
                return pytz.timezone(timezone_name)
            raise
    elif _HAS_PYTZ:
        return pytz.timezone(timezone_name)
    else:
        # Fallback to UTC if no timezone library available
        logger.warning("No timezone library available. Using UTC as fallback.")
        if _HAS_ZONEINFO:
            return ZoneInfo("UTC")
        elif _HAS_PYTZ:
            return pytz.UTC
        else:
            return None


def is_after_report_cutoff_time(
    hour: int = 3,
    minute: int = 55,
    timezone_name: str = "America/Los_Angeles"
) -> bool:
    """
    Check if the current time is after the report generation cutoff time.
    
    Args:
        hour: Hour of the cutoff time (default: 3)
        minute: Minute of the cutoff time (default: 55)
        timezone_name: Timezone name (default: "America/Los_Angeles")
    
    Returns:
        True if current time is after the cutoff time, False otherwise
    """
    try:
        tz = _get_timezone(timezone_name)
        if tz is None:
            # Fallback: assume we're after cutoff if we can't determine timezone
            logger.warning("Cannot determine timezone, assuming after cutoff time")
            return True
        
        # Get current time in the specified timezone
        now = datetime.now(tz)
        
        # Create cutoff time for today
        cutoff = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If current time is after cutoff, return True
        return now >= cutoff
    except Exception as e:
        logger.error(f"Error checking cutoff time: {e}", exc_info=True)
        # Fallback: assume we're after cutoff to be safe
        return True


def get_active_report_date(
    hour: int = 3,
    minute: int = 55,
    timezone_name: str = "America/Los_Angeles"
) -> date:
    """
    Determine which report date should be active based on the current time and cutoff schedule.
    
    If current time is before the cutoff time (e.g., 3:55am), returns yesterday's date.
    If current time is after the cutoff time, returns today's date.
    
    Args:
        hour: Hour of the cutoff time (default: 3)
        minute: Minute of the cutoff time (default: 55)
        timezone_name: Timezone name (default: "America/Los_Angeles")
    
    Returns:
        The date that should be used for the active report
    """
    try:
        if is_after_report_cutoff_time(hour, minute, timezone_name):
            # After cutoff: use today's date
            return date.today()
        else:
            # Before cutoff: use yesterday's date
            return date.today() - timedelta(days=1)
    except Exception as e:
        logger.error(f"Error determining active report date: {e}", exc_info=True)
        # Fallback: use today's date
        return date.today()


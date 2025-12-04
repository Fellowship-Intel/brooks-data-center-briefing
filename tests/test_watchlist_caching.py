from datetime import date
from unittest.mock import patch

from report_service import (
    generate_watchlist_daily_report,
    _generate_watchlist_daily_report_cached,
)


def test_generate_watchlist_daily_report_cached(
    mock_gemini, mock_firestore, mock_storage, mock_tts
):
    """Test that watchlist report generation uses caching."""
    trading_date = date(2025, 1, 2)
    client_id = "michael_brooks"
    watchlist = ["IREN", "CRWV"]

    # Clear the cache before testing
    _generate_watchlist_daily_report_cached.cache_clear()

    with patch("report_service.generate_and_store_daily_report") as mocked_generate:
        mocked_generate.return_value = {"client_id": client_id, "summary_text": "OK"}

        # First call
        generate_watchlist_daily_report(trading_date, client_id, watchlist)
        # Second call; should hit cache, not call underlying pipeline again
        generate_watchlist_daily_report(trading_date, client_id, watchlist)

        assert mocked_generate.call_count == 1
    
    # Clean up: clear cache after test
    _generate_watchlist_daily_report_cached.cache_clear()


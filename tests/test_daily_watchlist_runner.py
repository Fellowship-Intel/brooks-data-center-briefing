from datetime import date

from unittest.mock import patch

from scripts.run_daily_watchlist_report import main as run_daily_main


@patch("scripts.run_daily_watchlist_report.generate_watchlist_daily_report")
def test_daily_runner_calls_generate_with_defaults(mock_generate):
    run_daily_main()

    assert mock_generate.call_count == 1
    call_args = mock_generate.call_args
    assert call_args is not None
    args, kwargs = call_args
    assert isinstance(kwargs["trading_date"], date)
    assert kwargs["client_id"] == "michael_brooks"
    assert set(kwargs["watchlist"]) == {"IREN", "CRWV", "NBIS", "MRVL"}


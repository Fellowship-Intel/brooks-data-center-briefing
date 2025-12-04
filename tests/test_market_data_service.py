from datetime import date

from python_app.services.market_data_service import fetch_watchlist_intraday_data


def test_fetch_watchlist_intraday_data_shape(monkeypatch):
    # Optionally monkeypatch yf.Tickers to avoid hitting the network in tests
    trading_date = date(2025, 1, 2)
    df = fetch_watchlist_intraday_data(["IREN", "CRWV"], trading_date)

    # Only test structure; real values may be None in mocked runs
    assert set(df.columns) == {
        "ticker",
        "last_price",
        "prev_close",
        "change_pct",
        "intraday_volatility",
        "volume",
    }


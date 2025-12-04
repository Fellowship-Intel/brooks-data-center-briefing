# python_app/services/market_data_service.py

from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import Dict, Any, List, Tuple

import logging
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def _fetch_watchlist_intraday_data_cached(
    watchlist_tuple: Tuple[str, ...],
    trading_date_iso: str,
) -> pd.DataFrame:
    """
    Internal cached function. Converts tuple back to list and date.
    """
    watchlist = list(watchlist_tuple)
    trading_date = date.fromisoformat(trading_date_iso)
    return _fetch_watchlist_intraday_data_uncached(watchlist, trading_date)


def _fetch_watchlist_intraday_data_uncached(
    watchlist: List[str],
    trading_date: date,
) -> pd.DataFrame:
    """
    Internal implementation of market data fetching.
    """
    tickers = [t.upper() for t in watchlist]
    if not tickers:
        return pd.DataFrame(columns=[
            "ticker",
            "last_price",
            "prev_close",
            "change_pct",
            "intraday_volatility",
            "volume",
        ])

    logger.info(
        "Fetching intraday market data for %s on %s",
        ",".join(tickers),
        trading_date.isoformat(),
    )

    tickers_str = " ".join(tickers)

    try:
        quotes = yf.Tickers(tickers_str)
    except Exception:
        logger.exception("Failed to fetch quotes for %s", tickers_str)
        raise

    rows: List[Dict[str, Any]] = []

    for ticker in tickers:
        info = quotes.tickers[ticker].info

        last_price = info.get("regularMarketPrice") or info.get("currentPrice")
        prev_close = info.get("previousClose")
        volume = info.get("regularMarketVolume") or info.get("volume")

        if last_price is not None and prev_close:
            change_pct = (last_price - prev_close) / prev_close * 100.0
        else:
            change_pct = None

        # Simple "volatility" proxy using day high/low if available
        day_high = info.get("dayHigh")
        day_low = info.get("dayLow")
        if day_high is not None and day_low is not None:
            intraday_volatility = (day_high - day_low) / ((day_high + day_low) / 2.0) * 100.0
        else:
            intraday_volatility = None

        rows.append(
            {
                "ticker": ticker,
                "last_price": last_price,
                "prev_close": prev_close,
                "change_pct": change_pct,
                "intraday_volatility": intraday_volatility,
                "volume": volume,
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values(
        by=["intraday_volatility", "volume"],
        ascending=[False, False],
        na_position="last",
    )

    return df


def fetch_watchlist_intraday_data(
    watchlist: List[str],
    trading_date: date,
) -> pd.DataFrame:
    """
    Fetch intraday market data for the given watchlist and date using yfinance.
    
    Results are cached based on watchlist and trading_date to reduce API calls.
    Cache size: 128 entries (approximately 4-5 days of data for typical watchlists).

    Columns returned:
    - ticker
    - last_price
    - prev_close
    - change_pct
    - intraday_volatility
    - volume
    """
    # Convert to hashable types for caching
    tickers = [t.upper() for t in watchlist]
    watchlist_tuple = tuple(sorted(tickers))
    trading_date_iso = trading_date.isoformat()
    
    return _fetch_watchlist_intraday_data_cached(watchlist_tuple, trading_date_iso)


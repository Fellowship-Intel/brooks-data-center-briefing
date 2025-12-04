"""Utility functions for data conversion."""
from dataclasses import asdict
from typing import Dict, Any, List
from .types import MarketData, NewsItem, MiniReport


def market_data_to_dict(md: MarketData) -> Dict[str, Any]:
    """Convert MarketData dataclass to dictionary."""
    return {
        'ticker': md.ticker,
        'company_name': md.company_name,
        'previous_close': md.previous_close,
        'open': md.open,
        'high': md.high,
        'low': md.low,
        'close': md.close,
        'volume': md.volume,
        'average_volume': md.average_volume,
        'percent_change': md.percent_change,
        'intraday_range': md.intraday_range,
        'market_cap': md.market_cap
    }


def news_item_to_dict(ni: NewsItem) -> Dict[str, Any]:
    """Convert NewsItem dataclass to dictionary."""
    result = {
        'ticker': ni.ticker,
        'headline': ni.headline,
        'summary': ni.summary,
        'source': ni.source,
        'time': ni.time
    }
    if ni.sentiment is not None:
        result['sentiment'] = ni.sentiment
    return result


def dict_to_market_data(data: Dict[str, Any]) -> MarketData:
    """Convert dictionary to MarketData dataclass."""
    return MarketData(
        ticker=data['ticker'],
        company_name=data['company_name'],
        previous_close=float(data.get('previous_close', 0)),
        open=float(data.get('open', 0)),
        high=float(data.get('high', 0)),
        low=float(data.get('low', 0)),
        close=float(data.get('close', 0)),
        volume=int(data.get('volume', 0)),
        average_volume=int(data.get('average_volume', 0)),
        percent_change=float(data.get('percent_change', 0)),
        intraday_range=str(data.get('intraday_range', '')),
        market_cap=str(data.get('market_cap', ''))
    )


def dict_to_news_item(data: Dict[str, Any]) -> NewsItem:
    """Convert dictionary to NewsItem dataclass."""
    return NewsItem(
        ticker=data['ticker'],
        headline=data['headline'],
        summary=data['summary'],
        source=data['source'],
        time=data['time'],
        sentiment=data.get('sentiment')
    )


def mini_report_to_dict(mr: MiniReport) -> Dict[str, Any]:
    """Convert MiniReport dataclass to dictionary."""
    return {
        'ticker': mr.ticker,
        'company_name': mr.company_name,
        'section_title': mr.section_title,
        'snapshot': mr.snapshot,
        'catalyst_and_context': mr.catalyst_and_context,
        'day_trading_lens': mr.day_trading_lens,
        'watch_next_bullets': mr.watch_next_bullets
    }






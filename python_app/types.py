from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from enum import Enum


@dataclass
class MiniReport:
    ticker: str
    company_name: str
    section_title: str
    snapshot: str
    catalyst_and_context: str
    day_trading_lens: str
    watch_next_bullets: List[str]


@dataclass
class MarketData:
    ticker: str
    company_name: str
    previous_close: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    average_volume: int
    percent_change: float
    intraday_range: str
    market_cap: str


@dataclass
class DailyReportResponse:
    report_markdown: str
    core_tickers_in_depth_markdown: str
    reports: List[MiniReport]
    audio_report: str
    updated_market_data: Optional[List[MarketData]] = None


@dataclass
class NewsItem:
    ticker: str
    headline: str
    summary: str
    source: str
    time: str
    sentiment: Optional[str] = None


@dataclass
class InputData:
    trading_date: str
    tickers_tracked: List[str]
    market_data_json: List[MarketData]
    news_json: List[NewsItem]
    macro_context: str
    constraints_or_notes: str


class AppMode(Enum):
    INPUT = 'INPUT'
    REPORT = 'REPORT'


@dataclass
class ChatMessage:
    role: str  # 'user' or 'model'
    text: str


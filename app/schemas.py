from __future__ import annotations
from typing import List, Optional, Dict, Any, Union
from datetime import date
from pydantic import BaseModel, Field

# Matches 'MiniReport' in types.ts
class MiniReport(BaseModel):
    ticker: str
    company_name: str
    section_title: str
    snapshot: str
    catalyst_and_context: str
    day_trading_lens: str
    watch_next_bullets: List[str]

# Matches 'MarketData' in types.ts
class MarketData(BaseModel):
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

# Matches 'NewsItem' in types.ts
class NewsItem(BaseModel):
    ticker: str
    headline: str
    summary: str
    source: str
    time: str
    sentiment: Optional[str] = None

# Matches 'InputData' in types.ts
# Using CamelCase aliases where necessary if frontend sends them, 
# but types.ts uses snake_case so we stick to that.
class GenerateReportRequest(BaseModel):
    trading_date: date
    tickers_tracked: List[str] = Field(default_factory=list)
    market_data_json: List[MarketData] = Field(default_factory=list)
    news_json: List[NewsItem] = Field(default_factory=list)
    macro_context: str = ""
    constraints_or_notes: str = ""
    
    # Optional client_id override (not in InputData but passed via auth or separate field)
    client_id: Optional[str] = None

# Matches 'DailyReportResponse' in types.ts
class DailyReportResponse(BaseModel):
    report_markdown: str
    core_tickers_in_depth_markdown: str
    reports: List[MiniReport]
    audio_report: str
    updated_market_data: Optional[List[MarketData]] = None
    
    # Extra fields for backend compatibility/storage but not strictly in UI minimal type
    # raw_payload: Optional[Dict[str, Any]] = None 


class WatchlistReportRequest(BaseModel):
    trading_date: Optional[date] = None
    client_id: str
    watchlist: List[str]


class WatchlistReportResponse(BaseModel):
    client_id: str
    trading_date: date
    watchlist: List[str]
    summary_text: str
    key_insights: List[str]
    audio_gcs_path: Optional[str] = None
    raw_payload: Dict[str, Any] 

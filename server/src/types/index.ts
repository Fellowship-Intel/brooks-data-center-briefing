/**
 * TypeScript interfaces matching Python dataclasses.
 */

export interface MiniReport {
  ticker: string;
  company_name: string;
  section_title: string;
  snapshot: string;
  catalyst_and_context: string;
  day_trading_lens: string;
  watch_next_bullets: string[];
}

export interface MarketData {
  ticker: string;
  company_name: string;
  previous_close: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  average_volume: number;
  percent_change: number;
  intraday_range: string;
  market_cap: string;
}

export interface DailyReportResponse {
  report_markdown: string;
  core_tickers_in_depth_markdown: string;
  reports: MiniReport[];
  audio_report: string;
  updated_market_data?: MarketData[];
}

export interface NewsItem {
  ticker: string;
  headline: string;
  summary: string;
  source: string;
  time: string;
  sentiment?: string;
}

export interface InputData {
  trading_date: string;
  tickers_tracked: string[];
  market_data_json: MarketData[];
  news_json: NewsItem[];
  macro_context: string;
  constraints_or_notes: string;
}

export interface DailyReport {
  client_id: string;
  trading_date: string; // ISO date format: "2025-12-03"
  tickers: string[];
  summary_text: string;
  created_at?: Date;
  key_insights?: string[];
  market_context?: Record<string, any> | string;
  audio_gcs_path?: string;
  email_status?: string; // "pending", "sent", "failed"
  raw_payload?: Record<string, any>;
  tts_provider?: string;
}

export interface Client {
  email: string;
  name: string;
  timezone: string;
  preferences?: Record<string, any>;
  watchlist?: string[];
}

export interface TickerSummary {
  ticker: string;
  latest_snapshot: Record<string, any>;
  last_updated?: Date;
  last_report_date?: string; // ISO date format
  notes?: string;
}


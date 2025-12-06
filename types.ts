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

export enum AppMode {
  INPUT = 'INPUT',
  REPORT = 'REPORT'
}

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
}

/**
 * Union type for error handling throughout the application
 * Covers various error formats from different sources (API, network, etc.)
 */
export type AppError = 
  | Error 
  | { message: string; name?: string; stack?: string }
  | { detail?: string; message?: string }
  | unknown;

/**
 * Helper function to extract error message from AppError
 */
export function getErrorMessage(error: AppError): string {
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'object' && error !== null) {
    const err = error as { message?: string; detail?: string };
    return err.message || err.detail || 'An unknown error occurred';
  }
  
  return 'An unknown error occurred';
}
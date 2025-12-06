import { DailyReportResponse, InputData } from '../types';
import { logger } from '../utils/logger';

// API base URL - must be set via environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL;

if (!API_BASE_URL) {
  throw new Error('VITE_API_URL environment variable is not set');
}

/**
 * Generate a daily report by calling the Node.js API.
 */
export const generateDailyReport = async (inputData: InputData): Promise<DailyReportResponse> => {
  try {
    logger.debug(`[geminiService] Generating report for ${inputData.trading_date} via ${API_BASE_URL}/reports/generate`);
    
    // Transform market_data_json array to prices dictionary format
    const prices: Record<string, { close: number; change_percent: number }> = {};
    const tickersList: string[] = [];
    
    if (inputData.market_data_json && inputData.market_data_json.length > 0) {
      inputData.market_data_json.forEach((item) => {
        const ticker = item.ticker.toUpperCase();
        tickersList.push(ticker);
        prices[ticker] = {
          close: item.close,
          change_percent: item.percent_change,
        };
      });
    } else if (inputData.tickers_tracked && inputData.tickers_tracked.length > 0) {
      // If no market data but tickers provided, use tickers list
      inputData.tickers_tracked.forEach((ticker) => {
        tickersList.push(ticker.toUpperCase());
      });
    }
    
    // Transform news_json array to ticker-keyed dictionary format
    const newsItems: Record<string, Array<{ headline: string; source: string; summary: string }>> = {};
    const macroNews: Array<{ headline: string; source: string; summary: string }> = [];
    
    if (inputData.news_json && inputData.news_json.length > 0) {
      inputData.news_json.forEach((item) => {
        const newsItem = {
          headline: item.headline,
          source: item.source || 'Unknown',
          summary: item.summary || '',
        };
        
        if (item.ticker && item.ticker.toUpperCase() !== 'MACRO') {
          const ticker = item.ticker.toUpperCase();
          if (!newsItems[ticker]) {
            newsItems[ticker] = [];
          }
          newsItems[ticker].push(newsItem);
        } else {
          // Macro news or news without specific ticker
          macroNews.push(newsItem);
        }
      });
    }
    
    // Add macro news if any
    if (macroNews.length > 0) {
      newsItems['macro'] = macroNews;
    }
    
    // Transform macro_context string to dictionary format
    const macroContext: Record<string, any> = {};
    if (inputData.macro_context) {
      // Try to parse as JSON first, otherwise treat as plain text
      try {
        const parsed = JSON.parse(inputData.macro_context);
        if (typeof parsed === 'object' && parsed !== null) {
          Object.assign(macroContext, parsed);
        } else {
          macroContext['context'] = inputData.macro_context;
        }
      } catch {
        // Not JSON, treat as plain text context
        macroContext['context'] = inputData.macro_context;
      }
    }
    
    // Add notes if provided
    if (inputData.constraints_or_notes) {
      macroContext['notes'] = inputData.constraints_or_notes;
    }
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout for report generation
    
    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}/reports/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
        body: JSON.stringify({
          trading_date: inputData.trading_date,
          client_id: 'michael_brooks',
          market_data: {
            tickers: tickersList.length > 0 ? tickersList : inputData.tickers_tracked.map(t => t.toUpperCase()),
            prices: prices,
          },
          news_items: Object.keys(newsItems).length > 0 ? newsItems : undefined,
          macro_context: Object.keys(macroContext).length > 0 ? macroContext : undefined,
        }),
      });
      clearTimeout(timeoutId);
    } catch (fetchErr: any) {
      clearTimeout(timeoutId);
      if (fetchErr.name === 'AbortError') {
        throw new Error('Request timeout - report generation took too long (over 2 minutes)');
      }
      throw fetchErr;
    }

    logger.debug(`[geminiService] Response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      let errorMessage = `API error: ${response.status} ${response.statusText}`;
      try {
        const error = await response.json();
        errorMessage = error.detail || error.message || errorMessage;
        logger.error('[geminiService] API error response:', error);
      } catch {
        // Response is not JSON
        const text = await response.text();
        logger.error('[geminiService] Non-JSON error response:', text);
      }
      throw new Error(errorMessage);
    }

    const result = await response.json();
    logger.debug('[geminiService] Report generated successfully, has raw_payload:', !!result.raw_payload);
    
    // Transform API response to match DailyReportResponse interface
    // The API returns raw_payload which contains the full report structure
    if (result.raw_payload) {
      return result.raw_payload as DailyReportResponse;
    }

    // Fallback: construct from available fields
    logger.warn('[geminiService] Response missing raw_payload, using fallback structure');
    return {
      report_markdown: result.summary_text || '',
      core_tickers_in_depth_markdown: result.market_context || '',
      reports: [],
      audio_report: '',
      updated_market_data: inputData.market_data_json,
    };
  } catch (error: any) {
    logger.error('[geminiService] Error generating daily report:', error);
    
    // Enhance error message for common issues
    if (error.message?.includes('timeout')) {
      throw new Error('Report generation timed out. The server may be overloaded or the request is too complex.');
    } else if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
      throw new Error('Network error - unable to connect to the API server. Please check if the backend is running.');
    } else if (error.message?.includes('CORS')) {
      throw new Error('CORS error - the API server may not be configured to allow requests from this origin.');
    }
    
    throw error;
  }
};

/**
 * Send a chat message to the Node.js API.
 */
export const sendChatMessage = async (message: string): Promise<string> => {
  try {
    logger.debug(`[geminiService] Sending chat message via ${API_BASE_URL}/chat/message`);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout for chat
    
    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
        body: JSON.stringify({ message }),
      });
      clearTimeout(timeoutId);
    } catch (fetchErr: any) {
      clearTimeout(timeoutId);
      if (fetchErr.name === 'AbortError') {
        throw new Error('Request timeout - chat response took too long');
      }
      throw fetchErr;
    }

    logger.debug(`[geminiService] Chat response status: ${response.status}`);

    if (!response.ok) {
      let errorMessage = `API error: ${response.status} ${response.statusText}`;
      try {
        const error = await response.json();
        errorMessage = error.detail || error.message || errorMessage;
        logger.error('[geminiService] Chat API error:', error);
      } catch {
        // Response is not JSON
      }
      throw new Error(errorMessage);
    }

    const result = await response.json();
    return result.response || "I couldn't generate a response.";
  } catch (error: any) {
    logger.error('[geminiService] Error sending chat message:', error);
    
    // Enhance error message
    if (error.message?.includes('timeout')) {
      throw new Error('Chat request timed out. Please try again.');
    } else if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
      throw new Error('Network error - unable to connect to the API server.');
    }
    
    throw error;
  }
};

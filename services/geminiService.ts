import { DailyReportResponse, InputData, AppError, getErrorMessage } from '../types';
import { logger } from '../utils/logger';

// API base URL - fallback to localhost:3000 if not set
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

/**
 * Generate a daily report by calling the Node.js API.
 */
export const generateDailyReport = async (inputData: InputData): Promise<DailyReportResponse> => {
  try {
    logger.debug(`[geminiService] Generating report for ${inputData.trading_date} via ${API_BASE_URL}/reports/generate`);
    
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
          // Optional: client_id override if needed, otherwise backend uses auth token
          // client_id: 'michael_brooks', 
          market_data_json: inputData.market_data_json,
          news_json: inputData.news_json,
          macro_context: inputData.macro_context, // Send as string
          constraints_or_notes: inputData.constraints_or_notes
        }),
      });
      clearTimeout(timeoutId);
    } catch (fetchErr: unknown) {
      clearTimeout(timeoutId);
      const error = fetchErr as AppError;
      if (error instanceof Error && error.name === 'AbortError') {
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
  } catch (error: unknown) {
    logger.error('[geminiService] Error generating daily report:', error);
    
    const err = error as AppError;
    const errorMessage = getErrorMessage(err);
    
    // Enhance error message for common issues
    if (errorMessage.includes('timeout')) {
      throw new Error('Report generation timed out. The server may be overloaded or the request is too complex.');
    } else if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
      throw new Error('Network error - unable to connect to the API server. Please check if the backend is running.');
    } else if (errorMessage.includes('CORS')) {
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
    } catch (fetchErr: unknown) {
      clearTimeout(timeoutId);
      const error = fetchErr as AppError;
      if (error instanceof Error && error.name === 'AbortError') {
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
  } catch (error: unknown) {
    logger.error('[geminiService] Error sending chat message:', error);
    
    const err = error as AppError;
    const errorMessage = getErrorMessage(err);
    
    // Enhance error message
    if (errorMessage.includes('timeout')) {
      throw new Error('Chat request timed out. Please try again.');
    } else if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
      throw new Error('Network error - unable to connect to the API server.');
    }
    
    throw error;
  }
};

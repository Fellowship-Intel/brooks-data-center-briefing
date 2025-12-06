/**
 * Gemini AI service for report generation and chat.
 */

import { GoogleGenerativeAI, ChatSession } from '@google/generative-ai';
import { SYSTEM_INSTRUCTION } from '../config/constants';
import { DailyReportResponse, InputData } from '../types';
import { accessSecretValue } from '../clients/gcpClients';
import { parseGeminiJsonResponse } from '../utils/jsonParser';
import { logger } from '../utils/logger';
import { env } from '../config/env';

// Global chat session to maintain context
// Note: This is a simple implementation. For production with multiple clients,
// consider using a Map<clientId, ChatSession> or request-scoped sessions.
let chatSession: ChatSession | null = null;
let sessionLastUsed: number = 0;
const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

/**
 * Get Gemini API key from Secret Manager or environment.
 */
async function getGeminiApiKey(): Promise<string> {
  try {
    // Try Secret Manager first
    return await accessSecretValue('GEMINI_API_KEY');
  } catch (error) {
    // Fall back to environment variable
    const apiKey = env.geminiApiKey;
    if (!apiKey) {
      throw new Error(
        'GEMINI_API_KEY not found in Secret Manager or environment variables. ' +
        'Note: Gemini API requires an API key even when using service account credentials for other GCP services.'
      );
    }
    return apiKey;
  }
}

/**
 * Get or create a Gemini model instance.
 */
async function getGeminiModel() {
  const apiKey = await getGeminiApiKey();
  const genAI = new GoogleGenerativeAI(apiKey);
  return genAI.getGenerativeModel({
    model: env.geminiModelName || 'gemini-1.5-pro',
    systemInstruction: SYSTEM_INSTRUCTION,
  });
}

/**
 * Generate a daily report using Gemini AI.
 */
export async function generateDailyReport(inputData: InputData): Promise<DailyReportResponse> {
  const hasMarketData = inputData.market_data_json && inputData.market_data_json.length > 0;
  const hasNewsData = inputData.news_json && inputData.news_json.length > 0;

  const prompt = `
    Generate today's daily briefing and audio report based on the following context.
    
    Trading Date: ${inputData.trading_date} (Use this date or the most recent trading session if today is a weekend/holiday).
    Tickers Tracked: ${inputData.tickers_tracked.join(', ')}
    Macro Context Instruction: ${inputData.macro_context}
    Constraints/Notes: ${inputData.constraints_or_notes}

    Market Data Status: ${hasMarketData ? 'Provided in JSON below' : '**MISSING/EMPTY** - You MUST use Google Search to find the latest market data (Open, High, Low, Close, Volume) for the tracked tickers.'}
    News Data Status: ${hasNewsData ? 'Provided in JSON below' : '**MISSING/EMPTY** - You MUST use Google Search to find the latest relevant news for the tracked tickers.'}

    If you perform a Google Search for market data, you MUST populate the 'updated_market_data' field in your JSON response with the values you found, so the dashboard can update its charts.

    Market Data JSON (Input):
    \`\`\`json
    ${JSON.stringify(inputData.market_data_json)}
    \`\`\`

    News JSON (Input):
    \`\`\`json
    ${JSON.stringify(inputData.news_json)}
    \`\`\`

    CRITICAL OUTPUT INSTRUCTION:
    1. You must return a SINGLE valid JSON object.
    2. Do NOT wrap it in markdown code blocks (like \`\`\`json ... \`\`\`).
    3. Do NOT include any conversational text before or after the JSON.
    4. **IMPORTANT**: Ensure all newlines inside string values (like 'report_markdown' or 'audio_report') are properly escaped as \\n. Do not produce real line breaks inside the JSON string values.
    5. **Return the JSON in a minified format (single line) if possible** to ensure parsing reliability.
    6. **CRITICAL JSON SYNTAX**: Do NOT use unescaped double quotes inside your text string values. Use single quotes (') for emphasis or titles within the text content. (e.g. use 'AI Mega-Deals' instead of "AI Mega-Deals"). If you absolutely must use a double quote inside a string value, you MUST escape it with a backslash (\\").

    The JSON object must strictly adhere to this schema:
    {
      "report_markdown": "string (The full written report in markdown format)",
      "core_tickers_in_depth_markdown": "string (The deep dive section in markdown format)",
      "reports": [
        {
          "ticker": "string",
          "company_name": "string",
          "section_title": "string",
          "snapshot": "string",
          "catalyst_and_context": "string",
          "day_trading_lens": "string",
          "watch_next_bullets": ["string"]
        }
      ],
      "audio_report": "string (The full text for the audio report, written for TTS)",
      "updated_market_data": [
         {
            "ticker": "string",
            "company_name": "string",
            "previous_close": number,
            "open": number,
            "high": number,
            "low": number,
            "close": number,
            "volume": number,
            "average_volume": number,
            "percent_change": number,
            "intraday_range": "string",
            "market_cap": "string"
         }
      ]
    }
  `;

  try {
    const model = await getGeminiModel();

    // Start a new chat session
    chatSession = model.startChat({
      history: [],
    });

    const result = await chatSession.sendMessage(prompt);
    const response = await result.response;
    const text = response.text();

    if (!text) {
      throw new Error('No response from Gemini');
    }

    // Parse JSON from response
    const parsed = parseGeminiJsonResponse(text);
    return parsed as DailyReportResponse;
  } catch (error) {
    logger.error('Error generating daily report:', error);
    throw error;
  }
}

/**
 * Clear the chat session (useful for cleanup or reset).
 */
export function clearChatSession(): void {
  chatSession = null;
  sessionLastUsed = 0;
  logger.debug('Chat session cleared');
}

/**
 * Check if chat session exists and is still valid.
 */
function isSessionValid(): boolean {
  if (!chatSession) {
    return false;
  }
  
  // Check if session has timed out
  const now = Date.now();
  if (sessionLastUsed > 0 && (now - sessionLastUsed) > SESSION_TIMEOUT_MS) {
    logger.debug('Chat session expired, clearing');
    clearChatSession();
    return false;
  }
  
  return true;
}

/**
 * Initialize a new chat session if one doesn't exist or has expired.
 */
async function ensureChatSession(): Promise<ChatSession> {
  if (isSessionValid()) {
    sessionLastUsed = Date.now();
    return chatSession!;
  }

  // Create a new session
  logger.debug('Initializing new chat session');
  const model = await getGeminiModel();
  chatSession = model.startChat({
    history: [],
  });
  sessionLastUsed = Date.now();
  return chatSession;
}

/**
 * Send a chat message and get a response.
 * 
 * If no session exists, a new one will be created automatically.
 * Sessions expire after 30 minutes of inactivity.
 */
export async function sendChatMessage(message: string): Promise<string> {
  try {
    const session = await ensureChatSession();
    const result = await session.sendMessage(message);
    const response = await result.response;
    sessionLastUsed = Date.now();
    return response.text() || "I couldn't generate a response.";
  } catch (error) {
    logger.error('Error sending chat message:', error);
    // Clear session on error to force recreation on next request
    clearChatSession();
    throw error;
  }
}


import { GoogleGenAI, Chat } from "@google/genai";
import { SYSTEM_INSTRUCTION } from '../constants';
import { DailyReportResponse, InputData } from '../types';

let ai: GoogleGenAI | null = null;
let chatSession: Chat | null = null;
let isJsonMode = false;

const initializeAI = () => {
  const apiKey = process.env.API_KEY || process.env.GEMINI_API_KEY;
  if (!apiKey) {
    console.error("API_KEY or GEMINI_API_KEY is missing from environment variables.");
    throw new Error("API Key not found");
  }
  if (!ai) {
    ai = new GoogleGenAI({ apiKey });
  }
};

export const generateDailyReport = async (inputData: InputData): Promise<DailyReportResponse> => {
  initializeAI();
  if (!ai) throw new Error("AI not initialized");

  const hasMarketData = inputData.market_data_json && inputData.market_data_json.length > 0;
  const hasNewsData = inputData.news_json && inputData.news_json.length > 0;

  const prompt = `
    Generate today's daily briefing and audio report based on the following context.
    
    Trading Date: ${inputData.trading_date} (Use this date or the most recent trading session if today is a weekend/holiday).
    Tickers Tracked: ${inputData.tickers_tracked.join(', ')}
    Macro Context Instruction: ${inputData.macro_context}
    Constraints/Notes: ${inputData.constraints_or_notes}

    Market Data Status: ${hasMarketData ? "Provided in JSON below" : "**MISSING/EMPTY** - You MUST use Google Search to find the latest market data (Open, High, Low, Close, Volume) for the tracked tickers."}
    News Data Status: ${hasNewsData ? "Provided in JSON below" : "**MISSING/EMPTY** - You MUST use Google Search to find the latest relevant news for the tracked tickers."}

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

  // We are entering JSON reporting mode
  isJsonMode = true;

  chatSession = ai.chats.create({
    model: 'gemini-2.5-flash',
    config: {
      systemInstruction: SYSTEM_INSTRUCTION,
      tools: [{ googleSearch: {} }]
    },
  });

  const response = await chatSession.sendMessage({ message: prompt });
  let text = response.text;
  
  if (!text) {
    throw new Error("No response from Gemini");
  }

  // CLEANUP: Remove common markdown fences if present
  text = text.replace(/```json/gi, '').replace(/```/g, '').trim();

  // ROBUST JSON EXTRACTION
  // Find the first '{' and the last '}' to extract the JSON object, ignoring any preamble or markdown fences.
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  
  if (start !== -1 && end !== -1) {
    text = text.substring(start, end + 1);
  } else {
    // If we can't find braces, it's definitely invalid
    console.error("No JSON object found in response:", text);
    throw new Error("Model response did not contain a valid JSON object.");
  }

  try {
    return JSON.parse(text) as DailyReportResponse;
  } catch (e) {
    console.error("Failed to parse JSON response:", text);
    throw new Error("Invalid JSON response from model. Please try again.");
  }
};

export const sendChatMessage = async (message: string): Promise<string> => {
  if (!chatSession) {
    throw new Error("Please generate a report first to establish context.");
  }

  // If we were in strict JSON mode, we should ideally transition to a more conversational config,
  // but keeping the history is more important. The system instruction handles both modes.
  // We just simply send the message now.
  
  const response = await chatSession.sendMessage({ message });
  return response.text || "I couldn't generate a response.";
};
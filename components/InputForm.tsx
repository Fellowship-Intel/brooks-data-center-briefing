import React, { useState } from 'react';
import { InputData, AppError, getErrorMessage } from '../types';
import { SAMPLE_INPUT } from '../constants';
import { FileText, Database, TrendingUp, Info, AlertCircle, Settings } from 'lucide-react';

interface InputFormProps {
  onSubmit: (data: InputData) => void;
  isLoading: boolean;
}

const InputForm: React.FC<InputFormProps> = ({ onSubmit, isLoading }) => {
  // Local state for form fields to allow free typing (especially for JSON)
  const [tradingDate, setTradingDate] = useState<string>(SAMPLE_INPUT.trading_date);
  const [tickers, setTickers] = useState<string>(SAMPLE_INPUT.tickers_tracked.join(', '));
  const [marketJsonStr, setMarketJsonStr] = useState<string>(JSON.stringify(SAMPLE_INPUT.market_data_json, null, 2));
  const [newsJsonStr, setNewsJsonStr] = useState<string>(JSON.stringify(SAMPLE_INPUT.news_json, null, 2));
  const [macroContext, setMacroContext] = useState<string>(SAMPLE_INPUT.macro_context);
  const [constraints, setConstraints] = useState<string>(SAMPLE_INPUT.constraints_or_notes);
  
  // Error state for validation
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Validate ticker format (1-5 uppercase letters/numbers)
  const validateTicker = (ticker: string): boolean => {
    return /^[A-Z0-9]{1,5}$/.test(ticker.trim().toUpperCase());
  };

  // Validate date format (YYYY-MM-DD)
  const validateDate = (dateStr: string): boolean => {
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(dateStr)) return false;
    const date = new Date(dateStr);
    return date instanceof Date && !isNaN(date.getTime());
  };

  // Validate and format JSON
  const validateAndFormatJson = (jsonStr: string, fieldName: string): { valid: boolean; formatted?: string; error?: string } => {
    if (!jsonStr.trim()) {
      return { valid: true, formatted: '[]' };
    }
    
    try {
      const parsed = JSON.parse(jsonStr);
      if (!Array.isArray(parsed)) {
        return { valid: false, error: `${fieldName} must be a JSON array` };
      }
      return { valid: true, formatted: JSON.stringify(parsed, null, 2) };
    } catch (e: unknown) {
      const error = e as AppError;
      const errorMsg = getErrorMessage(error);
      return { valid: false, error: `Invalid JSON in ${fieldName}: ${errorMsg}` };
    }
  };

  const loadSampleData = () => {
    setTradingDate(SAMPLE_INPUT.trading_date);
    setTickers(SAMPLE_INPUT.tickers_tracked.join(', '));
    setMarketJsonStr(JSON.stringify(SAMPLE_INPUT.market_data_json, null, 2));
    setNewsJsonStr(JSON.stringify(SAMPLE_INPUT.news_json, null, 2));
    setMacroContext(SAMPLE_INPUT.macro_context);
    setConstraints(SAMPLE_INPUT.constraints_or_notes);
    setJsonError(null);
    setFieldErrors({});
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setJsonError(null);
    setFieldErrors({});

    const errors: Record<string, string> = {};

    // Validate date
    if (!validateDate(tradingDate)) {
      errors.tradingDate = 'Invalid date format. Use YYYY-MM-DD';
    }

    // Validate tickers
    const tickerList = tickers.split(',').map(s => s.trim()).filter(Boolean);
    if (tickerList.length === 0) {
      errors.tickers = 'At least one ticker is required';
    } else {
      const invalidTickers = tickerList.filter(t => !validateTicker(t));
      if (invalidTickers.length > 0) {
        errors.tickers = `Invalid ticker format: ${invalidTickers.join(', ')}. Tickers must be 1-5 uppercase letters/numbers.`;
      }
    }

    // Validate and parse market data JSON
    const marketValidation = validateAndFormatJson(marketJsonStr, 'Market Data');
    if (!marketValidation.valid) {
      errors.marketJson = marketValidation.error || 'Invalid market data JSON';
    }

    // Validate and parse news JSON
    const newsValidation = validateAndFormatJson(newsJsonStr, 'News');
    if (!newsValidation.valid) {
      errors.newsJson = newsValidation.error || 'Invalid news JSON';
    }

    // If there are field errors, show them and stop
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    try {
      let marketData: any[] = [];
      let newsData: any[] = [];

      // Parse JSON fields (already validated)
      if (marketJsonStr.trim()) {
        marketData = JSON.parse(marketJsonStr);
      }

      if (newsJsonStr.trim()) {
        newsData = JSON.parse(newsJsonStr);
      }

      // Validate market data structure if provided
      if (marketData.length > 0) {
        const requiredFields = ['ticker', 'close', 'percent_change'];
        for (const item of marketData) {
          for (const field of requiredFields) {
            if (!(field in item)) {
              throw new Error(`Market data item missing required field: ${field}`);
            }
          }
        }
      }

      // Validate news data structure if provided
      if (newsData.length > 0) {
        const requiredFields = ['headline', 'summary'];
        for (const item of newsData) {
          for (const field of requiredFields) {
            if (!(field in item)) {
              throw new Error(`News item missing required field: ${field}`);
            }
          }
        }
      }

      onSubmit({
        trading_date: tradingDate,
        tickers_tracked: tickerList.map(t => t.toUpperCase()),
        market_data_json: marketData,
        news_json: newsData,
        macro_context: macroContext,
        constraints_or_notes: constraints,
      });
    } catch (e: unknown) {
      const error = e as AppError;
      const errorMsg = getErrorMessage(error);
      setJsonError(errorMsg || "Invalid data provided. Please check all fields.");
    }
  };

  // Auto-format JSON on blur
  const handleJsonBlur = (field: 'market' | 'news') => {
    const jsonStr = field === 'market' ? marketJsonStr : newsJsonStr;
    const fieldName = field === 'market' ? 'Market Data' : 'News';
    const validation = validateAndFormatJson(jsonStr, fieldName);
    
    if (validation.valid && validation.formatted) {
      if (field === 'market') {
        setMarketJsonStr(validation.formatted);
      } else {
        setNewsJsonStr(validation.formatted);
      }
      // Clear any previous errors for this field
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field === 'market' ? 'marketJson' : 'newsJson'];
        return newErrors;
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8 animate-in fade-in duration-500 pb-20">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-emerald-400 tracking-tight">Daily Briefing Generator</h1>
        <p className="text-slate-400">Enter market data to generate today's briefing package.</p>
        <button
          type="button"
          onClick={loadSampleData}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-emerald-300 text-sm font-medium rounded transition-colors border border-slate-700"
        >
          Reset to Defaults
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Row 1: Date & Tickers */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-bold text-slate-300 flex items-center gap-2">
              <Info size={16} className="text-emerald-500" /> Trading Date
            </label>
            <input
              type="date"
              required
              value={tradingDate}
              onChange={(e) => {
                setTradingDate(e.target.value);
                setFieldErrors(prev => {
                  const newErrors = { ...prev };
                  delete newErrors.tradingDate;
                  return newErrors;
                });
              }}
              className={`w-full bg-slate-900 border rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none ${
                fieldErrors.tradingDate ? 'border-red-600' : 'border-slate-700'
              }`}
              aria-label="Trading date"
              aria-describedby={fieldErrors.tradingDate ? "trading-date-error" : "trading-date-help"}
              aria-invalid={!!fieldErrors.tradingDate}
            />
            {fieldErrors.tradingDate && (
              <p id="trading-date-error" className="text-xs text-red-400" role="alert">{fieldErrors.tradingDate}</p>
            )}
            <p id="trading-date-help" className="text-xs text-slate-500">Example: 2025-12-01</p>
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-bold text-slate-300 flex items-center gap-2">
              <TrendingUp size={16} className="text-emerald-500" /> Tickers Tracked
            </label>
             <textarea
              rows={2}
              placeholder="EQIX, DLR, AMZN, MSFT, NVDA, SMCI, IRM, GDS, CRVW, NBIS, IREN"
              value={tickers}
              onChange={(e) => {
                setTickers(e.target.value);
                setFieldErrors(prev => {
                  const newErrors = { ...prev };
                  delete newErrors.tickers;
                  return newErrors;
                });
              }}
              className={`w-full bg-slate-900 border rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none resize-none ${
                fieldErrors.tickers ? 'border-red-600' : 'border-slate-700'
              }`}
            />
            {fieldErrors.tickers && (
              <p className="text-xs text-red-400">{fieldErrors.tickers}</p>
            )}
            <p className="text-xs text-slate-500">Must always include SMCI, CRVW, NBIS, IREN. Comma-separated list.</p>
          </div>
        </div>

        {/* Row 2: Market Data JSON */}
        <div className="space-y-2">
          <label className="text-sm font-bold text-slate-300 flex items-center gap-2">
            <Database size={16} className="text-emerald-500" /> Market Data JSON
          </label>
           <p className="text-xs text-slate-500 mb-1">Full per-ticker market data JSON. Leave as [] to auto-fetch.</p>
          <textarea
            rows={8}
            placeholder='[] (Leave empty to fetch live data via AI)'
            value={marketJsonStr}
            onChange={(e) => {
              setMarketJsonStr(e.target.value);
              setFieldErrors(prev => {
                const newErrors = { ...prev };
                delete newErrors.marketJson;
                return newErrors;
              });
            }}
            onBlur={() => handleJsonBlur('market')}
            onPaste={() => {
              // Auto-format pasted JSON
              setTimeout(() => handleJsonBlur('market'), 100);
            }}
            className={`w-full bg-slate-900 border rounded-lg p-3 text-slate-300 font-mono text-xs focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none leading-relaxed ${
              fieldErrors.marketJson ? 'border-red-600' : 'border-slate-700'
            }`}
          />
          {fieldErrors.marketJson && (
            <p className="text-xs text-red-400">{fieldErrors.marketJson}</p>
          )}
        </div>

        {/* Row 3: News Data JSON */}
        <div className="space-y-2">
          <label className="text-sm font-bold text-slate-300 flex items-center gap-2">
            <FileText size={16} className="text-emerald-500" /> News JSON
          </label>
          <p className="text-xs text-slate-500 mb-1">Array of news items. Leave as [] to auto-fetch.</p>
          <textarea
            rows={8}
            placeholder='[] (Leave empty to fetch live data via AI)'
            value={newsJsonStr}
            onChange={(e) => {
              setNewsJsonStr(e.target.value);
              setFieldErrors(prev => {
                const newErrors = { ...prev };
                delete newErrors.newsJson;
                return newErrors;
              });
            }}
            onBlur={() => handleJsonBlur('news')}
            onPaste={() => {
              // Auto-format pasted JSON
              setTimeout(() => handleJsonBlur('news'), 100);
            }}
            className={`w-full bg-slate-900 border rounded-lg p-3 text-slate-300 font-mono text-xs focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none leading-relaxed ${
              fieldErrors.newsJson ? 'border-red-600' : 'border-slate-700'
            }`}
          />
          {fieldErrors.newsJson && (
            <p className="text-xs text-red-400">{fieldErrors.newsJson}</p>
          )}
        </div>

        {/* Row 4: Macro & Constraints */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-bold text-slate-300 flex items-center gap-2">
               <Settings size={16} className="text-emerald-500" /> Macro Context
            </label>
            <textarea
              rows={4}
              placeholder="Tech sold off after hawkish Fed comments..."
              value={macroContext}
              onChange={(e) => setMacroContext(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none resize-none"
            />
          </div>
           <div className="space-y-2">
            <label className="text-sm font-bold text-slate-300 flex items-center gap-2">
               <AlertCircle size={16} className="text-emerald-500" /> Constraints or Notes
            </label>
            <textarea
              rows={4}
              placeholder="Focus more on IPOs today..."
              value={constraints}
              onChange={(e) => setConstraints(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none resize-none"
            />
          </div>
        </div>

        {jsonError && (
            <div className="p-3 bg-red-900/30 border border-red-800 rounded text-red-300 text-sm text-center">
                {jsonError}
            </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-bold rounded-lg shadow-lg shadow-emerald-900/20 transition-all flex items-center justify-center gap-2 border border-transparent disabled:border-slate-700"
          aria-label={isLoading ? "Generating report, please wait" : "Generate daily briefing package"}
          aria-busy={isLoading}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating Analysis...
            </>
          ) : (
            'Generate Daily Briefing Package'
          )}
        </button>
      </form>
    </div>
  );
};

export default InputForm;

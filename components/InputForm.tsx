import React, { useState } from 'react';
import { InputData } from '../types';
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
  
  // Error state for JSON validation
  const [jsonError, setJsonError] = useState<string | null>(null);

  const loadSampleData = () => {
    setTradingDate(SAMPLE_INPUT.trading_date);
    setTickers(SAMPLE_INPUT.tickers_tracked.join(', '));
    setMarketJsonStr(JSON.stringify(SAMPLE_INPUT.market_data_json, null, 2));
    setNewsJsonStr(JSON.stringify(SAMPLE_INPUT.news_json, null, 2));
    setMacroContext(SAMPLE_INPUT.macro_context);
    setConstraints(SAMPLE_INPUT.constraints_or_notes);
    setJsonError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setJsonError(null);

    try {
      let marketData: any[] = [];
      let newsData: any[] = [];

      // Parse JSON fields
      if (marketJsonStr.trim()) {
        const parsedMarket = JSON.parse(marketJsonStr);
        if (Array.isArray(parsedMarket)) {
          marketData = parsedMarket;
        } else {
          throw new Error("Market Data JSON must be an array");
        }
      }

      if (newsJsonStr.trim()) {
        const parsedNews = JSON.parse(newsJsonStr);
        if (Array.isArray(parsedNews)) {
          newsData = parsedNews;
        } else {
          throw new Error("News JSON must be an array");
        }
      }

      onSubmit({
        trading_date: tradingDate,
        tickers_tracked: tickers.split(',').map(s => s.trim()).filter(Boolean),
        market_data_json: marketData,
        news_json: newsData,
        macro_context: macroContext,
        constraints_or_notes: constraints,
      });
    } catch (e: any) {
      setJsonError(e.message || "Invalid JSON provided. Please check the Market Data or News JSON fields.");
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
              onChange={(e) => setTradingDate(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
            />
             <p className="text-xs text-slate-500">Example: 2025-12-01</p>
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-bold text-slate-300 flex items-center gap-2">
              <TrendingUp size={16} className="text-emerald-500" /> Tickers Tracked
            </label>
             <textarea
              rows={2}
              placeholder="EQIX, DLR, AMZN, MSFT, NVDA, SMCI, IRM, GDS, CRVW, NBIS, IREN"
              value={tickers}
              onChange={(e) => setTickers(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none resize-none"
            />
            <p className="text-xs text-slate-500">Must always include SMCI, CRVW, NBIS, IREN.</p>
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
            onChange={(e) => setMarketJsonStr(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-300 font-mono text-xs focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none leading-relaxed"
          />
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
            onChange={(e) => setNewsJsonStr(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-300 font-mono text-xs focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none leading-relaxed"
          />
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

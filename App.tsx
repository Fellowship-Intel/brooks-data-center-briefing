import React, { useState, useEffect } from 'react';
import InputForm from './components/InputForm';
import ReportView from './components/ReportView';
import ChatInterface from './components/ChatInterface';
import { generateDailyReport } from './services/geminiService';
import { InputData, DailyReportResponse, AppMode } from './types';
import { MessageSquare, Loader2 } from 'lucide-react';
import { SAMPLE_INPUT } from './constants';

const App: React.FC = () => {
  const [mode, setMode] = useState<AppMode>(AppMode.INPUT);
  const [reportData, setReportData] = useState<DailyReportResponse | null>(null);
  const [marketDataInput, setMarketDataInput] = useState<any[]>(SAMPLE_INPUT.market_data_json);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [showChat, setShowChat] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Auto-generate report on client sign on (mount)
  useEffect(() => {
    const initReport = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await generateDailyReport(SAMPLE_INPUT);
        setReportData(response);
        
        // CRITICAL FIX: If the AI fetched new market data, update the state so charts render
        if (response.updated_market_data && response.updated_market_data.length > 0) {
            setMarketDataInput(response.updated_market_data);
        }

        setMode(AppMode.REPORT);
      } catch (err: any) {
        console.error("Auto-init failed:", err);
        const errorMessage = err.message || "Failed to initialize report";
        
        // Check if it's an API key error
        if (errorMessage.includes("API Key") || errorMessage.includes("API_KEY")) {
          setError("API Key not found. Please check your .env file and ensure GEMINI_API_KEY is set.");
        } else {
          setError(`Initialization failed: ${errorMessage}. You can still create a new report manually.`);
        }
        
        // Fallback to input mode if auto-gen fails
        setMode(AppMode.INPUT);
      } finally {
        setIsLoading(false);
        setIsInitializing(false);
      }
    };
    initReport();
  }, []);

  const handleGenerateReport = async (inputData: InputData) => {
    setIsLoading(true);
    setError(null);
    
    // Default to the input provided, but override if AI fetches better data
    setMarketDataInput(inputData.market_data_json);
    
    try {
      const response = await generateDailyReport(inputData);
      setReportData(response);

      // CRITICAL FIX: If the AI fetched new market data, update the state so charts render
      if (response.updated_market_data && response.updated_market_data.length > 0) {
          setMarketDataInput(response.updated_market_data);
      }

      setMode(AppMode.REPORT);
    } catch (err: any) {
      setError(err.message || "An error occurred generating the report.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isInitializing) {
      return (
          <div className="h-screen w-screen flex flex-col items-center justify-center bg-zinc-950 text-emerald-500 gap-4">
              <Loader2 size={48} className="animate-spin" />
              <h1 className="text-2xl font-bold tracking-widest uppercase">Brooks Data Center Briefing</h1>
              <p className="text-zinc-500 text-sm animate-pulse">Initializing Market Intelligence...</p>
          </div>
      )
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-zinc-950 text-zinc-200 overflow-hidden font-sans">
      {/* Top Navigation Bar (Only visible in report mode or when loading) */}
      {mode === AppMode.REPORT && (
        <header className="h-16 border-b border-zinc-800 bg-zinc-900/95 backdrop-blur-md flex items-center justify-between px-6 shrink-0 z-10 shadow-md shadow-black/20">
          <div className="flex items-center gap-4">
             <div>
                <h1 className="text-lg font-bold text-zinc-100 tracking-tight leading-tight">Daily Briefing for Michael Brooks</h1>
             </div>
          </div>
          <div className="flex items-center gap-4">
             <button 
               onClick={() => setMode(AppMode.INPUT)}
               className="text-xs font-medium text-zinc-400 hover:text-emerald-400 transition-colors px-3 py-1.5 rounded-md hover:bg-zinc-800"
             >
               New Report
             </button>
             <div className="h-6 w-px bg-zinc-800"></div>
             <button 
               onClick={() => setShowChat(!showChat)}
               className={`p-2.5 rounded-full transition-all duration-300 ${showChat ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/50 ring-2 ring-emerald-500/20' : 'bg-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-700'}`}
               title="Toggle Analyst Q&A"
             >
               <MessageSquare size={18} />
             </button>
          </div>
        </header>
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex overflow-hidden relative">
        {mode === AppMode.INPUT ? (
          <div className="w-full h-full overflow-y-auto">
            {error && (
              <div className="max-w-4xl mx-auto mt-6 p-4 bg-red-900/20 border border-red-800 text-red-200 rounded-lg text-center flex items-center justify-center gap-2">
                <Loader2 className="animate-spin" size={16} />
                {error}
              </div>
            )}
            <InputForm onSubmit={handleGenerateReport} isLoading={isLoading} />
          </div>
        ) : (
          <>
            {/* Report View */}
            <div className={`flex-1 h-full overflow-hidden transition-all duration-300 ${showChat ? 'mr-0' : ''}`}>
              {reportData && <ReportView data={reportData} marketData={marketDataInput} />}
            </div>

            {/* Chat Sidebar */}
            {showChat && (
               <div className="h-full animate-in slide-in-from-right duration-300 shadow-2xl z-20 border-l border-zinc-800">
                  <ChatInterface />
               </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default App;
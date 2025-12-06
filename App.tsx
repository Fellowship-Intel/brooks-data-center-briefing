import React, { useState, useEffect } from 'react';
import InputForm from './components/InputForm';
import ReportView from './components/ReportView';
import ChatInterface from './components/ChatInterface';
import { Dashboard } from './components/Dashboard';
import { ErrorDisplay } from './components/ErrorDisplay';
import { NetworkDiagnostics } from './components/NetworkDiagnostics';
import { generateDailyReport } from './services/geminiService';
import { InputData, DailyReportResponse, AppMode, MarketData, AppError, getErrorMessage } from './types';
import { MessageSquare, Loader2, LayoutDashboard, FileText } from 'lucide-react';
import { SAMPLE_INPUT } from './constants';
import { logger } from './utils/logger';

type Page = 'dashboard' | 'input' | 'report';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [mode, setMode] = useState<AppMode>(AppMode.INPUT);
  const [reportData, setReportData] = useState<DailyReportResponse | null>(null);
  const [marketDataInput, setMarketDataInput] = useState<MarketData[]>(SAMPLE_INPUT.market_data_json);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [showChat, setShowChat] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<{ message: string; details?: any } | null>(null);

  // Fetch today's report on launch instead of generating
  useEffect(() => {
    const fetchTodayReport = async () => {
      setIsLoading(true);
      setError(null);
      setFetchError(null);
      
      try {
        // Get today's date in YYYY-MM-DD format
        const today = new Date().toISOString().split('T')[0];
        const API_BASE_URL = import.meta.env.VITE_API_URL;
        
        if (!API_BASE_URL) {
          throw new Error('VITE_API_URL environment variable is not set');
        }
        
        logger.debug(`[App] Fetching report for ${today} from ${API_BASE_URL}`);
        
        // Try to fetch today's report with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        let response: Response;
        try {
          response = await fetch(`${API_BASE_URL}/reports/${today}`, {
            signal: controller.signal,
            headers: {
              'Content-Type': 'application/json',
            },
          });
          clearTimeout(timeoutId);
        } catch (fetchErr: unknown) {
          clearTimeout(timeoutId);
          const error = fetchErr as AppError;
          if (error instanceof Error && error.name === 'AbortError') {
            throw new Error('Request timeout - the server took too long to respond');
          }
          throw fetchErr;
        }
        
        logger.debug(`[App] Response status: ${response.status} ${response.statusText}`);
        
        if (response.ok) {
          const reportData = await response.json();
          logger.debug('[App] Report data received:', { hasRawPayload: !!reportData.raw_payload });
          
          // If report has raw_payload, use it; otherwise construct from report data
          if (reportData.raw_payload) {
            setReportData(reportData.raw_payload);
            // Update market data if available in raw_payload
            if (reportData.raw_payload.updated_market_data && reportData.raw_payload.updated_market_data.length > 0) {
              setMarketDataInput(reportData.raw_payload.updated_market_data);
            }
          } else {
            // Transform report data to match DailyReportResponse format
            setReportData({
              report_markdown: reportData.summary_text || '',
              core_tickers_in_depth_markdown: reportData.market_context || '',
              reports: reportData.key_insights?.map((insight: string, idx: number) => ({
                ticker: reportData.tickers?.[idx] || 'N/A',
                company_name: '',
                section_title: '',
                snapshot: insight,
                catalyst_and_context: '',
                day_trading_lens: '',
                watch_next_bullets: []
              })) || [],
              audio_report: '',
              updated_market_data: []
            });
          }
          
          setMode(AppMode.REPORT);
          setCurrentPage('report');
          setFetchError(null);
        } else if (response.status === 404) {
          // No report for today - show dashboard instead
          logger.debug('[App] No report found for today, showing dashboard');
          setCurrentPage('dashboard');
          setMode(AppMode.INPUT);
          setFetchError(null);
        } else {
          // Try to get error message from response
          let errorMessage = `Server error: ${response.status} ${response.statusText}`;
          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorData.message || errorMessage;
          } catch {
            // If response is not JSON, use status text
          }
          throw new Error(errorMessage);
        }
      } catch (err: unknown) {
        logger.error("[App] Failed to fetch today's report:", err);
        
        // Categorize the error
        const error = err as AppError;
        let errorMessage = getErrorMessage(error);
        const errorDetails: { originalError: AppError; networkError?: boolean; corsError?: boolean } = { originalError: error };
        
        if (errorMessage.includes('timeout')) {
          errorMessage = 'Connection timeout - the server may be slow or unreachable';
        } else if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
          errorMessage = 'Network error - unable to connect to the API server';
          errorDetails.networkError = true;
        } else if (errorMessage.includes('CORS')) {
          errorMessage = 'CORS error - the API server may not be configured to allow requests from this origin';
          errorDetails.corsError = true;
        }
        
        setFetchError({
          message: errorMessage,
          details: errorDetails,
        });
        
        // Still show dashboard, but with error message
        setCurrentPage('dashboard');
        setMode(AppMode.INPUT);
      } finally {
        setIsLoading(false);
        setIsInitializing(false);
      }
    };
    
    fetchTodayReport();
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
      setCurrentPage('report');
    } catch (err: unknown) {
      const error = err as AppError;
      setError(getErrorMessage(error) || "An error occurred generating the report.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isInitializing) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 text-emerald-500 gap-6" role="status" aria-live="polite" aria-label="Loading application">
        <div className="relative">
          <Loader2 size={64} className="animate-spin text-emerald-500" aria-hidden="true" />
          <div className="absolute inset-0 animate-ping" aria-hidden="true">
            <Loader2 size={64} className="text-emerald-500/20" />
          </div>
        </div>
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-widest uppercase bg-gradient-to-r from-emerald-400 to-emerald-600 bg-clip-text text-transparent">
            Brooks Data Center Briefing
          </h1>
          <p className="text-zinc-400 text-sm animate-pulse">Loading market intelligence...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-zinc-950 text-zinc-200 overflow-hidden font-sans">
      {/* Top Navigation Bar */}
      <header className="h-16 border-b border-zinc-800 bg-zinc-900/95 backdrop-blur-md flex items-center justify-between px-6 shrink-0 z-10 shadow-md shadow-black/20">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold text-zinc-100 tracking-tight leading-tight">
            Brooks Data Center Briefing
          </h1>
        </div>
        <nav className="flex items-center gap-2" role="navigation" aria-label="Main navigation">
          <button
            onClick={() => setCurrentPage('dashboard')}
            className={`px-4 py-2 rounded-md transition-colors ${
              currentPage === 'dashboard'
                ? 'bg-emerald-600 text-white'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
            }`}
            aria-label="Go to dashboard"
            aria-current={currentPage === 'dashboard' ? 'page' : undefined}
          >
            <LayoutDashboard size={18} className="inline mr-2" aria-hidden="true" />
            Dashboard
          </button>
          <button
            onClick={() => {
              setCurrentPage('input');
              setMode(AppMode.INPUT);
            }}
            className={`px-4 py-2 rounded-md transition-colors ${
              currentPage === 'input'
                ? 'bg-emerald-600 text-white'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
            }`}
            aria-label="Create new report"
            aria-current={currentPage === 'input' ? 'page' : undefined}
          >
            <FileText size={18} className="inline mr-2" aria-hidden="true" />
            New Report
          </button>
          {currentPage === 'report' && (
            <>
              <div className="h-6 w-px bg-zinc-800" aria-hidden="true"></div>
              <button
                onClick={() => setShowChat(!showChat)}
                className={`p-2.5 rounded-full transition-all duration-300 ${
                  showChat
                    ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/50 ring-2 ring-emerald-500/20'
                    : 'bg-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-700'
                }`}
                aria-label={showChat ? "Hide Analyst Q&A" : "Show Analyst Q&A"}
                aria-expanded={showChat}
                aria-controls="chat-interface"
              >
                <MessageSquare size={18} aria-hidden="true" />
              </button>
            </>
          )}
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex overflow-hidden relative">
        {currentPage === 'dashboard' ? (
          <div className="w-full h-full overflow-y-auto p-6">
            {fetchError && (
              <div className="mb-4">
                <ErrorDisplay
                  title="Failed to Load Today's Report"
                  message={fetchError.message}
                  error={fetchError.details}
                  onRetry={() => {
                    setIsInitializing(true);
                    window.location.reload();
                  }}
                  onDismiss={() => setFetchError(null)}
                />
              </div>
            )}
            <NetworkDiagnostics 
              apiUrl={import.meta.env.VITE_API_URL}
            />
            <div className="mt-4">
              <Dashboard onGenerateReport={() => {
                setCurrentPage('input');
                setMode(AppMode.INPUT);
              }} />
            </div>
          </div>
        ) : mode === AppMode.INPUT ? (
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
          <div className="flex flex-col h-full overflow-hidden">
            {/* Report View - takes remaining space */}
            <div className="flex-1 overflow-hidden">
              {reportData && <ReportView data={reportData} marketData={marketDataInput} />}
            </div>

            {/* Chat Interface at Bottom */}
            {showChat && (
              <div 
                id="chat-interface"
                className="h-96 border-t border-zinc-800 bg-slate-950 animate-in slide-in-from-bottom duration-300 shadow-2xl z-20 shrink-0"
                role="complementary"
                aria-label="Analyst Q&A chat"
              >
                <ChatInterface />
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
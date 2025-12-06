import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Clock, FileText, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';
import { ErrorDisplay } from './ErrorDisplay';
import { logger } from '../utils/logger';
import { AppError, getErrorMessage } from '../types';

interface DashboardStats {
  totalReports: number;
  ttsSuccessRate: number;
  avgGenerationTime: string;
  lastReportDate: string | null;
}

interface ActivityItem {
  date: string;
  client: string;
  ttsProvider: string;
  status: 'success' | 'partial' | 'failed';
  id: string;
}

interface HealthStatus {
  status: string;
  components: Record<string, { status: string; error?: string }>;
}

/**
 * Interface for report data returned from the API
 */
interface ApiReport {
  trading_date: string;
  client_id?: string;
  audio_gcs_path?: string;
  tts_provider?: string;
  summary_text?: string;
  key_insights?: string[];
  market_context?: string;
  raw_payload?: any;
  [key: string]: any; // Allow additional fields
}

const API_BASE_URL = import.meta.env.VITE_API_URL;

if (!API_BASE_URL) {
  throw new Error('VITE_API_URL environment variable is not set');
}

interface DashboardProps {
  onGenerateReport?: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onGenerateReport }) => {
  const [stats, setStats] = useState<DashboardStats>({
    totalReports: 0,
    ttsSuccessRate: 0,
    avgGenerationTime: 'N/A',
    lastReportDate: null,
  });
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ message: string; details?: any } | null>(null);

  useEffect(() => {
    fetchDashboardData();
    fetchHealthStatus();
    const interval = setInterval(() => {
      fetchHealthStatus();
    }, 60000); // Refresh every 60 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    setError(null);
    try {
      logger.debug(`[Dashboard] Fetching reports from ${API_BASE_URL}/reports`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      let response: Response;
      try {
        response = await fetch(`${API_BASE_URL}/reports?limit=100`, {
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
      
      logger.debug(`[Dashboard] Response status: ${response.status}`);
      
      if (response.ok) {
        const data = await response.json();
        const reports: ApiReport[] = data.reports || [];
        
        logger.debug(`[Dashboard] Received ${reports.length} reports`);
        
        const totalReports = reports.length;
        const reportsWithAudio = reports.filter((r: ApiReport) => r.audio_gcs_path).length;
        const ttsSuccessRate = totalReports > 0 ? (reportsWithAudio / totalReports * 100) : 0;
        const lastReport = reports.length > 0 ? reports[0] : null;
        
        setStats({
          totalReports,
          ttsSuccessRate: Math.round(ttsSuccessRate * 10) / 10,
          avgGenerationTime: 'N/A',
          lastReportDate: lastReport?.trading_date || null,
        });

        // Format activity
        const activityItems: ActivityItem[] = reports.slice(0, 10).map((report: ApiReport) => ({
          date: report.trading_date,
          client: report.client_id || 'Unknown',
          ttsProvider: report.tts_provider || 'N/A',
          status: report.audio_gcs_path ? 'success' : (report.summary_text ? 'partial' : 'failed'),
          id: report.id || report.trading_date,
        }));
        setActivity(activityItems);
        setError(null);
      } else {
        let errorMessage = `Server error: ${response.status} ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          // Response is not JSON
        }
        throw new Error(errorMessage);
      }
    } catch (err: unknown) {
      logger.error('[Dashboard] Error fetching dashboard data:', err);
      
      const error = err as AppError;
      let errorMessage = getErrorMessage(error) || 'Failed to fetch dashboard data';
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
      
      setError({
        message: errorMessage,
        details: errorDetails,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchHealthStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        const data = await response.json();
        setHealth(data);
      }
    } catch (error) {
      logger.error('Error fetching health status:', error);
      setHealth({ status: 'unhealthy', components: {} });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  const statusEmoji = {
    success: '✅',
    partial: '⚠️',
    failed: '❌',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-emerald-500">📊 Dashboard Overview</h1>
        {error && (
          <button
            onClick={fetchDashboardData}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors text-sm"
          >
            <RefreshCw size={16} />
            Retry
          </button>
        )}
      </div>
      
      {error && (
        <ErrorDisplay
          title="Failed to Load Dashboard Data"
          message={error.message}
          error={error.details}
          onRetry={fetchDashboardData}
          onDismiss={() => setError(null)}
        />
      )}

      {/* No Reports Message */}
      {stats.totalReports === 0 && (
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-8 border border-slate-700 text-center shadow-lg">
          <div className="max-w-md mx-auto space-y-4">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-2xl font-bold text-emerald-400">No Reports Yet</h2>
            <p className="text-slate-400 text-lg">Generate your first daily briefing report to get started with market intelligence.</p>
            {onGenerateReport && (
              <button 
                onClick={onGenerateReport}
                className="mt-6 px-8 py-4 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-semibold rounded-lg transition-all shadow-lg shadow-emerald-900/50 hover:shadow-xl hover:shadow-emerald-900/60 transform hover:scale-105"
              >
                Generate Today's Report
              </button>
            )}
          </div>
        </div>
      )}

      {/* Key Metrics */}
      {stats.totalReports > 0 && (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">Total Reports</p>
              <p className="text-2xl font-bold text-emerald-500 mt-1">{stats.totalReports}</p>
            </div>
            <FileText className="w-8 h-8 text-emerald-500/50" />
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">TTS Success Rate</p>
              <p className="text-2xl font-bold text-emerald-500 mt-1">{stats.ttsSuccessRate}%</p>
            </div>
            <TrendingUp className="w-8 h-8 text-emerald-500/50" />
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">Avg Generation Time</p>
              <p className="text-2xl font-bold text-emerald-500 mt-1">{stats.avgGenerationTime}</p>
            </div>
            <Clock className="w-8 h-8 text-emerald-500/50" />
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">Last Report Date</p>
              <p className="text-2xl font-bold text-emerald-500 mt-1">
                {stats.lastReportDate ? new Date(stats.lastReportDate).toLocaleDateString() : 'None'}
              </p>
            </div>
            <Activity className="w-8 h-8 text-emerald-500/50" />
          </div>
        </div>
      </div>
      )}

      {/* Recent Activity */}
      {stats.totalReports > 0 && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold text-emerald-500 mb-4">Recent Activity</h2>
          <div className="space-y-3">
            {activity.length > 0 ? (
              activity.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <span className="text-emerald-500 font-medium">{item.date}</span>
                    <span className="text-slate-400">{item.client}</span>
                    <span className="text-slate-400">TTS: {item.ttsProvider}</span>
                    <span className="text-lg">{statusEmoji[item.status]}</span>
                  </div>
                  <button className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors">
                    View
                  </button>
                </div>
              ))
            ) : (
              <p className="text-slate-400">No recent activity to display.</p>
            )}
          </div>
        </div>
      )}

      {/* System Health */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h2 className="text-xl font-bold text-emerald-500 mb-4">System Health</h2>
        {health ? (
          <div className="space-y-2">
            {health.status === 'healthy' ? (
              <div className="flex items-center gap-2 text-emerald-500">
                <CheckCircle2 className="w-5 h-5" />
                <span>All systems operational</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-amber-500">
                <AlertCircle className="w-5 h-5" />
                <span>Some systems may be experiencing issues</span>
              </div>
            )}
            <div className="mt-4 space-y-2">
              {Object.entries(health.components).map(([component, status]) => (
                <div key={component} className="flex items-center gap-2">
                  {status.status === 'healthy' ? (
                    <span className="text-emerald-500">✅ {component}</span>
                  ) : (
                    <span className="text-red-500">
                      ❌ {component}: {status.error || 'Unknown error'}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-slate-400">Loading health status...</p>
        )}
      </div>
    </div>
  );
};


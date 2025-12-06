import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';

interface NetworkDiagnosticsProps {
  apiUrl?: string;
  onStatusChange?: (connected: boolean) => void;
}

export const NetworkDiagnostics: React.FC<NetworkDiagnosticsProps> = ({
  apiUrl,
  onStatusChange,
}) => {
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [lastError, setLastError] = useState<string | null>(null);
  const [apiBaseUrl, setApiBaseUrl] = useState<string>('');

  useEffect(() => {
    const url = apiUrl || import.meta.env.VITE_API_URL;
    if (!url) {
      setLastError('VITE_API_URL environment variable is not set');
      setStatus('disconnected');
      onStatusChange?.(false);
      return;
    }
    setApiBaseUrl(url);
    checkConnection(url);
  }, [apiUrl]);

  const checkConnection = async (url: string) => {
    setStatus('checking');
    setLastError(null);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

      const response = await fetch(`${url}/health`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        setStatus('connected');
        setLastError(null);
        onStatusChange?.(true);
      } else {
        setStatus('disconnected');
        setLastError(`Server returned ${response.status}: ${response.statusText}`);
        onStatusChange?.(false);
      }
    } catch (error: any) {
      setStatus('disconnected');
      
      if (error.name === 'AbortError') {
        setLastError('Connection timeout - server may be slow or unreachable');
      } else if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
        setLastError('Network error - check if backend is running on ' + url);
      } else if (error.message?.includes('CORS')) {
        setLastError('CORS error - backend may not be configured to allow requests from this origin');
      } else {
        setLastError(error.message || 'Unknown error occurred');
      }
      
      onStatusChange?.(false);
    }
  };

  const handleRetry = () => {
    checkConnection(apiBaseUrl);
  };

  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {status === 'connected' ? (
            <>
              <Wifi className="text-emerald-500" size={18} />
              <span className="text-emerald-500 text-sm font-medium">API Connected</span>
            </>
          ) : status === 'checking' ? (
            <>
              <RefreshCw className="text-amber-500 animate-spin" size={18} />
              <span className="text-amber-500 text-sm font-medium">Checking...</span>
            </>
          ) : (
            <>
              <WifiOff className="text-red-500" size={18} />
              <span className="text-red-500 text-sm font-medium">API Disconnected</span>
            </>
          )}
        </div>
        <button
          onClick={handleRetry}
          className="text-zinc-400 hover:text-zinc-200 p-1 rounded transition-colors"
          title="Retry connection"
        >
          <RefreshCw size={16} />
        </button>
      </div>
      
      <div className="text-xs text-zinc-500 space-y-1">
        <div>API URL: <code className="text-zinc-400">{apiBaseUrl}</code></div>
        {lastError && (
          <div className="text-red-400 mt-2">
            Error: {lastError}
          </div>
        )}
      </div>
    </div>
  );
};


import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { logger } from '../utils/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * React Error Boundary component
 * Catches JavaScript errors anywhere in the child component tree
 * and displays a fallback UI instead of crashing the app
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console/error tracking service
    logger.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // In production, you could send to error tracking service here
    // errorTracking.captureException(error, { extra: errorInfo });
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  handleGoHome = (): void => {
    window.location.href = '/';
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 p-4">
          <div className="max-w-2xl w-full bg-zinc-900 border border-red-800/50 rounded-xl p-8 shadow-2xl">
            <div className="flex items-start gap-4 mb-6">
              <div className="flex-shrink-0">
                <AlertCircle className="text-red-500" size={48} />
              </div>
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-red-400 mb-2">
                  Something went wrong
                </h1>
                <p className="text-zinc-400 mb-4">
                  An unexpected error occurred. Please try refreshing the page or returning to the home page.
                </p>
                
                {this.state.error && (
                  <div className="mb-4 p-4 bg-zinc-950 rounded-lg border border-zinc-800">
                    <p className="text-sm font-mono text-red-300 mb-2">
                      {this.state.error.name}: {this.state.error.message}
                    </p>
                    {import.meta.env.DEV && this.state.errorInfo && (
                      <details className="mt-2">
                        <summary className="text-xs text-zinc-500 cursor-pointer hover:text-zinc-400">
                          Stack Trace
                        </summary>
                        <pre className="mt-2 text-xs text-zinc-600 overflow-auto max-h-48">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </details>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors flex items-center gap-2"
                aria-label="Try again"
              >
                <RefreshCw size={18} />
                Try Again
              </button>
              <button
                onClick={this.handleReload}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-lg transition-colors flex items-center gap-2"
                aria-label="Reload page"
              >
                <RefreshCw size={18} />
                Reload Page
              </button>
              <button
                onClick={this.handleGoHome}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-lg transition-colors flex items-center gap-2"
                aria-label="Go to home page"
              >
                <Home size={18} />
                Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}


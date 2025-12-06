import React from 'react';
import { AlertCircle, RefreshCw, X } from 'lucide-react';

interface ErrorDisplayProps {
  title?: string;
  message: string;
  error?: any;
  onRetry?: () => void;
  onDismiss?: () => void;
  type?: 'error' | 'warning' | 'info';
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  title,
  message,
  error,
  onRetry,
  onDismiss,
  type = 'error',
}) => {
  const getColors = () => {
    switch (type) {
      case 'warning':
        return {
          bg: 'bg-amber-900/20',
          border: 'border-amber-800',
          text: 'text-amber-200',
          icon: 'text-amber-500',
        };
      case 'info':
        return {
          bg: 'bg-blue-900/20',
          border: 'border-blue-800',
          text: 'text-blue-200',
          icon: 'text-blue-500',
        };
      default:
        return {
          bg: 'bg-red-900/20',
          border: 'border-red-800',
          text: 'text-red-200',
          icon: 'text-red-500',
        };
    }
  };

  const colors = getColors();

  return (
    <div className={`${colors.bg} ${colors.border} border rounded-lg p-4 mb-4`}>
      <div className="flex items-start gap-3">
        <AlertCircle className={`${colors.icon} flex-shrink-0 mt-0.5`} size={20} />
        <div className="flex-1 min-w-0">
          {title && (
            <h3 className={`${colors.text} font-semibold mb-1`}>{title}</h3>
          )}
          <p className={`${colors.text} text-sm`}>{message}</p>
          {error && import.meta.env.DEV && (
            <details className="mt-2">
              <summary className={`${colors.text} text-xs cursor-pointer hover:underline`}>
                Technical Details
              </summary>
              <pre className={`${colors.text} text-xs mt-2 p-2 bg-black/20 rounded overflow-auto`}>
                {JSON.stringify(error, null, 2)}
              </pre>
            </details>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {onRetry && (
            <button
              onClick={onRetry}
              className={`${colors.text} hover:${colors.icon} p-1.5 rounded transition-colors`}
              title="Retry"
            >
              <RefreshCw size={16} />
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className={`${colors.text} hover:${colors.icon} p-1.5 rounded transition-colors`}
              title="Dismiss"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};


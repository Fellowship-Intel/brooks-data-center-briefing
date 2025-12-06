/**
 * Production-safe logging utility
 * Only logs debug/warn/info in development mode
 * Always logs errors
 */

const isDev = import.meta.env.DEV;
const isProduction = import.meta.env.PROD;

export const logger = {
  /**
   * Debug logs - only in development
   */
  debug: (...args: any[]): void => {
    if (isDev) {
      console.log('[DEBUG]', ...args);
    }
  },

  /**
   * Info logs - only in development
   */
  info: (...args: any[]): void => {
    if (isDev) {
      console.info('[INFO]', ...args);
    }
  },

  /**
   * Warning logs - only in development
   */
  warn: (...args: any[]): void => {
    if (isDev) {
      console.warn('[WARN]', ...args);
    }
  },

  /**
   * Error logs - always logged (even in production)
   * In production, consider sending to error tracking service
   */
  error: (...args: any[]): void => {
    console.error('[ERROR]', ...args);
    
    // In production, you could send to error tracking service here
    if (isProduction) {
      // Example: send to error tracking service
      // errorTracking.captureException(new Error(args.join(' ')));
    }
  },
};


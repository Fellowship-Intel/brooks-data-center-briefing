/**
 * Retry utilities with exponential backoff and custom retry conditions.
 */

import { logger } from './logger';

export interface RetryOptions {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  exponentialBase?: number;
  retryOn?: (new (...args: any[]) => Error)[];
  retryOnCondition?: (error: Error) => boolean;
  onRetry?: (error: Error, attempt: number) => void;
}

const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * Retry a function with exponential backoff.
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelay = 1.0,
    maxDelay = 60.0,
    exponentialBase = 2.0,
    retryOn,
    retryOnCondition,
    onRetry,
  } = options;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      // Check if we should retry this exception
      if (retryOn && !retryOn.some(ErrorType => lastError instanceof ErrorType)) {
        logger.debug(`Exception ${lastError.constructor.name} is not in retry list`);
        throw lastError;
      }

      if (retryOnCondition && !retryOnCondition(lastError)) {
        logger.debug(`Exception ${lastError.constructor.name} does not meet retry condition`);
        throw lastError;
      }

      // Don't retry on last attempt
      if (attempt >= maxRetries) {
        logger.error(
          `Function failed after ${maxRetries + 1} attempts: ${lastError.message}`,
          { error: lastError }
        );
        throw lastError;
      }

      // Calculate delay with exponential backoff
      const delay = Math.min(
        initialDelay * Math.pow(exponentialBase, attempt),
        maxDelay
      );

      // Call retry callback if provided
      if (onRetry) {
        try {
          onRetry(lastError, attempt + 1);
        } catch (callbackError) {
          logger.warn(`Retry callback failed: ${callbackError}`);
        }
      }

      logger.warn(
        `Function failed (attempt ${attempt + 1}/${maxRetries + 1}): ${lastError.message}. Retrying in ${delay.toFixed(2)} seconds...`
      );

      await sleep(delay * 1000);
    }
  }

  throw lastError || new Error('Unknown error in retry logic');
}

/**
 * Retry decorator for async functions (API calls).
 */
export function retryOnApiError(options: RetryOptions = {}) {
  return function <T extends (...args: any[]) => Promise<any>>(
    _target: any,
    _propertyKey: string,
    descriptor: TypedPropertyDescriptor<T>
  ) {
    const originalMethod = descriptor.value!;

    descriptor.value = async function (this: any, ...args: any[]) {
      return retryWithBackoff(
        () => originalMethod.apply(this, args),
        {
          maxRetries: 3,
          initialDelay: 1.0,
          ...options,
        }
      );
    } as T;

    return descriptor;
  };
}


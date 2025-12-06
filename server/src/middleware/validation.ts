/**
 * Input validation schemas using express-validator.
 */

import { body, param, query, ValidationChain } from 'express-validator';

/**
 * Validation for POST /reports/generate
 */
export const validateGenerateReport: ValidationChain[] = [
  body('trading_date')
    .optional()
    .isISO8601()
    .withMessage('trading_date must be a valid ISO 8601 date (YYYY-MM-DD)')
    .toDate(),
  body('client_id')
    .optional()
    .isString()
    .trim()
    .isLength({ min: 1, max: 100 })
    .withMessage('client_id must be a string between 1 and 100 characters'),
  body('market_data')
    .optional()
    .isObject()
    .withMessage('market_data must be an object'),
  body('market_data.tickers')
    .optional()
    .isArray()
    .withMessage('market_data.tickers must be an array'),
  body('market_data.tickers.*')
    .optional()
    .isString()
    .trim()
    .isLength({ min: 1, max: 10 })
    .withMessage('Each ticker must be a string between 1 and 10 characters'),
  body('news_items')
    .optional()
    .isObject()
    .withMessage('news_items must be an object'),
  body('macro_context')
    .optional()
    .isObject()
    .withMessage('macro_context must be an object'),
];

/**
 * Validation for POST /reports/generate/watchlist
 */
export const validateWatchlistReport: ValidationChain[] = [
  body('trading_date')
    .optional()
    .isISO8601()
    .withMessage('trading_date must be a valid ISO 8601 date (YYYY-MM-DD)')
    .toDate(),
  body('client_id')
    .notEmpty()
    .withMessage('client_id is required')
    .isString()
    .trim()
    .isLength({ min: 1, max: 100 })
    .withMessage('client_id must be a string between 1 and 100 characters'),
  body('watchlist')
    .notEmpty()
    .withMessage('watchlist is required')
    .isArray({ min: 1, max: 50 })
    .withMessage('watchlist must be an array with 1-50 items'),
  body('watchlist.*')
    .isString()
    .trim()
    .isLength({ min: 1, max: 10 })
    .withMessage('Each watchlist item must be a string between 1 and 10 characters')
    .matches(/^[A-Z0-9]+$/)
    .withMessage('Each watchlist item must be alphanumeric uppercase'),
];

/**
 * Validation for GET /reports/:tradingDate
 */
export const validateTradingDate: ValidationChain[] = [
  param('tradingDate')
    .isISO8601()
    .withMessage('tradingDate must be a valid ISO 8601 date (YYYY-MM-DD)'),
  query('client_id')
    .optional()
    .isString()
    .trim()
    .isLength({ min: 1, max: 100 })
    .withMessage('client_id must be a string between 1 and 100 characters'),
];

/**
 * Validation for POST /chat/message
 */
export const validateChatMessage: ValidationChain[] = [
  body('message')
    .notEmpty()
    .withMessage('message is required')
    .isString()
    .trim()
    .isLength({ min: 1, max: 5000 })
    .withMessage('message must be a string between 1 and 5000 characters')
    .escape(),
];

/**
 * Validation error from express-validator
 */
export interface ValidationError {
  path?: string;
  param?: string;
  msg?: string;
  message?: string;
  value?: unknown;
}

/**
 * Formatted validation error
 */
export interface FormattedValidationError {
  field: string;
  message: string;
}

/**
 * Validation error formatter
 */
export function formatValidationErrors(errors: ValidationError[]): FormattedValidationError[] {
  return errors.map((error) => ({
    field: error.path || error.param || 'unknown',
    message: error.msg || error.message || 'Invalid value',
  }));
}


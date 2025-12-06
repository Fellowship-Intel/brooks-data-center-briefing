/**
 * Rate limiting middleware configurations.
 */

import rateLimit from 'express-rate-limit';

/**
 * Rate limiter for report generation endpoints.
 * 10 requests per 15 minutes per IP.
 */
export const reportGenerationLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10, // Limit each IP to 10 requests per windowMs
  message: {
    error: 'Too many report generation requests',
    message: 'Please try again later. Limit: 10 requests per 15 minutes.',
  },
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
});

/**
 * Rate limiter for chat endpoints.
 * 30 requests per minute per IP.
 */
export const chatLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 30, // Limit each IP to 30 requests per minute
  message: {
    error: 'Too many chat requests',
    message: 'Please try again later. Limit: 30 requests per minute.',
  },
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * Rate limiter for health check endpoint.
 * 100 requests per minute per IP.
 */
export const healthCheckLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100, // Limit each IP to 100 requests per minute
  message: {
    error: 'Too many health check requests',
    message: 'Please try again later.',
  },
  standardHeaders: true,
  legacyHeaders: false,
});


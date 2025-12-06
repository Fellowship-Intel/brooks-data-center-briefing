/**
 * Request ID middleware for request tracking.
 */

import { Request, Response, NextFunction } from 'express';
import { randomUUID } from 'crypto';

declare global {
  namespace Express {
    interface Request {
      id?: string;
    }
  }
}

/**
 * Generate and attach a unique request ID to each request.
 * Adds X-Request-ID header to response.
 */
export function requestIdMiddleware(req: Request, res: Response, next: NextFunction): void {
  const requestId = randomUUID();
  req.id = requestId;
  res.setHeader('X-Request-ID', requestId);
  next();
}


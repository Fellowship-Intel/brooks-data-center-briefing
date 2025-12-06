/**
 * Express server entry point.
 */

import express, { Request, Response, NextFunction } from 'express';
import { Server } from 'http';
import cors from 'cors';
import helmet from 'helmet';
import timeout from 'connect-timeout';
import { logger } from './utils/logger';
import { env, validateEnv } from './config/env';
import reportsRouter from './routes/reports';
import healthRouter from './routes/health';
import chatRouter from './routes/chat';
import { requestIdMiddleware } from './middleware/requestId';

// Validate environment variables on startup
try {
  validateEnv();
  logger.info('Environment validation passed');
} catch (error) {
  logger.error('Environment validation failed:', error);
  process.exit(1);
}

const app = express();

// Security headers
app.use(
  helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        scriptSrc: ["'self'"],
        imgSrc: ["'self'", 'data:', 'https:'],
      },
    },
    crossOriginEmbedderPolicy: false, // Allow CORS
  })
);

// CORS configuration - allow React and Streamlit frontends
const getAllowedOrigins = (): string | string[] => {
  if (env.environment === 'development') {
    return '*'; // Allow all in development (return as string)
  }
  
  // In production, allow specific origins (return as array)
  const origins: string[] = [];
  if (env.reactAppUrl) origins.push(env.reactAppUrl);
  if (env.streamlitAppUrl) origins.push(env.streamlitAppUrl);
  
  // In production, fail securely - require explicit origins
  if (origins.length === 0) {
    logger.warn(
      'No CORS origins configured in production. Set REACT_APP_URL and/or STREAMLIT_APP_URL environment variables.'
    );
    // Return empty array to deny all origins (more secure than '*')
    return [];
  }
  
  return origins;
};

const corsOptions = {
  origin: getAllowedOrigins(),
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
};

// Middleware
app.use(cors(corsOptions));

// Request ID middleware (must be early in the chain)
app.use(requestIdMiddleware);

// Body parsing with size limits
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logging with request ID
app.use((req: Request, _res: Response, next: NextFunction) => {
  logger.info(`${req.method} ${req.path}`, {
    requestId: req.id,
    ip: req.ip,
    userAgent: req.get('user-agent'),
  });
  next();
});

// Timeout middleware for long-running requests
app.use(timeout('5m')); // 5 minute default timeout

// Routes
app.use('/reports', reportsRouter);
app.use('/health', healthRouter);
app.use('/chat', chatRouter);

// Root endpoint
app.get('/', (req: Request, res: Response) => {
  res.json({
    name: 'Brooks Data Center Daily Briefing API',
    version: '1.0.0',
    status: 'running',
    requestId: req.id,
  });
});

// Timeout error handler
app.use((req: Request, res: Response, next: NextFunction) => {
  if (!req.timedout) {
    next();
  } else {
    logger.warn('Request timeout', { requestId: req.id, path: req.path });
    res.status(504).json({
      error: 'Gateway Timeout',
      message: 'Request exceeded maximum time limit',
      requestId: req.id,
    });
  }
});

// Payload too large error handler
app.use((err: Error & { type?: string }, req: Request, res: Response, next: NextFunction) => {
  if (err.type === 'entity.too.large') {
    logger.warn('Payload too large', { requestId: req.id, path: req.path });
    res.status(413).json({
      error: 'Payload Too Large',
      message: 'Request body exceeds maximum size limit (10MB)',
      requestId: req.id,
    });
    return;
  }
  next(err);
});

// Error handling middleware
app.use((err: Error, req: Request, res: Response, _next: NextFunction) => {
  logger.error('Unhandled error:', {
    error: err,
    requestId: req.id,
    path: req.path,
  });
  res.status(500).json({
    error: 'Internal server error',
    message: env.environment === 'development' ? err.message : 'An error occurred',
    requestId: req.id,
  });
});

// 404 handler
app.use((req: Request, res: Response) => {
  return res.status(404).json({
    error: 'Not found',
    path: req.path,
    requestId: req.id,
  });
});

// Graceful shutdown handler
let server: Server | null = null;

function gracefulShutdown(signal: string): void {
  logger.info(`Received ${signal}, starting graceful shutdown...`);
  
  if (!server) {
    logger.warn('Server instance not found, exiting immediately');
    process.exit(0);
  }

  // Stop accepting new connections
  server.close(() => {
    logger.info('HTTP server closed');
    
    // Close database connections if needed
    // (Firestore and Storage clients don't need explicit closing)
    
    logger.info('Graceful shutdown complete');
    process.exit(0);
  });

  // Force shutdown after 30 seconds
  setTimeout(() => {
    logger.error('Graceful shutdown timeout, forcing exit');
    process.exit(1);
  }, 30000);
}

// Handle shutdown signals
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Handle uncaught exceptions
process.on('uncaughtException', (error: Error) => {
  logger.error('Uncaught exception:', error);
  gracefulShutdown('uncaughtException');
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason: unknown, promise: Promise<unknown>) => {
  logger.error('Unhandled rejection:', { reason, promise });
  gracefulShutdown('unhandledRejection');
});

// Start server
const port = env.port;

try {
  server = app.listen(port, () => {
    logger.info(`Server running on port ${port}`);
    logger.info(`Environment: ${env.environment}`);
    logger.info('Server ready to accept connections');
  });

  server.on('error', (error: NodeJS.ErrnoException) => {
    if (error.code === 'EADDRINUSE') {
      logger.error(`Port ${port} is already in use. Please choose a different port.`);
      process.exit(1);
    } else if (error.code === 'EACCES') {
      logger.error(`Permission denied to bind to port ${port}. Try using a port >= 1024.`);
      process.exit(1);
    } else {
      logger.error('Server error:', error);
      process.exit(1);
    }
  });
} catch (error) {
  logger.error('Failed to start server:', error);
  process.exit(1);
}

export default app;

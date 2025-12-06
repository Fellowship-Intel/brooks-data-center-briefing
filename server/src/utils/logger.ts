/**
 * Logger configuration using Winston.
 */

import winston from 'winston';
import { env } from '../config/env';

const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.splat(),
  winston.format.json()
);

const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.printf(({ timestamp, level, message, requestId, ...meta }) => {
    let msg = `${timestamp} [${level}]`;
    if (requestId) {
      msg += ` [${requestId}]`;
    }
    msg += `: ${message}`;
    if (Object.keys(meta).length > 0) {
      msg += ` ${JSON.stringify(meta)}`;
    }
    return msg;
  })
);

export const logger = winston.createLogger({
  level: env.environment === 'production' ? 'info' : 'debug',
  format: logFormat,
  defaultMeta: { service: 'brooks-briefing-api' },
  transports: [
    new winston.transports.Console({
      format: consoleFormat,
    }),
  ],
});

// In production, also log to file
if (env.environment === 'production') {
  logger.add(
    new winston.transports.File({
      filename: 'error.log',
      level: 'error',
    })
  );
  logger.add(
    new winston.transports.File({
      filename: 'combined.log',
    })
  );
}


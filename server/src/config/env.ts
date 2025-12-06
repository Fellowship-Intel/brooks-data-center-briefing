/**
 * Environment configuration and validation.
 */

import dotenv from 'dotenv';
import { logger } from '../utils/logger';

// Load environment variables
dotenv.config();

export interface EnvConfig {
  port: number;
  projectId: string;
  reportsBucketName: string;
  geminiModelName: string;
  geminiApiKey?: string;
  elevenLabsApiKey?: string;
  elevenLabsVoiceId?: string;
  elevenLabsModelId?: string;
  environment: string;
  sentryDsn?: string;
  reactAppUrl?: string;
  streamlitAppUrl?: string;
}

export function getEnvConfig(): EnvConfig {
  return {
    port: parseInt(process.env.PORT || '8000', 10),
    projectId: process.env.GCP_PROJECT_ID || 'mikebrooks',
    reportsBucketName: process.env.REPORTS_BUCKET_NAME || 'mikebrooks-reports',
    geminiModelName: process.env.GEMINI_MODEL_NAME || 'gemini-1.5-pro',
    geminiApiKey: process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY,
    elevenLabsApiKey: process.env.ELEVEN_LABS_API_KEY,
    elevenLabsVoiceId: process.env.ELEVEN_LABS_VOICE_ID,
    elevenLabsModelId: process.env.ELEVEN_LABS_MODEL_ID,
    environment: process.env.ENVIRONMENT || 'development',
    sentryDsn: process.env.SENTRY_DSN,
    reactAppUrl: process.env.REACT_APP_URL,
    streamlitAppUrl: process.env.STREAMLIT_APP_URL,
  };
}

/**
 * Validate environment variables on startup.
 * Throws error if critical variables are missing.
 */
export function validateEnv(): void {
  const config = getEnvConfig();
  const errors: string[] = [];

  // Required variables
  if (!config.projectId || config.projectId.trim() === '') {
    errors.push('GCP_PROJECT_ID is required');
  }

  if (!config.reportsBucketName || config.reportsBucketName.trim() === '') {
    errors.push('REPORTS_BUCKET_NAME is required');
  }

  // Validate port
  if (isNaN(config.port) || config.port < 1 || config.port > 65535) {
    errors.push(`PORT must be a valid number between 1 and 65535, got: ${config.port}`);
  }

  // Warn about missing API keys (not critical if using Secret Manager)
  if (!config.geminiApiKey && config.environment === 'development') {
    logger.warn(
      '⚠️  WARNING: GEMINI_API_KEY not found in environment. ' +
      'Ensure it exists in Secret Manager or set it as an environment variable.'
    );
  }

  if (errors.length > 0) {
    throw new Error(
      `Environment validation failed:\n${errors.map(e => `  - ${e}`).join('\n')}\n\n` +
      'Please set the required environment variables and restart the server.'
    );
  }
}

export const env = getEnvConfig();

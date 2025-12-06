/**
 * Health check route.
 */

import { Router, Request, Response } from 'express';
import { getFirestoreClient, getSecretManagerClient, getBucket } from '../clients/gcpClients';
import { env } from '../config/env';
import { healthCheckLimiter } from '../middleware/rateLimiter';

const router = Router();

/**
 * GET /health
 * Comprehensive health check endpoint.
 */
router.get('/', healthCheckLimiter, async (req: Request, res: Response) => {
  const startTime = Date.now();
  const healthStatus: Record<string, any> = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    components: {},
    requestId: req.id,
  };

  // Check Firestore
  try {
    const db = getFirestoreClient();
    // Use existing 'clients' collection for health check (safer than non-existent _health)
    await db.collection('clients').limit(1).get();
    healthStatus.components.firestore = { status: 'healthy' };
  } catch (error) {
    healthStatus.components.firestore = {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : String(error),
    };
    healthStatus.status = 'unhealthy';
  }

  // Check Storage - check if specific bucket exists (requires only storage.buckets.get, not storage.buckets.list)
  try {
    const bucket = getBucket(env.reportsBucketName);
    // Try to get bucket metadata (lightweight operation that doesn't require list permission)
    await bucket.getMetadata();
    healthStatus.components.storage = { status: 'healthy' };
  } catch (error) {
    healthStatus.components.storage = {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : String(error),
    };
    healthStatus.status = 'unhealthy';
  }

  // Check Secret Manager
  try {
    getSecretManagerClient();
    // Just check if client can be created
    healthStatus.components.secret_manager = { status: 'healthy' };
  } catch (error) {
    healthStatus.components.secret_manager = {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : String(error),
    };
    healthStatus.status = 'unhealthy';
  }

  // Optional: Check external APIs (non-blocking)
  // Gemini API check - verify API key is accessible
  try {
    const { accessSecretValue } = await import('../clients/gcpClients');
    try {
      await accessSecretValue('GEMINI_API_KEY');
      healthStatus.components.gemini_api = { status: 'available' };
    } catch (error) {
      // API key not available in Secret Manager, check env var
      if (env.geminiApiKey) {
        healthStatus.components.gemini_api = { status: 'available', source: 'environment' };
      } else {
        healthStatus.components.gemini_api = { 
          status: 'unavailable', 
          note: 'API key not found in Secret Manager or environment' 
        };
      }
    }
  } catch (error) {
    // Non-critical, just mark as unknown
    healthStatus.components.gemini_api = { status: 'unknown', error: String(error) };
  }

  // Calculate response time
  const responseTime = Date.now() - startTime;
  healthStatus.responseTimeMs = responseTime;

  const statusCode = healthStatus.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(healthStatus);
});

export default router;


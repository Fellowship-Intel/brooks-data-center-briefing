/**
 * Chat/Q&A API routes.
 */

import { Router, Request, Response } from 'express';
import { validationResult } from 'express-validator';
import { sendChatMessage } from '../services/geminiService';
import { logger } from '../utils/logger';
import { validateChatMessage, formatValidationErrors } from '../middleware/validation';
import { chatLimiter } from '../middleware/rateLimiter';

const router = Router();

/**
 * POST /chat/message
 * Send a chat message and get AI response.
 */
router.post(
  '/message',
  chatLimiter,
  validateChatMessage,
  async (req: Request, res: Response) => {
    // Check validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: formatValidationErrors(errors.array()),
        requestId: req.id,
      });
    }

    try {
      const { message } = req.body;

      const response = await sendChatMessage(message);
      return res.json({ response, requestId: req.id });
    } catch (error) {
      logger.error('Chat message failed:', {
        error,
        requestId: req.id,
      });
      return res.status(500).json({
        error: 'Chat message failed',
        message: error instanceof Error ? error.message : String(error),
        requestId: req.id,
      });
    }
  }
);

export default router;


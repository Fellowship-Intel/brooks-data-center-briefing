/**
 * Report API routes.
 */

import { Router, Request, Response } from 'express';
import { validationResult } from 'express-validator';
import {
  generateAndStoreDailyReport,
  generateWatchlistDailyReport,
  getDailyReportByDate,
} from '../services/reportService';
import { logger } from '../utils/logger';
import { DEFAULT_CLIENT_ID } from '../config/constants';
import {
  validateGenerateReport,
  validateWatchlistReport,
  validateTradingDate,
  formatValidationErrors,
} from '../middleware/validation';
import { reportGenerationLimiter } from '../middleware/rateLimiter';

const router = Router();

/**
 * POST /reports/generate
 * Generate a new daily report.
 */
router.post(
  '/generate',
  reportGenerationLimiter,
  validateGenerateReport,
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
    const {
      trading_date,
      client_id = DEFAULT_CLIENT_ID,
      market_data = {},
      news_items = {},
      macro_context = {},
    } = req.body;

    const date = trading_date || new Date().toISOString().split('T')[0];

    // Use dummy data if not provided
    const marketData = market_data.tickers
      ? market_data
      : {
          tickers: ['SMCI', 'IREN'],
          market_data: [
            {
              ticker: 'SMCI',
              company_name: 'Super Micro Computer, Inc.',
              previous_close: 850.25,
              open: 855.0,
              high: 870.0,
              low: 848.0,
              close: 865.5,
              volume: 4200000,
              average_volume: 3800000,
              percent_change: 1.8,
              intraday_range: '848.0–870.0',
              market_cap: '16000000000',
            },
            {
              ticker: 'IREN',
              company_name: 'Iris Energy Limited',
              previous_close: 10.42,
              open: 10.50,
              high: 10.80,
              low: 10.30,
              close: 10.65,
              volume: 2100000,
              average_volume: 1800000,
              percent_change: 2.2,
              intraday_range: '10.30–10.80',
              market_cap: '500000000',
            },
          ],
        };

    const newsItems = news_items.news
      ? news_items
      : {
          news: [
            {
              ticker: 'SMCI',
              headline: 'Supermicro extends rally as AI server demand stays strong',
              source: 'Example Newswire',
              summary: 'Investors continue to price in sustained AI infrastructure demand.',
              time: new Date().toISOString(),
            },
          ],
        };

    const macroCtx = macro_context.context
      ? macro_context
      : {
          context: 'Broadly positive risk sentiment, with rotation into data center and AI infrastructure names.',
          notes: '',
        };

    const result = await generateAndStoreDailyReport(
      date,
      client_id,
      marketData,
      newsItems,
      macroCtx
    );

      return res.json(result);
    } catch (error) {
      logger.error('Report generation failed:', {
        error,
        requestId: req.id,
      });
      return res.status(500).json({
        error: 'Report generation failed',
        message: error instanceof Error ? error.message : String(error),
        requestId: req.id,
      });
    }
  }
);

/**
 * GET /reports/:tradingDate
 * Fetch an existing report.
 */
router.get('/:tradingDate', validateTradingDate, async (req: Request, res: Response) => {
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
    const { tradingDate } = req.params;
    const clientId = (req.query.client_id as string) || DEFAULT_CLIENT_ID;

    const report = await getDailyReportByDate(tradingDate);

    if (!report) {
      return res.status(404).json({ error: 'Report not found' });
    }

    // Check if client_id matches
    if (report.client_id && report.client_id !== clientId) {
      return res.status(404).json({ error: 'Report not found for this client' });
    }

    return res.json(report);
  } catch (error) {
    logger.error('Error loading report:', {
      error,
      requestId: req.id,
    });
    return res.status(500).json({
      error: 'Error loading report',
      message: error instanceof Error ? error.message : String(error),
      requestId: req.id,
    });
  }
});

/**
 * GET /reports/:tradingDate/audio
 * Get audio metadata for a report.
 */
router.get('/:tradingDate/audio', validateTradingDate, async (req: Request, res: Response) => {
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
    const { tradingDate } = req.params;
    const clientId = (req.query.client_id as string) || DEFAULT_CLIENT_ID;

    const report = await getDailyReportByDate(tradingDate);

    if (!report) {
      return res.status(404).json({ error: 'Report not found' });
    }

    if (report.client_id && report.client_id !== clientId) {
      return res.status(404).json({ error: 'Report not found for this client' });
    }

    if (!report.audio_gcs_path) {
      return res.status(404).json({ error: 'No audio recorded for this report' });
    }

    return res.json({
      client_id: clientId,
      trading_date: tradingDate,
      audio_gcs_path: report.audio_gcs_path,
    });
  } catch (error) {
    logger.error('Error loading audio metadata:', {
      error,
      requestId: req.id,
    });
    return res.status(500).json({
      error: 'Error loading audio metadata',
      message: error instanceof Error ? error.message : String(error),
      requestId: req.id,
    });
  }
});

/**
 * POST /reports/generate/watchlist
 * Generate a watchlist-based report.
 */
router.post(
  '/generate/watchlist',
  reportGenerationLimiter,
  validateWatchlistReport,
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
      const { trading_date, client_id, watchlist } = req.body;

    const date = trading_date || new Date().toISOString().split('T')[0];

    logger.info(
      `API /reports/generate/watchlist: client=${client_id}, date=${date}, watchlist=${watchlist.join(',')}`
    );

    const report = await generateWatchlistDailyReport(date, client_id, watchlist);

    // Fetch raw_payload from Firestore if not in report
    let rawPayload = report.raw_payload || {};
    if (!rawPayload || Object.keys(rawPayload).length === 0) {
      try {
        const storedReport = await getDailyReportByDate(date);
        if (storedReport?.raw_payload) {
          rawPayload = storedReport.raw_payload as Record<string, any>;
        }
      } catch (error) {
        // If fetch fails, use empty object
        rawPayload = {};
      }
    }

    return res.json({
      client_id: report.client_id || client_id,
      trading_date: date,
      watchlist,
      summary_text: report.summary_text || '',
      key_insights: report.key_insights || [],
      audio_gcs_path: report.audio_gcs_path,
      raw_payload: rawPayload,
    });
    } catch (error) {
      logger.error('Watchlist report generation failed:', {
        error,
        requestId: req.id,
      });
      return res.status(500).json({
        error: 'Watchlist report generation failed',
        message: error instanceof Error ? error.message : String(error),
        requestId: req.id,
      });
    }
  }
);

export default router;


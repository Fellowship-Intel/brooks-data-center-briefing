/**
 * Report generation service - main orchestration.
 */

import { generateDailyReport } from './geminiService';
import { ttsService } from './ttsService';
import {
  createOrUpdateDailyReport,
  updateDailyReportAudioPath,
  getDailyReport,
} from '../repositories/reportRepository';
import { getBucket } from '../clients/gcpClients';
import { logger } from '../utils/logger';
import { retryWithBackoff } from '../utils/retryUtils';
import { env } from '../config/env';
import { DailyReport, InputData, DailyReportResponse } from '../types';

/**
 * Generate and store a daily report.
 */
export async function generateAndStoreDailyReport(
  tradingDate: string,
  clientId: string,
  marketData: Record<string, any>,
  newsItems: Record<string, any>,
  macroContext: Record<string, any>
): Promise<Record<string, any>> {
  try {
    // Extract tickers from market data
    const tickers = marketData.tickers || [];

    // Build input data
    const inputData: InputData = {
      trading_date: tradingDate,
      tickers_tracked: tickers,
      market_data_json: marketData.market_data || [],
      news_json: newsItems.news || [],
      macro_context: macroContext.context || '',
      constraints_or_notes: macroContext.notes || '',
    };

    // Generate report text using Gemini (with retry)
    logger.info(`Generating report for client=${clientId}, date=${tradingDate}`);
    const reportResponse: DailyReportResponse = await retryWithBackoff(
      () => generateDailyReport(inputData),
      { maxRetries: 3, initialDelay: 1.0 }
    );

    // Validate audio_report exists before attempting TTS
    const hasAudioReport = reportResponse.audio_report && reportResponse.audio_report.trim().length > 0;
    if (!hasAudioReport) {
      logger.warn(
        `No audio_report in response for client=${clientId}, date=${tradingDate}. Skipping TTS generation.`
      );
    }

    // Prepare report data for Firestore
    const reportData: Partial<DailyReport> = {
      client_id: clientId,
      trading_date: tradingDate,
      tickers,
      summary_text: reportResponse.report_markdown || '',
      key_insights: reportResponse.reports?.map(r => r.snapshot) || [],
      market_context: reportResponse.core_tickers_in_depth_markdown || '',
      raw_payload: reportResponse,
      email_status: 'pending',
    };

    // Store report in Firestore (with retry)
    await retryWithBackoff(
      () => createOrUpdateDailyReport(reportData as DailyReport & { trading_date: string }),
      { maxRetries: 3, initialDelay: 1.0 }
    );

    // Generate and store audio (with fallback, doesn't break pipeline)
    let audioGcsPath: string | undefined;
    let ttsProvider: string | undefined;

    // Only attempt TTS if audio_report is available
    if (hasAudioReport) {
      try {
        logger.info(`Attempting TTS generation for client=${clientId}, date=${tradingDate}`);
        const audioResult = await generateAndStoreAudioForReport(
          tradingDate,
          clientId,
          reportResponse.audio_report!,
          env.reportsBucketName
        );
        audioGcsPath = audioResult.gcsPath;
        ttsProvider = audioResult.provider;
      } catch (error) {
        // Log error but don't break the pipeline
        logger.error(
          `TTS generation failed for client=${clientId}, date=${tradingDate}: ${error}`,
          { error }
        );
      }
    }

    // Update report with audio path if available
    if (audioGcsPath) {
      await retryWithBackoff(
        () => updateDailyReportAudioPath(tradingDate, audioGcsPath!, ttsProvider),
        { maxRetries: 3, initialDelay: 1.0 }
      );
    }

    // Return consolidated result
    return {
      client_id: clientId,
      trading_date: tradingDate,
      summary_text: reportData.summary_text,
      key_insights: reportData.key_insights,
      market_context: reportData.market_context,
      audio_gcs_path: audioGcsPath,
      tts_provider: ttsProvider,
      raw_payload: reportData.raw_payload,
    };
  } catch (error) {
    logger.error(`Report generation failed for client=${clientId}, date=${tradingDate}:`, error);
    throw error;
  }
}

/**
 * Generate and store audio for a report.
 */
async function generateAndStoreAudioForReport(
  tradingDate: string,
  clientId: string,
  audioText: string,
  bucketName: string
): Promise<{ gcsPath: string; provider: string }> {
  if (!audioText || !audioText.trim()) {
    throw new Error('Audio text is empty');
  }

  // Generate audio using TTS service (with fallback)
  const { audioBytes, providerUsed } = await ttsService.synthesize(audioText);

  // Upload to Cloud Storage
  const gcsPath = `reports/${clientId}/${tradingDate}/report.wav`;
  const bucket = getBucket(bucketName);
  const blob = bucket.file(gcsPath);

  await retryWithBackoff(
    async () => {
      await blob.save(audioBytes, {
        contentType: 'audio/wav',
        metadata: {
          contentType: 'audio/wav',
        },
      });
    },
    { maxRetries: 3, initialDelay: 1.0 }
  );

  logger.info(`Audio uploaded to GCS: ${gcsPath}, provider: ${providerUsed}`);

  return {
    gcsPath: `gs://${bucketName}/${gcsPath}`,
    provider: providerUsed,
  };
}

/**
 * Generate watchlist-based daily report.
 */
export async function generateWatchlistDailyReport(
  tradingDate: string,
  clientId: string,
  watchlist: string[]
): Promise<Record<string, any>> {
  // This would fetch market data for the watchlist
  // For now, using dummy data structure
  const marketData = {
    tickers: watchlist,
    market_data: [],
  };

  const newsItems = {
    news: [],
  };

  const macroContext = {
    context: '',
    notes: '',
  };

  return generateAndStoreDailyReport(tradingDate, clientId, marketData, newsItems, macroContext);
}

/**
 * Get daily report from Firestore.
 */
export async function getDailyReportByDate(tradingDate: string): Promise<DailyReport | null> {
  return getDailyReport(tradingDate);
}


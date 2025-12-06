/**
 * Repository module for Firestore data access.
 * 
 * This module provides a clean interface for managing:
 * - Clients (collection: 'clients')
 * - Daily reports (collection: 'daily_reports')
 * - Ticker summaries (collection: 'ticker_summaries')
 */

import { getFirestoreClient } from '../clients/gcpClients';
import { DailyReport, Client, TickerSummary } from '../types';
import type { Query } from '@google-cloud/firestore';

/**
 * Fetch a client document from Firestore.
 */
export async function getClient(clientId: string): Promise<Client | null> {
  const db = getFirestoreClient();
  const docRef = db.collection('clients').doc(clientId);
  const doc = await docRef.get();
  
  if (!doc.exists) {
    return null;
  }
  
  return { id: doc.id, ...doc.data() } as Client & { id: string };
}

/**
 * Create or update a client document in Firestore.
 */
export async function upsertClient(
  clientId: string,
  email: string,
  name: string,
  timezone: string,
  preferences?: Record<string, any>
): Promise<void> {
  const db = getFirestoreClient();
  const docRef = db.collection('clients').doc(clientId);
  
  const data: any = {
    email,
    name,
    timezone,
  };
  
  if (preferences !== undefined) {
    data.preferences = preferences;
  }
  
  await docRef.set(data);
}

/**
 * Create or update a daily report document in Firestore.
 * 
 * Uses the 'trading_date' field as the document ID in the 'daily_reports' collection.
 * Automatically sets 'created_at' timestamp if not provided.
 */
export async function createOrUpdateDailyReport(report: Partial<DailyReport> & { trading_date: string }): Promise<void> {
  const db = getFirestoreClient();
  const tradingDate = report.trading_date;
  
  if (!tradingDate) {
    throw new Error("report must contain 'trading_date' field");
  }
  
  const docRef = db.collection('daily_reports').doc(tradingDate);
  
  // Prepare data with defaults
  const data: any = {
    client_id: report.client_id,
    trading_date: tradingDate,
    tickers: report.tickers || [],
    summary_text: report.summary_text || '',
    email_status: report.email_status || 'pending',
  };
  
  // Set created_at if not provided
  if (!report.created_at) {
    data.created_at = new Date();
  } else {
    data.created_at = report.created_at instanceof Date ? report.created_at : new Date(report.created_at);
  }
  
  // Add optional fields if present
  if (report.key_insights !== undefined) {
    data.key_insights = report.key_insights;
  }
  if (report.market_context !== undefined) {
    data.market_context = report.market_context;
  }
  if (report.audio_gcs_path !== undefined) {
    data.audio_gcs_path = report.audio_gcs_path;
  }
  if (report.raw_payload !== undefined) {
    data.raw_payload = report.raw_payload;
  }
  if (report.tts_provider !== undefined) {
    data.tts_provider = report.tts_provider;
  }
  
  await docRef.set(data);
}

/**
 * Fetch a daily report document from Firestore.
 */
export async function getDailyReport(tradingDate: string): Promise<DailyReport | null> {
  const db = getFirestoreClient();
  const docRef = db.collection('daily_reports').doc(tradingDate);
  const doc = await docRef.get();
  
  if (!doc.exists) {
    return null;
  }
  
  const data = doc.data();
  if (!data) {
    return null;
  }
  
  // Convert Firestore timestamps to Date objects
  if (data.created_at && data.created_at.toDate) {
    data.created_at = data.created_at.toDate();
  }
  
  return { id: doc.id, ...data } as DailyReport & { id: string };
}

/**
 * List daily reports from Firestore with optional filtering, pagination, and optimization.
 */
export async function listDailyReports(
  clientId?: string,
  limit: number = 50,
  orderBy: string = 'trading_date',
  descending: boolean = true,
  startAfter?: string
): Promise<{
  reports: (DailyReport & { id: string })[];
  has_more: boolean;
  last_date?: string;
  count: number;
}> {
  // Enforce max limit for performance
  const actualLimit = Math.min(limit, 100);
  
  const db = getFirestoreClient();
  let query: Query = db.collection('daily_reports');
  
  // Filter by client_id if provided
  if (clientId) {
    query = query.where('client_id', '==', clientId);
  }
  
  // Order by specified field
  const direction: 'desc' | 'asc' = descending ? 'desc' : 'asc';
  
  // Use trading_date as primary sort (it's the document ID, so very efficient)
  if (orderBy === 'trading_date') {
    query = query.orderBy(orderBy, direction);
    if (startAfter) {
      const startAfterDoc = await db.collection('daily_reports').doc(startAfter).get();
      if (startAfterDoc.exists) {
        query = query.startAfter(startAfterDoc);
      }
    }
  } else {
    query = query.orderBy(orderBy, direction);
  }
  
  // Limit results (fetch one extra to check if more exists)
  query = query.limit(actualLimit + 1);
  
  // Execute query
  const snapshot = await query.get();
  const docs = snapshot.docs;
  
  // Check if there are more results
  const hasMore = docs.length > actualLimit;
  const reports = (hasMore ? docs.slice(0, actualLimit) : docs).map((doc: any) => {
    const data = doc.data();
    // Convert Firestore timestamps to Date objects
    if (data.created_at && data.created_at.toDate) {
      data.created_at = data.created_at.toDate();
    }
    return { id: doc.id, ...data } as DailyReport & { id: string };
  });
  
  const lastDate = reports.length > 0 ? reports[reports.length - 1].trading_date : undefined;
  
  return {
    reports,
    has_more: hasMore,
    last_date: lastDate,
    count: reports.length,
  };
}

/**
 * Update the audio GCS path for a daily report.
 */
export async function updateDailyReportAudioPath(
  tradingDate: string,
  audioGcsPath: string,
  ttsProvider?: string
): Promise<void> {
  const db = getFirestoreClient();
  const docRef = db.collection('daily_reports').doc(tradingDate);
  
  const updateData: any = {
    audio_gcs_path: audioGcsPath,
  };
  
  if (ttsProvider) {
    updateData.tts_provider = ttsProvider;
  }
  
  await docRef.update(updateData);
}

/**
 * Get or create a ticker summary document.
 */
export async function getOrCreateTickerSummary(ticker: string): Promise<TickerSummary & { id: string }> {
  const db = getFirestoreClient();
  const docRef = db.collection('ticker_summaries').doc(ticker.toUpperCase());
  const doc = await docRef.get();
  
  if (doc.exists) {
    const data = doc.data();
    if (data?.last_updated && data.last_updated.toDate) {
      data.last_updated = data.last_updated.toDate();
    }
    return { id: doc.id, ...data } as TickerSummary & { id: string };
  }
  
  // Create new summary
  const newData: TickerSummary = {
    ticker: ticker.toUpperCase(),
    latest_snapshot: {},
  };
  
  await docRef.set(newData);
  return { id: doc.id, ...newData };
}

/**
 * Update a ticker summary document.
 */
export async function updateTickerSummary(
  ticker: string,
  snapshot: Record<string, any>,
  notes?: string
): Promise<void> {
  const db = getFirestoreClient();
  const docRef = db.collection('ticker_summaries').doc(ticker.toUpperCase());
  
  const updateData: any = {
    latest_snapshot: snapshot,
    last_updated: new Date(),
  };
  
  if (notes !== undefined) {
    updateData.notes = notes;
  }
  
  await docRef.set(updateData, { merge: true });
}


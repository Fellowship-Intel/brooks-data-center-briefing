/**
 * GCP client helpers for the 'mikebrooks' project.
 * 
 * This module centralizes Google Cloud Platform client creation and authentication.
 * It uses Application Default Credentials (ADC) for authentication, which works
 * both locally (via GOOGLE_APPLICATION_CREDENTIALS) and on Cloud Run (via bound service account).
 */

import { Firestore } from '@google-cloud/firestore';
import { Storage, Bucket } from '@google-cloud/storage';
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';
import { GoogleAuth } from 'google-auth-library';
import * as path from 'path';
import * as fs from 'fs';
import { env } from '../config/env';

// Singleton instances
let firestoreClient: Firestore | null = null;
let storageClient: Storage | null = null;
let secretManagerClient: SecretManagerServiceClient | null = null;

/**
 * Check if GCP credentials are available and provide helpful error messages.
 */
function checkCredentials(): void {
  const credsPath = process.env.GOOGLE_APPLICATION_CREDENTIALS;
  
  // Check if we're in a GCP environment (Cloud Run, etc.)
  // In GCP environments, metadata server provides credentials
  try {
    const auth = new GoogleAuth();
    auth.getClient();
    return; // Credentials found
  } catch (error) {
    // Continue to check local credentials
  }
  
  // Check for local credentials file
  if (credsPath) {
    if (fs.existsSync(credsPath)) {
      return; // Credentials file exists
    } else {
      throw new Error(
        `GOOGLE_APPLICATION_CREDENTIALS is set to '${credsPath}' but the file does not exist.\n` +
        `Please ensure the service account JSON file exists at this path.\n` +
        `Or run: .\\setup-gcp-env.ps1 (on Windows) to set up credentials automatically.`
      );
    }
  } else {
    // Try to find credentials in common location
    const defaultCredsPath = path.join(process.cwd(), '.secrets', 'app-backend-sa.json');
    if (fs.existsSync(defaultCredsPath)) {
      process.env.GOOGLE_APPLICATION_CREDENTIALS = defaultCredsPath;
      return;
    }
    
    // No credentials found
    throw new Error(
      'GCP credentials not found. To set up Application Default Credentials:\n\n' +
      'Option 1 (Recommended - Windows PowerShell):\n' +
      '  .\\setup-gcp-env.ps1\n\n' +
      'Option 2 (Manual - Windows PowerShell):\n' +
      `  $env:GOOGLE_APPLICATION_CREDENTIALS="$PWD\\.secrets\\app-backend-sa.json"\n\n` +
      'Option 3 (Manual - Linux/Mac):\n' +
      `  export GOOGLE_APPLICATION_CREDENTIALS="$PWD/.secrets/app-backend-sa.json"\n\n` +
      `Make sure you have a service account JSON file at:\n` +
      `  ${defaultCredsPath}\n\n` +
      'For more information, see: https://cloud.google.com/docs/authentication/external/set-up-adc'
    );
  }
}

/**
 * Get the active GCP project ID.
 * 
 * Priority:
 * 1. GCP_PROJECT_ID environment variable
 * 2. Default project id constant set to "mikebrooks"
 */
export function getProjectId(): string {
  const projectId = env.projectId;
  if (!projectId) {
    throw new Error(
      'GCP_PROJECT_ID is not set and no default project ID is defined.'
    );
  }
  return projectId;
}

/**
 * Returns an authenticated Firestore client using Application Default Credentials.
 * 
 * Requirements:
 * - GOOGLE_APPLICATION_CREDENTIALS points to a valid service account key (local)
 *   OR the code is running on GCP (Cloud Run, etc.) with a bound service account.
 * - Service account has roles/datastore.user on the project.
 * 
 * Returns:
 *   An authenticated Firestore client instance.
 */
export function getFirestoreClient(): Firestore {
  if (firestoreClient) {
    return firestoreClient;
  }
  
  checkCredentials();
  const projectId = getProjectId();
  firestoreClient = new Firestore({
    projectId,
  });
  return firestoreClient;
}

/**
 * Returns an authenticated Cloud Storage client.
 * 
 * Requirements:
 * - Same auth expectations as Firestore.
 * - Service account should have at least roles/storage.objectAdmin.
 * 
 * Returns:
 *   An authenticated Storage client instance.
 */
export function getStorageClient(): Storage {
  if (storageClient) {
    return storageClient;
  }
  
  checkCredentials();
  const projectId = getProjectId();
  storageClient = new Storage({
    projectId,
  });
  return storageClient;
}

/**
 * Returns a Bucket object for the given bucket_name.
 * 
 * Uses getStorageClient() internally.
 */
export function getBucket(bucketName: string): Bucket {
  const client = getStorageClient();
  return client.bucket(bucketName);
}

/**
 * Returns a Secret Manager client.
 * 
 * Requirements:
 * - Service account has roles/secretmanager.secretAccessor.
 * 
 * Returns:
 *   An authenticated SecretManagerServiceClient instance.
 */
export function getSecretManagerClient(): SecretManagerServiceClient {
  if (secretManagerClient) {
    return secretManagerClient;
  }
  
  checkCredentials();
  secretManagerClient = new SecretManagerServiceClient();
  return secretManagerClient;
}

/**
 * Fetches the value of a secret from Secret Manager as a UTF-8 string.
 * 
 * Falls back to environment variable if Secret Manager is unavailable.
 * 
 * @param secretId Secret name only (e.g. "GEMINI_API_KEY"), not the full resource path.
 * @param version Secret version to access (default: "latest").
 * @returns The secret payload decoded as UTF-8 text.
 */
export async function accessSecretValue(secretId: string, version: string = 'latest'): Promise<string> {
  // Try Secret Manager first
  try {
    const projectId = getProjectId();
    const client = getSecretManagerClient();
    const name = `projects/${projectId}/secrets/${secretId}/versions/${version}`;
    const [response] = await client.accessSecretVersion({ name });
    if (response.payload?.data) {
      return response.payload.data.toString();
    }
    throw new Error(`Secret ${secretId} has no data`);
  } catch (error) {
    // Fall back to environment variable
    const envValue = process.env[secretId];
    if (envValue) {
      return envValue;
    }
    throw new Error(
      `Secret ${secretId} not found in Secret Manager or environment variables. ` +
      `Error: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

/**
 * Retrieve the Eleven Labs API key from Secret Manager.
 * 
 * Falls back to ELEVEN_LABS_API_KEY environment variable if Secret Manager is unavailable.
 */
export async function accessElevenLabsApiKey(version: string = 'latest'): Promise<string> {
  try {
    return await accessSecretValue('ELEVEN_LABS_API_KEY', version);
  } catch (error) {
    const apiKey = process.env.ELEVEN_LABS_API_KEY;
    if (!apiKey) {
      throw new Error(
        'Eleven Labs API key not found. Set ELEVEN_LABS_API_KEY in environment, ' +
        'or ensure ELEVEN_LABS_API_KEY exists in Secret Manager.'
      );
    }
    return apiKey;
  }
}


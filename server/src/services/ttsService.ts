/**
 * TTS service abstraction layer supporting multiple providers.
 */

import { ElevenLabsClient } from 'elevenlabs';
import { GoogleGenAI } from '@google/genai';
import { accessElevenLabsApiKey } from '../clients/gcpClients';
import { logger } from '../utils/logger';
import { env } from '../config/env';

export class TTSGenerationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TTSGenerationError';
  }
}

/**
 * Eleven Labs TTS implementation.
 */
class ElevenLabsTTS {
  private client: ElevenLabsClient | null = null;
  private voiceId: string;
  private modelId: string = 'eleven_multilingual_v2';
  private providedApiKey?: string;
  private initializationPromise: Promise<void> | null = null;

  constructor(apiKey?: string, voiceId?: string) {
    this.voiceId = voiceId || process.env.ELEVEN_LABS_VOICE_ID || this.getDefaultVoice();
    this.modelId = process.env.ELEVEN_LABS_MODEL_ID || 'eleven_multilingual_v2';
    this.providedApiKey = apiKey;
  }

  /**
   * Initialize the ElevenLabs client with API key (lazy initialization).
   * This ensures async operations complete before client is used.
   */
  private async initializeClient(): Promise<void> {
    // If already initialized, return
    if (this.client) {
      return;
    }

    // If initialization is in progress, wait for it
    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    // Start initialization
    this.initializationPromise = (async () => {
      try {
        let apiKey: string;

        if (this.providedApiKey) {
          apiKey = this.providedApiKey;
        } else {
          // Try Secret Manager first, fall back to environment variable
          try {
            apiKey = await accessElevenLabsApiKey();
          } catch (error) {
            const envKey = env.elevenLabsApiKey;
            if (!envKey) {
              throw new Error(
                'Eleven Labs API key not found. Set ELEVEN_LABS_API_KEY in environment, ' +
                'or ensure ELEVEN_LABS_API_KEY exists in Secret Manager.'
              );
            }
            apiKey = envKey;
          }
        }

        this.client = new ElevenLabsClient({ apiKey });
      } catch (error) {
        // Clear promise so retry can be attempted
        this.initializationPromise = null;
        throw error;
      }
    })();

    return this.initializationPromise;
  }

  private getDefaultVoice(): string {
    // Default to Rachel's voice ID (verify this is correct)
    return '21m00Tcm4TlvDq8ikWAM';
  }

  async synthesize(text: string, outputPath?: string): Promise<Buffer> {
    if (!text || !text.trim()) {
      throw new Error('Text must not be empty');
    }

    // Ensure client is initialized before use
    await this.initializeClient();

    if (!this.client) {
      throw new Error('Failed to initialize ElevenLabs client');
    }

    try {
      logger.debug(
        `Generating speech with Eleven Labs: voice_id=${this.voiceId}, text_length=${text.length}`
      );

      const audio = await this.client.textToSpeech.convert(this.voiceId, {
        text,
        model_id: this.modelId,
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
          style: 0.0,
          use_speaker_boost: true,
        },
      });

      // Convert stream to buffer
      const chunks: Buffer[] = [];
      for await (const chunk of audio) {
        chunks.push(Buffer.from(chunk));
      }
      const audioBuffer = Buffer.concat(chunks);

      // Write to file if path provided
      if (outputPath) {
        const fs = await import('fs');
        fs.writeFileSync(outputPath, audioBuffer);
      }

      return audioBuffer;
    } catch (error) {
      logger.error('Eleven Labs TTS synthesis failed:', error);
      throw new TTSGenerationError(
        `Eleven Labs TTS failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }
}

/**
 * Gemini TTS implementation.
 * 
 * NOTE: This implementation is currently incomplete. The Gemini TTS API from @google/genai
 * is not yet fully implemented. When this provider is selected, it will throw an error
 * and the TTS service will automatically fall back to the primary provider (Eleven Labs).
 * 
 * To implement Gemini TTS:
 * 1. Check the latest @google/genai documentation for TTS API
 * 2. Update this method with the correct API calls
 * 3. Remove this placeholder error
 */
class GeminiTTS {
  constructor(_apiKey?: string) {
    const key = _apiKey || env.geminiApiKey;
    if (!key) {
      throw new Error(
        'API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY in environment, ' +
        'or ensure GEMINI_API_KEY exists in Secret Manager.'
      );
    }
    // Client initialization for future use when Gemini TTS is implemented
    void new GoogleGenAI({ apiKey: key });
  }

  /**
   * Synthesize speech using Gemini TTS.
   * Note: This is a placeholder implementation. Gemini TTS API may not be available
   * in the current @google/genai package. This will automatically fall back to
   * Eleven Labs if Gemini TTS is not available.
   */
  async synthesize(_text: string, _outputPath?: string): Promise<Buffer> {
    // Placeholder - Gemini TTS not fully implemented
    // This will cause fallback to Eleven Labs
    throw new Error('Gemini TTS not implemented - falling back to Eleven Labs');
  }
}

/**
 * Unified TTS service with automatic fallback.
 */
export class TTSService {
  private primaryProvider: 'eleven_labs' | 'gemini';
  private fallbackProvider: 'eleven_labs' | 'gemini';
  private elevenLabs?: ElevenLabsTTS;
  private geminiTTS?: GeminiTTS;

  constructor(
    primaryProvider: 'eleven_labs' | 'gemini' = 'eleven_labs',
    fallbackProvider: 'eleven_labs' | 'gemini' = 'gemini'
  ) {
    this.primaryProvider = primaryProvider;
    this.fallbackProvider = fallbackProvider;
    logger.info(`TTS Service initialized: primary=${primaryProvider}, fallback=${fallbackProvider}`);
  }

  private getElevenLabs(): ElevenLabsTTS {
    if (!this.elevenLabs) {
      this.elevenLabs = new ElevenLabsTTS();
    }
    return this.elevenLabs;
  }

  private getGeminiTTS(): GeminiTTS {
    if (!this.geminiTTS) {
      this.geminiTTS = new GeminiTTS();
    }
    return this.geminiTTS;
  }

  /**
   * Synthesize speech from text with automatic fallback.
   */
  async synthesize(
    text: string,
    outputPath?: string,
    provider?: 'eleven_labs' | 'gemini'
  ): Promise<{ audioBytes: Buffer; providerUsed: string }> {
    // Determine which provider to try first
    const providersToTry: ('eleven_labs' | 'gemini')[] = provider
      ? [provider, provider === this.primaryProvider ? this.fallbackProvider : this.primaryProvider]
      : [this.primaryProvider, this.fallbackProvider];

    let lastError: Error | null = null;

    for (const providerName of providersToTry) {
      try {
        let audioBytes: Buffer;
        
        if (providerName === 'eleven_labs') {
          audioBytes = await this.getElevenLabs().synthesize(text, outputPath);
        } else {
          audioBytes = await this.getGeminiTTS().synthesize(text, outputPath);
        }

        logger.info(`TTS synthesis successful using ${providerName}`);
        return { audioBytes, providerUsed: providerName };
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        logger.warn(`TTS provider ${providerName} failed: ${lastError.message}`);
        
        // Try next provider
        continue;
      }
    }

    // All providers failed
    throw new TTSGenerationError(
      `All TTS providers failed. Last error: ${lastError?.message || 'Unknown error'}`
    );
  }
}

// Export singleton instance
export const ttsService = new TTSService();


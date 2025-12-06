import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, Volume2, AlertCircle } from 'lucide-react';
import { logger } from '../utils/logger';

interface AudioPlayerProps {
  text: string;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ text }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // Use a ref to track if we've mounted to prevent memory leaks during async operations
  const mountedRef = useRef(true);
  
  // CRITICAL FIX: Store utterances in a ref to prevent garbage collection
  // which causes the 'error' event to fire unexpectedly in Chrome/Edge.
  const utterancesRef = useRef<SpeechSynthesisUtterance[]>([]);

  useEffect(() => {
    mountedRef.current = true;
    const loadVoices = () => {
      const vs = window.speechSynthesis.getVoices();
      if (mountedRef.current) {
        setVoices(vs);
      }
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      mountedRef.current = false;
      window.speechSynthesis.cancel();
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  // Reset state when text changes
  useEffect(() => {
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
    setError(null);
    utterancesRef.current = [];
  }, [text]);

  const handlePlay = () => {
    setError(null);

    if (!text) {
        setError("No audio report text available.");
        return;
    }

    // Resume if paused
    if (isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
      setIsPlaying(true);
      return;
    }

    if (isPlaying) {
        return;
    }

    // Ensure we start from a clean slate
    window.speechSynthesis.cancel();
    utterancesRef.current = [];

    // CLEANUP: Strip markdown characters that might have slipped in
    const cleanText = text.replace(/[*#_`]/g, '');

    // CHUNKING STRATEGY:
    // Split by punctuation, keeping the punctuation, or end of line.
    // This regex matches sequences of characters ending in punctuation or end of string.
    const chunks = cleanText.match(/[^.!?]+(?:[.!?]+["']?|$)(\s+|$)/g) || [cleanText];
    
    if (chunks.length === 0) {
        setError("Could not parse audio text.");
        return;
    }

    setIsPlaying(true);

    // Try to select a high-quality voice
    const preferredVoice = voices.find(v => v.name.includes('Google US English')) || 
                           voices.find(v => v.lang === 'en-US' && v.name.includes('Male')) ||
                           voices.find(v => v.lang === 'en-US') ||
                           voices[0];

    // Queue all chunks
    chunks.forEach((chunk, index) => {
        const trimmedChunk = chunk.trim();
        if (!trimmedChunk) return;

        const utterance = new SpeechSynthesisUtterance(trimmedChunk);
        
        if (preferredVoice) utterance.voice = preferredVoice;
        
        // Settings for natural pacing
        utterance.rate = 0.95; 
        utterance.pitch = 1.0;

        // Error handling per chunk
        utterance.onerror = (e) => {
            // Ignore expected interruptions (like clicking stop)
            if (e.error === 'interrupted' || e.error === 'canceled') {
                return;
            }
            
            logger.error("TTS Chunk Error:", e.error, e);
            
            if (index === chunks.length - 1 && mountedRef.current) {
                setIsPlaying(false);
            }
        };

        // When the LAST chunk finishes, reset the playing state
        if (index === chunks.length - 1) {
            utterance.onend = () => {
                if (mountedRef.current) {
                    setIsPlaying(false);
                    setIsPaused(false);
                }
            };
        }

        // Store reference to prevent Garbage Collection
        utterancesRef.current.push(utterance);

        window.speechSynthesis.speak(utterance);
    });
  };

  const handlePause = () => {
    window.speechSynthesis.pause();
    setIsPaused(true);
    setIsPlaying(false);
  };

  const handleStop = () => {
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
    utterancesRef.current = [];
  };

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 flex items-center justify-between shadow-lg min-w-[300px]">
        <div className="flex items-center gap-4">
            <div className={`p-2 rounded-full transition-all duration-500 ${isPlaying ? 'bg-emerald-500/20 text-emerald-400 animate-pulse' : 'bg-slate-800 text-slate-400'}`}>
                <Volume2 size={24} />
            </div>
            <div className="flex-1">
                <h3 className="text-sm font-semibold text-emerald-100">Audio Briefing</h3>
                {error ? (
                    <p className="text-xs text-red-400 flex items-center gap-1 mt-1">
                        <AlertCircle size={10} /> {error}
                    </p>
                ) : (
                    <p className="text-xs text-slate-400 mt-0.5">
                        {isPlaying ? 'Playing Report...' : isPaused ? 'Paused' : 'Ready to Play'}
                    </p>
                )}
            </div>
        </div>
        
        <div className="flex items-center gap-2">
            {!isPlaying && !isPaused ? (
                <button 
                    onClick={handlePlay} 
                    className="p-2 hover:bg-slate-800 rounded-full text-emerald-400 transition-colors"
                    aria-label="Play audio briefing"
                    title="Play"
                >
                    <Play size={20} fill="currentColor" aria-hidden="true" />
                </button>
            ) : isPaused ? (
                 <button 
                    onClick={handlePlay} 
                    className="p-2 hover:bg-slate-800 rounded-full text-emerald-400 transition-colors"
                    aria-label="Resume audio briefing"
                    title="Resume"
                >
                    <Play size={20} fill="currentColor" aria-hidden="true" />
                </button>
            ) : (
                <button 
                    onClick={handlePause} 
                    className="p-2 hover:bg-slate-800 rounded-full text-amber-400 transition-colors"
                    aria-label="Pause audio briefing"
                    title="Pause"
                >
                    <Pause size={20} fill="currentColor" aria-hidden="true" />
                </button>
            )}
            
            <button 
                onClick={handleStop} 
                className="p-2 hover:bg-slate-800 rounded-full text-red-400 transition-colors"
                aria-label="Stop audio briefing"
                title="Stop"
            >
                <Square size={16} fill="currentColor" aria-hidden="true" />
            </button>
        </div>
    </div>
  );
};

export default AudioPlayer;
"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * German pronunciation. A recorded / provider-made file (`audioUrl`) is played
 * when the word has one; otherwise the browser's own speech synthesis with a
 * German voice. Voices differ per browser and device (quality is not the same
 * everywhere) and some browsers have no German voice at all — then
 * `error === "no-voice"` and the UI says so instead of failing silently.
 */
export type SpeechError = "unsupported" | "no-voice" | "failed";

function germanVoice(): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices();
  return (
    voices.find((v) => v.lang === "de-DE" && v.localService) ??
    voices.find((v) => v.lang === "de-DE") ??
    voices.find((v) => v.lang.toLowerCase().startsWith("de")) ??
    null
  );
}

export function useSpeech() {
  const [speakingKey, setSpeakingKey] = useState<string | null>(null);
  const [error, setError] = useState<SpeechError | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const supported = typeof window !== "undefined" && "speechSynthesis" in window;

  useEffect(() => {
    if (!supported) return;
    // Chrome loads voices asynchronously; asking once makes them available later
    window.speechSynthesis.getVoices();
    return () => {
      window.speechSynthesis.cancel();
      audioRef.current?.pause();
    };
  }, [supported]);

  const stop = useCallback(() => {
    if (supported) window.speechSynthesis.cancel();
    audioRef.current?.pause();
    setSpeakingKey(null);
  }, [supported]);

  const speak = useCallback(
    (text: string, key: string, audioUrl?: string | null) => {
      setError(null);
      if (speakingKey === key) return stop();
      stop();
      if (audioUrl) {
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        audio.onended = () => setSpeakingKey(null);
        audio.onerror = () => {
          setSpeakingKey(null);
          setError("failed");
        };
        setSpeakingKey(key);
        audio.play().catch(() => {
          setSpeakingKey(null);
          setError("failed");
        });
        return;
      }
      if (!supported) return setError("unsupported");
      const voice = germanVoice();
      if (!voice) return setError("no-voice");
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "de-DE";
      utterance.voice = voice;
      utterance.rate = 0.9;
      utterance.onend = () => setSpeakingKey(null);
      utterance.onerror = (e) => {
        setSpeakingKey(null);
        if (e.error !== "canceled" && e.error !== "interrupted") setError("failed");
      };
      setSpeakingKey(key);
      window.speechSynthesis.speak(utterance);
    },
    [speakingKey, stop, supported],
  );

  return { speak, stop, speakingKey, error, supported };
}

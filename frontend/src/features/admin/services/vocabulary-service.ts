import { API_URL } from "@/src/constants/api";
import { getToken } from "@/src/lib/token";
import { api } from "@/src/services/api";

import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  AudioQueueStatus,
  BulkVocabularySaveItem,
  BulkVocabularySaveResult,
  BulkVocabularyStreamEvent,
  Vocabulary,
  VocabularyCreate,
  VocabularyUpdate,
} from "../types/content.types";

export const vocabularyApi = createCrudApi<Vocabulary, VocabularyCreate, VocabularyUpdate>(
  ADMIN_ENDPOINTS.vocabularies,
);

export interface BulkAnalyzePayload {
  lesson_id: string;
  words: string[];
  auto_complete: boolean;
}

/** POST /vocabularies/bulk/analyze streams newline-delimited JSON — one
 * line per progress tick, then one per preview row, then {"type":"done"}.
 * axios doesn't expose a ReadableStream body reader in the browser the
 * way native fetch does, so this one call bypasses the shared `api`
 * instance and attaches the same Bearer token by hand instead. */
export async function* analyzeVocabularyBulk(
  payload: BulkAnalyzePayload,
  signal?: AbortSignal,
): AsyncGenerator<BulkVocabularyStreamEvent> {
  const token = getToken();

  const response = await fetch(`${API_URL}/api/v1/vocabularies/bulk/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => "");
    throw new Error(text || `Analyze failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let newlineIndex = buffer.indexOf("\n");
    while (newlineIndex >= 0) {
      const line = buffer.slice(0, newlineIndex).trim();
      buffer = buffer.slice(newlineIndex + 1);
      if (line) yield JSON.parse(line) as BulkVocabularyStreamEvent;
      newlineIndex = buffer.indexOf("\n");
    }
  }

  const remainder = buffer.trim();
  if (remainder) yield JSON.parse(remainder) as BulkVocabularyStreamEvent;
}

export async function saveVocabularyBulk(
  lessonId: string,
  items: BulkVocabularySaveItem[],
): Promise<BulkVocabularySaveResult> {
  const response = await api.post<BulkVocabularySaveResult>(`${ADMIN_ENDPOINTS.vocabularies}bulk/save`, {
    lesson_id: lessonId,
    items,
  });
  return response.data;
}

// ==========================
// Personal voice recording — no AI-generated audio. The admin's own
// microphone recording is processed (cleaned + repeated 3x) server-side
// via ffmpeg, then, only once the admin confirms, saved permanently.
// ==========================

/** POST /vocabularies/audio/process — uploads the raw MediaRecorder
 * blob, gets back the final processed WAV (word, pause, word, pause,
 * word) as a Blob. Nothing is persisted yet; this is purely the preview
 * step. Bypasses axios (raw binary body, not JSON) the same way the
 * NDJSON streaming calls do. */
export async function processVocabularyRecording(rawBlob: Blob): Promise<Blob> {
  const token = getToken();
  const form = new FormData();
  form.append("file", rawBlob, "recording");

  const response = await fetch(`${API_URL}/api/v1/vocabularies/audio/process`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: form,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    let message = text;
    try {
      message = JSON.parse(text).detail ?? text;
    } catch {
      // plain-text error body — use as-is
    }
    throw new Error(message || `Verarbeitung fehlgeschlagen (${response.status})`);
  }

  return response.blob();
}

/** POST /vocabularies/{id}/audio/save — persists the already-processed
 * WAV (the same blob processVocabularyRecording() returned) against one
 * existing Vocabulary row. Only called once the admin presses Speichern. */
export async function saveVocabularyRecording(
  vocabularyId: string,
  processedWav: Blob,
): Promise<{ audio_url: string }> {
  const form = new FormData();
  form.append("file", processedWav, "audio.wav");

  const response = await api.post<{ audio_url: string }>(
    `${ADMIN_ENDPOINTS.vocabularies}${vocabularyId}/audio/save`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

// ==========================
// Missing-audio queue ("Audio nacheinander aufnehmen")
// ==========================

export async function getAudioQueueStatus(lessonId: string): Promise<AudioQueueStatus> {
  const response = await api.get<AudioQueueStatus>(
    `${ADMIN_ENDPOINTS.vocabularies}lesson/${lessonId}/audio-queue`,
  );
  return response.data;
}

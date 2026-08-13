import { API_URL } from "@/src/constants/api";
import { getToken } from "@/src/lib/token";
import { api } from "@/src/services/api";

import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  AudioQueueStatus,
  AudioQueueStreamEvent,
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
  generate_audio: boolean;
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

export async function regenerateVocabularyAudio(vocabularyId: string): Promise<{ audio_url: string }> {
  const response = await api.post<{ audio_url: string }>(
    `${ADMIN_ENDPOINTS.vocabularies}${vocabularyId}/audio/regenerate`,
  );
  return response.data;
}

// ==========================
// Missing-audio queue ("Fehlende Audios generieren")
// ==========================

export async function getAudioQueueStatus(lessonId: string): Promise<AudioQueueStatus> {
  const response = await api.get<AudioQueueStatus>(
    `${ADMIN_ENDPOINTS.vocabularies}lesson/${lessonId}/audio-queue`,
  );
  return response.data;
}

/** POST /vocabularies/lesson/{id}/audio-queue/generate streams NDJSON,
 * same shape/reasoning as analyzeVocabularyBulk above — reused pattern,
 * not shared code, since the event types genuinely differ. */
export async function* generateMissingAudio(
  lessonId: string,
  signal?: AbortSignal,
): AsyncGenerator<AudioQueueStreamEvent> {
  const token = getToken();

  const response = await fetch(`${API_URL}/api/v1/vocabularies/lesson/${lessonId}/audio-queue/generate`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    signal,
  });

  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => "");
    throw new Error(text || `Audio queue failed (${response.status})`);
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
      if (line) yield JSON.parse(line) as AudioQueueStreamEvent;
      newlineIndex = buffer.indexOf("\n");
    }
  }

  const remainder = buffer.trim();
  if (remainder) yield JSON.parse(remainder) as AudioQueueStreamEvent;
}

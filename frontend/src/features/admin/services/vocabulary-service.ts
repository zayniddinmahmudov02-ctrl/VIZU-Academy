import { API_URL } from "@/src/constants/api";
import { getToken } from "@/src/lib/token";
import { api } from "@/src/services/api";

import { createCrudApi } from "../lib/crud-api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  BulkDeleteVocabularyResult,
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

export async function bulkDeleteVocabulary(
  lessonId: string,
  vocabularyIds: string[],
): Promise<BulkDeleteVocabularyResult> {
  const response = await api.post<BulkDeleteVocabularyResult>(`${ADMIN_ENDPOINTS.vocabularies}bulk/delete`, {
    lesson_id: lessonId,
    vocabulary_ids: vocabularyIds,
  });
  return response.data;
}

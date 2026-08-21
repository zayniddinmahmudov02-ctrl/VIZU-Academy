import { API_URL } from "@/src/constants/api";
import { getToken } from "@/src/lib/token";
import { api, refreshAccessToken } from "@/src/services/api";

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

/** A 401 here means the admin's own session expired — never to be
 * confused with (and shown alongside the same UI as) a Gemini failure.
 * See bulk-vocabulary-dialog.tsx, which checks `err instanceof
 * SessionExpiredError` to render a distinct message. */
export class SessionExpiredError extends Error {
  constructor() {
    super("Deine Sitzung ist abgelaufen. Bitte lade die Seite neu und melde dich erneut an.");
    this.name = "SessionExpiredError";
  }
}

async function fetchBulkAnalyze(payload: BulkAnalyzePayload, token: string | null, signal?: AbortSignal) {
  return fetch(`${API_URL}/api/v1/vocabularies/bulk/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });
}

/** POST /vocabularies/bulk/analyze streams newline-delimited JSON — one
 * line per progress tick, then one per preview row, then {"type":"done"}.
 * axios doesn't expose a ReadableStream body reader in the browser the
 * way native fetch does, so this one call bypasses the shared `api`
 * instance and attaches the Bearer token by hand instead — which means
 * it must also handle a 401 itself, exactly like the shared instance's
 * response interceptor does (see services/api.ts): try one silent
 * token refresh, retry once, and only then give up. Without this, an
 * access token that expires mid-admin-session fails this one call
 * forever until the page is reloaded, while every other admin request
 * quietly recovers. */
export async function* analyzeVocabularyBulk(
  payload: BulkAnalyzePayload,
  signal?: AbortSignal,
): AsyncGenerator<BulkVocabularyStreamEvent> {
  let response = await fetchBulkAnalyze(payload, getToken(), signal);

  if (response.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      response = await fetchBulkAnalyze(payload, newToken, signal);
    }
  }

  if (response.status === 401) {
    throw new SessionExpiredError();
  }

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

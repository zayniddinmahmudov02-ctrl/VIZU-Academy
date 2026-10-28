import { api } from "@/services/api";

const BASE = "/api/v1/dictionary";

export const CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1"] as const;
export type CefrLevel = (typeof CEFR_LEVELS)[number];
export type ContentStatus = "source" | "sourced" | "needs_review" | "reviewed" | "none";
export type WordStatus = "known" | "unknown";

export interface WordBrief {
  id: string;
  german: string;
  lemma: string;
  article: "der" | "die" | "das" | null;
  part_of_speech: string | null;
  cefr_level: CefrLevel;
  levels: CefrLevel[];
  translation: string;
}

export interface PresentForm {
  person: string;
  form: string;
}

/** Grammar as stored per part of speech (backend services/dictionary, from Wiktionary). */
export interface WordGrammar {
  // Nomen
  article?: string | null;
  gender?: string | null;
  singular?: string | null;
  plural?: string | null;
  plural_variants?: string[];
  plural_note?: string | null;
  number?: "Plural" | "Pluraletantum";
  compound_head?: string | null;
  // Verb
  infinitive?: string;
  reflexive?: boolean;
  conjugation_type?: string | null;
  separable?: boolean | null;
  praeteritum?: string | null;
  partizip_ii?: string | null;
  auxiliary?: string[] | null;
  perfekt?: string | null;
  praesens?: PresentForm[] | null;
  // Adjektiv
  positiv?: string;
  komparativ?: string | null;
  superlativ?: string | null;
  partizip_ii_von?: string;
  note?: string | null;
  // Präposition / Konjunktion
  cases?: string[] | null;
  wechselpraeposition?: boolean | null;
  conjunction?: { type: string; word_order: string };
}

export interface WordCard extends WordBrief {
  reflexive: boolean;
  translations_extra: string[];
  definition_de: string | null;
  grammar: WordGrammar | null;
  grammar_source: string;
  ipa: string | null;
  example_de: string | null;
  example_uz: string | null;
  audio_url: string | null;
  status: { translation: ContentStatus; grammar: ContentStatus; example: ContentStatus };
  attribution: { name: string; license: string; url: string } | null;
  me: { saved: boolean; status: WordStatus | null; seen_count: number };
}

export interface Paged<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface DictionaryMeta {
  total: number;
  levels: Record<CefrLevel, number>;
  parts_of_speech: string[];
  attribution: { name: string; license: string; url: string };
}

export interface RandomFive {
  level: CefrLevel | "ALL";
  pool_size: number;
  unseen_before: number;
  complete: boolean;
  items: WordCard[];
}

export interface MyWordItem extends WordBrief {
  me: { saved: boolean; status: WordStatus | null; seen_count: number };
}

export interface MyWords extends Paged<MyWordItem> {
  summary: { saved: number; known: number; unknown: number; seen: number };
}

export interface SearchFilters {
  q: string;
  level?: CefrLevel | "";
  pos?: string;
  page?: number;
}

const items = <T,>(data: { items?: T[] } | undefined): T[] => (Array.isArray(data?.items) ? data!.items! : []);

export const getDictionaryMeta = async () => (await api.get<DictionaryMeta>(`${BASE}/meta`)).data;

export const searchWords = async ({ q, level, pos, page = 1 }: SearchFilters, signal?: AbortSignal) => {
  const params = Object.fromEntries(Object.entries({ q, level, pos, page, page_size: 20 }).filter(([, v]) => v !== undefined && v !== ""));
  const data = (await api.get<Paged<WordBrief>>(`${BASE}/search`, { params, signal })).data;
  return { ...data, items: items(data) };
};

export const getWord = async (id: string) => (await api.get<WordCard>(`${BASE}/entries/${encodeURIComponent(id)}`)).data;

export const drawRandomFive = async (level: CefrLevel | "ALL") => {
  const data = (await api.post<RandomFive>(`${BASE}/random`, { level })).data;
  return { ...data, items: items(data) };
};

export const markWord = async (id: string, status: WordStatus) =>
  (await api.post<WordCard>(`${BASE}/entries/${encodeURIComponent(id)}/mark`, { status })).data;

export const saveWord = async (id: string, saved: boolean) =>
  (await api.put<WordCard>(`${BASE}/entries/${encodeURIComponent(id)}/saved`, { saved })).data;

export const getMyWords = async (kind: "saved" | "known" | "unknown", page = 1) => {
  const data = (await api.get<MyWords>(`${BASE}/my`, { params: { kind, page } })).data;
  return { ...data, items: items(data) };
};

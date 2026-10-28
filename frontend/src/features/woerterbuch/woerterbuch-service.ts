import { api } from "@/services/api";

const BASE = "/api/v1/dictionary";

export const CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1"] as const;
export type CefrLevel = (typeof CEFR_LEVELS)[number];
/** The CSV's own status — "verified" only after a teacher's review. */
export type WordStatus = "verified" | "needs_review";

/** One word as a list item. `id` = "<level>-<id in the level's CSV>", e.g. "A1-2". */
export interface WordBrief {
  id: string;
  level: CefrLevel;
  lemma: string;
  article: "der" | "die" | "das" | null;
  word_type: string | null;
  translation: string;
  status: WordStatus;
  saved: boolean;
}

export interface PresentForm {
  person: string;
  form: string;
}

export interface WordCard extends WordBrief {
  plural: string | null;
  other_translations: string[];
  verb: {
    infinitive: string;
    praeteritum: string | null;
    partizip_ii: string | null;
    auxiliary: string | null;
    praesens: PresentForm[] | null;
  } | null;
  adjective: { positiv: string; komparativ: string | null; superlativ: string | null } | null;
  /** worterbuch-extra-data.csv: noun_genitive, verb_perfekt, ipa, conjunction_word_order … */
  details: Record<string, unknown>;
  example_de: string | null;
  example_uz: string | null;
  /** text for the browser's TTS; null = nothing to pronounce */
  audio_text: string | null;
  review_note: string | null;
  also_in: CefrLevel[];
  attribution: { name: string; license: string; url: string } | null;
}

export interface Paged<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface SavedWords extends Paged<WordBrief> {
  by_level: Record<CefrLevel, number>;
}

export interface DictionaryMeta {
  total: number;
  rows: Record<CefrLevel, number>;
  levels: Record<CefrLevel, number>;
  word_types: string[];
  attribution: { name: string; license: string; url: string };
}

export interface RandomFive {
  level: CefrLevel | "ALL";
  complete: boolean;
  items: WordCard[];
}

export interface SearchFilters {
  q: string;
  level?: CefrLevel | "";
  word_type?: string;
  page?: number;
}

const items = <T,>(data: { items?: T[] } | undefined): T[] => (Array.isArray(data?.items) ? data!.items! : []);
const clean = (params: Record<string, unknown>) => Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ""));

export const getDictionaryMeta = async () => (await api.get<DictionaryMeta>(`${BASE}/meta`)).data;

export const searchWords = async ({ q, level, word_type, page = 1 }: SearchFilters, signal?: AbortSignal) => {
  const data = (await api.get<Paged<WordBrief>>(`${BASE}/search`, { params: clean({ q, level, word_type, page, page_size: 10 }), signal })).data;
  return { ...data, items: items(data) };
};

export const getWord = async (id: string) => (await api.get<WordCard>(`${BASE}/entries/${encodeURIComponent(id)}`)).data;

export const drawRandomFive = async (level: CefrLevel | "ALL") => {
  const data = (await api.post<RandomFive>(`${BASE}/random`, { level })).data;
  return { ...data, items: items(data) };
};

export const setWordSaved = async (id: string, saved: boolean) =>
  (await api.put<{ id: string; saved: boolean }>(`${BASE}/entries/${encodeURIComponent(id)}/saved`, { saved })).data;

export const getSavedWords = async ({ q, level, page = 1 }: SearchFilters, signal?: AbortSignal) => {
  const data = (await api.get<SavedWords>(`${BASE}/saved`, { params: clean({ q, level, page, page_size: 20 }), signal })).data;
  return { ...data, items: items(data) };
};

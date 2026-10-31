import { api } from "@/src/services/api";

const BASE = "/api/v1/lesson-skills";

/** One lesson word as the student dictionary shows it (backend
 * app/services/lesson_skills/wortschatz.py). Grammar fields come from the
 * course book or a verified Wörterbuch entry (`sources`); `missing` lists what
 * is not known yet — shown as such, never guessed. */
export interface WortschatzWord {
  id: string;
  lesson_id: string;
  lesson_number: number;
  lesson_title: string;
  german_word: string;
  article: string | null;
  plural: string | null;
  translation: string;
  word_type: string | null;
  verb_praeteritum: string | null;
  verb_partizip_ii: string | null;
  verb_auxiliary: string | null;
  example_sentence: string | null;
  example_translation: string | null;
  audio_url: string | null;
  audio_text: string;
  sources: Record<string, string>;
  missing: string[];
  saved: boolean;
  learned: boolean;
}

export interface WortschatzTopic {
  lesson_id: string;
  number: number;
  title: string;
}

export interface WortschatzWords {
  scope: "lesson" | "level";
  topics: WortschatzTopic[];
  words: WortschatzWord[];
}

export async function getWortschatzWords(lessonId: string, scope: "lesson" | "level" = "lesson"): Promise<WortschatzWords> {
  const data = (await api.get<WortschatzWords>(`${BASE}/${lessonId}/wortschatz/words`, { params: { scope } })).data;
  return { scope: data?.scope ?? scope, topics: Array.isArray(data?.topics) ? data.topics : [], words: Array.isArray(data?.words) ? data.words : [] };
}

export async function setWortschatzWordState(
  lessonId: string,
  wordId: string,
  state: { saved?: boolean; learned?: boolean },
): Promise<WortschatzWord> {
  return (await api.put<WortschatzWord>(`${BASE}/${lessonId}/wortschatz/words/${wordId}/state`, state)).data;
}

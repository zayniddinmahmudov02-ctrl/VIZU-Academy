/** Client-side search / filter of the student Wortschatz list (pure — unit
 * tested in tests/unit/wortschatz-filter.test.mjs). German and Uzbek search:
 * case-insensitive, ä/ae ö/oe ü/ue ß/ss treated alike, the Uzbek apostrophe
 * variants (' ‘ ’ ʻ ʼ `) as one, the article optional. */

export interface FilterableWord {
  german_word: string;
  article: string | null;
  plural: string | null;
  translation: string;
  word_type: string | null;
  lesson_number: number;
  saved: boolean;
  learned: boolean;
}

export interface WordFilter {
  query: string;
  topic: number | null;
  wordType: string | null;
  onlySaved: boolean;
  hideLearned: boolean;
}

export function normaliseSearch(value: string): string {
  return value
    .toLocaleLowerCase("de")
    .normalize("NFC")
    .replace(/[‘’ʻʼ`´]/g, "'")
    .replace(/ä/g, "a").replace(/ö/g, "o").replace(/ü/g, "u").replace(/ß/g, "ss")
    .replace(/ae/g, "a").replace(/oe/g, "o").replace(/ue/g, "u")
    .replace(/\s+/g, " ")
    .trim();
}

export function filterWords<T extends FilterableWord>(words: T[], f: WordFilter): T[] {
  const q = normaliseSearch(f.query.replace(/^(der|die|das)\s+/i, ""));
  return words.filter((w) => {
    if (f.topic !== null && w.lesson_number !== f.topic) return false;
    if (f.wordType && w.word_type !== f.wordType) return false;
    if (f.onlySaved && !w.saved) return false;
    if (f.hideLearned && w.learned) return false;
    if (!q) return true;
    return [w.german_word, w.plural ?? "", w.translation].some((v) => normaliseSearch(v).includes(q));
  });
}

/** Word types present in the list, in a fixed teaching order. */
export function wordTypes(words: FilterableWord[]): string[] {
  const order = ["Nomen", "Verb", "Adjektiv", "Adverb", "Präposition", "Konjunktion", "Pronomen", "Wendung"];
  const present = new Set(words.map((w) => w.word_type).filter((t): t is string => !!t));
  return [...order.filter((t) => present.has(t)), ...[...present].filter((t) => !order.includes(t)).sort()];
}

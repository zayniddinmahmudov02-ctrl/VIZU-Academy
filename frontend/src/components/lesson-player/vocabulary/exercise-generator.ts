import type { LessonVocabularyItem } from "@/features/lessons/services/vocabulary-service";

export type VocabularyExercise =
  | { kind: "MULTIPLE_CHOICE"; word: LessonVocabularyItem; choices: string[]; correctAnswer: string }
  | { kind: "ARTIKEL"; word: LessonVocabularyItem; choices: string[]; correctAnswer: string }
  | { kind: "LUECKENTEXT"; word: LessonVocabularyItem; sentenceWithBlank: string; correctAnswer: string }
  | { kind: "WORT_ORDNEN"; word: LessonVocabularyItem; scrambledTokens: string[]; correctTokens: string[] }
  | { kind: "ZUORDNUNG"; words: LessonVocabularyItem[] };

const ARTICLES = ["der", "die", "das"];

function shuffle<T>(items: T[]): T[] {
  const arr = [...items];
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function pickRandom<T>(items: T[]): T {
  return items[Math.floor(Math.random() * items.length)];
}

function buildMultipleChoice(word: LessonVocabularyItem, pool: LessonVocabularyItem[]): VocabularyExercise {
  const distractorPool = shuffle(
    pool.filter((w) => w.id !== word.id && w.translation !== word.translation).map((w) => w.translation),
  );
  const distractors = distractorPool.slice(0, 3);
  return {
    kind: "MULTIPLE_CHOICE",
    word,
    choices: shuffle([word.translation, ...distractors]),
    correctAnswer: word.translation,
  };
}

function buildArtikel(word: LessonVocabularyItem): VocabularyExercise {
  return { kind: "ARTIKEL", word, choices: ARTICLES, correctAnswer: word.article ?? "" };
}

function findWordInSentence(word: string, sentence: string): string | null {
  const match = sentence.match(new RegExp(`\\b${word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i"));
  return match ? match[0] : null;
}

function buildLueckentext(word: LessonVocabularyItem): VocabularyExercise | null {
  const sentence = word.example_sentence;
  if (!sentence) return null;
  const match = findWordInSentence(word.german_word, sentence);
  if (!match) return null;
  return {
    kind: "LUECKENTEXT",
    word,
    sentenceWithBlank: sentence.replace(match, "_____"),
    correctAnswer: match,
  };
}

function buildWortOrdnen(word: LessonVocabularyItem): VocabularyExercise | null {
  const sentence = word.example_sentence;
  if (!sentence) return null;
  const tokens = sentence.split(/\s+/).filter(Boolean);
  if (tokens.length < 2) return null;
  return {
    kind: "WORT_ORDNEN",
    word,
    scrambledTokens: shuffle(tokens),
    correctTokens: tokens,
  };
}

/** Generates one interactive exercise set from a lesson's published
 * Vocabulary rows — client-side only, no admin authoring involved (see
 * plan Feature 1). A batch of up to 4 words becomes one Zuordnung
 * (matching) exercise when there are enough words; every remaining word
 * gets exactly one exercise, randomly chosen among the types its own
 * fields make eligible (every word can always do MULTIPLE_CHOICE). */
export function generateExercises(words: LessonVocabularyItem[]): VocabularyExercise[] {
  if (words.length === 0) return [];

  const shuffledWords = shuffle(words);
  const exercises: VocabularyExercise[] = [];

  let remaining = shuffledWords;
  if (shuffledWords.length >= 3) {
    const batchSize = Math.min(4, shuffledWords.length);
    const matchingWords = shuffledWords.slice(0, batchSize);
    exercises.push({ kind: "ZUORDNUNG", words: matchingWords });
    remaining = shuffledWords.slice(batchSize);
  }

  for (const word of remaining) {
    const builders: (() => VocabularyExercise | null)[] = [() => buildMultipleChoice(word, words)];
    if (word.article) builders.push(() => buildArtikel(word));
    if (word.example_sentence) {
      builders.push(() => buildLueckentext(word));
      builders.push(() => buildWortOrdnen(word));
    }

    // Try the randomly chosen builder; some (Lückentext/Wort ordnen) can
    // return null if the sentence doesn't actually contain the word —
    // fall back to plain multiple choice, which is always eligible.
    const exercise = pickRandom(builders)() ?? buildMultipleChoice(word, words);
    exercises.push(exercise);
  }

  return shuffle(exercises);
}

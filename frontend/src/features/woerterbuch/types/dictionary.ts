export type Article = "der" | "die" | "das";

export interface DictionaryEntry {
  word: string;
  article?: Article;
  plural?: string;
  translation: string;
  partOfSpeech: string;
  cefrLevel: string;
  exampleSentence?: string;
}

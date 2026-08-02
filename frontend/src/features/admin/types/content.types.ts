// Mirrors backend Pydantic schemas exactly (see app/schemas/**). Every
// *Create/*Update type maps 1:1 onto the corresponding request body; every
// plain type maps onto the response body.

export interface Language {
  id: string;
  code: string;
  name: string;
  flag: string | null;
  is_active: boolean;
}
export interface LanguageCreate {
  code: string;
  name: string;
  flag?: string | null;
  is_active?: boolean;
}
export type LanguageUpdate = Partial<LanguageCreate>;

export interface Level {
  id: string;
  language_id: string;
  level: string;
  title: string;
  description: string | null;
  order_index: number;
  is_active: boolean;
}
export interface LevelCreate {
  language_id: string;
  level: string;
  title: string;
  description?: string | null;
  order_index?: number;
  is_active?: boolean;
}
export type LevelUpdate = Partial<LevelCreate>;

export interface ModuleItem {
  id: string;
  course_id: string;
  number: number;
  title: string;
  description: string | null;
  order_index: number;
  is_active: boolean;
}
export interface ModuleCreate {
  course_id: string;
  number: number;
  title: string;
  description?: string | null;
  order_index?: number;
  is_active?: boolean;
}
export type ModuleUpdate = Partial<Omit<ModuleCreate, "course_id">>;

export interface Lesson {
  id: string;
  module_id: string;
  number: number;
  title: string;
  video_url: string | null;
  duration: number;
  is_free: boolean;
}
export interface LessonCreate {
  module_id: string;
  number: number;
  title: string;
  video_url?: string | null;
  duration?: number;
  is_free?: boolean;
}
export type LessonUpdate = Partial<Omit<LessonCreate, "module_id">>;

export interface Video {
  id: string;
  lesson_id: string;
  title: string;
  description: string | null;
  video_url: string | null;
  thumbnail_url: string | null;
  duration_seconds: number;
  order_index: number;
  is_preview: boolean;
  is_published: boolean;
}
export interface VideoUpdate {
  title?: string;
  description?: string | null;
  thumbnail_url?: string | null;
  duration_seconds?: number;
  order_index?: number;
  is_preview?: boolean;
  is_published?: boolean;
}

export interface Vocabulary {
  id: string;
  lesson_id: string;
  german_word: string;
  article: string | null;
  plural: string | null;
  translation: string;
  example_sentence: string | null;
  example_translation: string | null;
  audio_url: string | null;
  image_url: string | null;
  order_index: number;
  is_published: boolean;
}
export interface VocabularyCreate {
  lesson_id: string;
  german_word: string;
  article?: string | null;
  plural?: string | null;
  translation: string;
  example_sentence?: string | null;
  example_translation?: string | null;
  audio_url?: string | null;
  image_url?: string | null;
  order_index?: number;
  is_published?: boolean;
}
export type VocabularyUpdate = Partial<Omit<VocabularyCreate, "lesson_id">>;

export interface Grammar {
  id: string;
  lesson_id: string;
  title: string;
  content: string;
  video_url: string | null;
  order_index: number;
  is_published: boolean;
}
export interface GrammarCreate {
  lesson_id: string;
  title: string;
  content: string;
  video_url?: string | null;
  order_index?: number;
  is_published?: boolean;
}
export type GrammarUpdate = Partial<Omit<GrammarCreate, "lesson_id">>;

export interface Reading {
  id: string;
  lesson_id: string;
  title: string;
  content: string;
  order_index: number;
  is_published: boolean;
}
export interface ReadingCreate {
  lesson_id: string;
  title: string;
  content: string;
  order_index?: number;
  is_published?: boolean;
}
export type ReadingUpdate = Partial<Omit<ReadingCreate, "lesson_id">>;

export interface ReadingQuestion {
  id: string;
  reading_id: string;
  question: string;
  explanation: string | null;
  order_index: number;
  is_published: boolean;
}
export interface ReadingQuestionCreate {
  reading_id: string;
  question: string;
  explanation?: string | null;
  order_index?: number;
  is_published?: boolean;
}
export type ReadingQuestionUpdate = Partial<Omit<ReadingQuestionCreate, "reading_id">>;

export interface ReadingOption {
  id: string;
  question_id: string;
  option_text: string;
  is_correct: boolean;
  order_index: number;
}
export interface ReadingOptionCreate {
  question_id: string;
  option_text: string;
  is_correct?: boolean;
  order_index?: number;
}
export type ReadingOptionUpdate = Partial<Omit<ReadingOptionCreate, "question_id">>;

export interface Listening {
  id: string;
  lesson_id: string;
  title: string;
  audio_url: string;
  transcript: string | null;
  order_index: number;
  is_published: boolean;
}
export interface ListeningCreate {
  lesson_id: string;
  title: string;
  audio_url: string;
  transcript?: string | null;
  order_index?: number;
  is_published?: boolean;
}
export type ListeningUpdate = Partial<Omit<ListeningCreate, "lesson_id">>;

export interface Writing {
  id: string;
  lesson_id: string;
  title: string;
  instruction: string;
  min_words: number;
  max_words: number;
  order_index: number;
  is_published: boolean;
}
export interface WritingCreate {
  lesson_id: string;
  title: string;
  instruction: string;
  min_words?: number;
  max_words?: number;
  order_index?: number;
  is_published?: boolean;
}
export type WritingUpdate = Partial<Omit<WritingCreate, "lesson_id">>;

export interface Speaking {
  id: string;
  lesson_id: string;
  title: string;
  topic: string;
  instruction: string;
  sample_answer: string | null;
  keywords: string | null;
  preparation_time: number;
  speaking_time: number;
  order_index: number;
  is_published: boolean;
}
export interface SpeakingCreate {
  lesson_id: string;
  title: string;
  topic: string;
  instruction: string;
  sample_answer?: string | null;
  keywords?: string | null;
  preparation_time?: number;
  speaking_time?: number;
  order_index?: number;
  is_published?: boolean;
}
export type SpeakingUpdate = Partial<Omit<SpeakingCreate, "lesson_id">>;

export interface Quiz {
  id: string;
  lesson_id: string;
  title: string;
  description: string | null;
  passing_score: number;
  order_index: number;
  is_published: boolean;
}
export interface QuizCreate {
  lesson_id: string;
  title: string;
  description?: string | null;
  passing_score?: number;
  order_index?: number;
  is_published?: boolean;
}
export type QuizUpdate = Partial<Omit<QuizCreate, "lesson_id">>;

export interface QuizQuestion {
  id: string;
  quiz_id: string;
  question: string;
  explanation: string | null;
  points: number;
  order_index: number;
  is_published: boolean;
}
export interface QuizQuestionCreate {
  quiz_id: string;
  question: string;
  explanation?: string | null;
  points?: number;
  order_index?: number;
  is_published?: boolean;
}
export type QuizQuestionUpdate = Partial<Omit<QuizQuestionCreate, "quiz_id">>;

export interface QuizOption {
  id: string;
  question_id: string;
  option_text: string;
  is_correct: boolean;
  order_index: number;
}
export interface QuizOptionCreate {
  question_id: string;
  option_text: string;
  is_correct?: boolean;
  order_index?: number;
}
export type QuizOptionUpdate = Partial<Omit<QuizOptionCreate, "question_id">>;

export interface Homework {
  id: string;
  lesson_id: string;
  title: string;
  description: string;
  max_score: number;
  is_published: boolean;
}
export interface HomeworkCreate {
  lesson_id: string;
  title: string;
  description: string;
  max_score?: number;
  is_published?: boolean;
}
export type HomeworkUpdate = Partial<Omit<HomeworkCreate, "lesson_id">>;

export interface ExamProvider {
  id: string;
  name: string;
  code: string;
}
export interface ExamProviderCreate {
  name: string;
  code: string;
}
export type ExamProviderUpdate = Partial<ExamProviderCreate>;

export interface Exam {
  id: string;
  provider_id: string;
  level: string;
  title: string;
  duration: number;
  is_active: boolean;
}
export interface ExamCreate {
  provider_id: string;
  level: string;
  title: string;
  duration?: number;
  is_active?: boolean;
}
export interface ExamUpdate {
  title?: string;
  duration?: number;
  is_active?: boolean;
}

export interface MediaAsset {
  id: string;
  filename: string;
  url: string;
  folder: string;
  media_type: "video" | "audio" | "image" | "document";
  content_type: string | null;
  size_bytes: number | null;
  uploaded_by: string | null;
}

// Mirrors backend/app/schemas/language/schema.py exactly.

export interface Language {
  id: string;
  code: string;
  locale: string;
  name: string;
  native_name: string | null;
  english_name: string | null;
  flag_file: string | null;
  primary_color: string | null;
  description: string | null;
  is_default: boolean;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
  learners_count: number;
  levels_count: number;
  modules_count: number;
  lessons_count: number;
}

export interface LanguageCreate {
  code: string;
  locale: string;
  name: string;
  native_name?: string | null;
  english_name?: string | null;
  flag_file?: string | null;
  primary_color?: string | null;
  description?: string | null;
  is_default?: boolean;
  is_active?: boolean;
  sort_order?: number;
}

export type LanguageUpdate = Partial<LanguageCreate>;

export interface LanguageStatistics {
  language_id: string;
  learners: number;
  active_learners: number;
  levels: number;
  modules: number;
  lessons: number;
  videos: number;
  vocabulary: number;
  grammar: number;
  reading: number;
  listening: number;
  writing: number;
  speaking: number;
  homework: number;
  quiz: number;
  mock_tests: number;
  certificates: number;
}

export interface LanguageLearnerItem {
  id: string;
  username: string;
  email: string;
  is_primary: boolean;
  joined_at: string;
  last_activity: string | null;
}

export interface LanguageLearnersResponse {
  items: LanguageLearnerItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LanguageSettings {
  language_id: string;
  certificates_enabled: boolean;
  leaderboard_enabled: boolean;
  vocabulary_enabled: boolean;
  grammar_enabled: boolean;
  reading_enabled: boolean;
  listening_enabled: boolean;
  writing_enabled: boolean;
  speaking_enabled: boolean;
  homework_enabled: boolean;
  quiz_enabled: boolean;
  ai_writing_enabled: boolean;
  ai_speaking_enabled: boolean;
  mock_exams_enabled: boolean;
  video_lessons_enabled: boolean;
  media_library_enabled: boolean;
}

export type LanguageSettingsUpdate = Partial<Omit<LanguageSettings, "language_id">>;

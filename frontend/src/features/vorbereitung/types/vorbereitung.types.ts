// Mirrors the public-facing subset of backend/app/schemas/mock_exam/schema.py
// exposed by app/api/mock_exam/public_router.py — published/active-only,
// never includes questions, options, or anything answer-key-shaped.

export const KOMPETENZ_TYPES = ["LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"] as const;
export type KompetenzType = (typeof KOMPETENZ_TYPES)[number];

export interface PublicProvider {
  id: string;
  name: string;
  code: string;
  logo_url: string | null;
  description: string | null;
  color: string | null;
  is_active: boolean;
  sort_order: number;
}

export interface PublicLevel {
  id: string;
  provider_id: string;
  level: string;
  title: string | null;
  description: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface PublicModelTest {
  id: string;
  level_id: string;
  title: string;
  description: string | null;
  sort_order: number;
}

export interface PublicKompetenzSummary {
  id: string;
  type: KompetenzType;
  title: string;
  has_content: boolean;
}

export interface PublicModelTestDetail {
  id: string;
  level_id: string;
  title: string;
  description: string | null;
  kompetenzen: PublicKompetenzSummary[];
}

export interface PublicReadingContent {
  id: string;
  teil_id: string;
  content_type: "TEXT" | "IMAGE" | "TEXT_IMAGE";
  text: string | null;
  image_url: string | null;
}

export interface PublicListeningContent {
  id: string;
  teil_id: string;
  audio_url: string;
  image_url: string | null;
  transcript: string | null;
}

export interface PublicWritingTask {
  id: string;
  teil_id: string;
  task_text: string;
  image_url: string | null;
  reference_document_url: string | null;
  word_limit: number | null;
  time_limit_minutes: number | null;
}

export interface PublicSpeakingTask {
  id: string;
  teil_id: string;
  task_text: string;
  image_url: string | null;
  preparation_time_seconds: number;
  speaking_time_seconds: number;
  max_recording_duration_seconds: number;
}

export interface PublicTeilContent {
  id: string;
  title: string;
  description: string | null;
  instructions: string | null;
  reading_content: PublicReadingContent | null;
  listening_content: PublicListeningContent | null;
  writing_task: PublicWritingTask | null;
  speaking_task: PublicSpeakingTask | null;
}

export interface PublicKompetenzDetail {
  id: string;
  model_test_id: string;
  type: KompetenzType;
  title: string;
  description: string | null;
  duration_minutes: number;
  teile: PublicTeilContent[];
}

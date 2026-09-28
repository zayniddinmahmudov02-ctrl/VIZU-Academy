import {
  ClipboardCheck,
  FileText,
  Headphones,
  ListChecks,
  Mic,
  PenLine,
  PlayCircle,
  Trophy,
  type LucideIcon,
} from "lucide-react";

import type { SectionGateKey } from "@/features/lessons/services/section-gate-service";

export type LessonSectionType =
  | "video"
  | "reading"
  | "listening"
  | "writing"
  | "speaking"
  | "vocabulary-quiz"
  | "lesson-quiz"
  | "results";

export interface LessonSectionMeta {
  /** URL segment, e.g. /lessons/1/wortschatz-test */
  slug: string;
  type: LessonSectionType;
  icon: LucideIcon;
  emoji: string;
  titleKey: string;
}

// Fixed student order: Video dars -> Lesen -> Hören -> Schreiben ->
// Sprechen -> Wortschatz Test -> Yakuniy Test -> Natijalar, identical for
// every lesson and never reordered based on which sections happen to
// have content. None of these sections gate each other — every one of
// them is independently reachable (see backend/app/services/
// lesson_progress/section_gate.py; the "unlocked" field it still returns
// per section is unconditionally true, kept only for API compatibility).
//
// Grammatik, Grammatik Quiz, the Wortschatz browsing/learning step and
// Hausaufgabe are no longer student steps: their slugs no longer resolve
// (getSectionBySlug returns undefined, so the route 404s). Their content
// and backend endpoints are untouched — this is only the student
// navigation/delivery.
//
// "reading"/"listening"/"writing"/"speaking" render from the LEGACY
// readings/listenings/writings/speakings tables (the Universal
// Assessment Engine is deliberately not their student-facing source).
// "vocabulary-quiz" (Wortschatz Test) self-detects whether the lesson has
// a VOCABULARY-type Quiz and shows "not available" otherwise; its
// sidebar entry is hidden for lessons without one (see section-progress).
// "lesson-quiz" is the Yakuniy Test: the lesson's LESSON-type Quiz.
export const lessonSections: LessonSectionMeta[] = [
  { slug: "video", type: "video", icon: PlayCircle, emoji: "🎥", titleKey: "lessons.sectionVideo" },
  { slug: "lesen", type: "reading", icon: FileText, emoji: "📖", titleKey: "lessons.sectionReading" },
  { slug: "hoeren", type: "listening", icon: Headphones, emoji: "🎧", titleKey: "lessons.sectionListening" },
  { slug: "schreiben", type: "writing", icon: PenLine, emoji: "✍️", titleKey: "lessons.sectionWriting" },
  { slug: "sprechen", type: "speaking", icon: Mic, emoji: "🎤", titleKey: "lessons.sectionSpeaking" },
  {
    slug: "wortschatz-test",
    type: "vocabulary-quiz",
    icon: ListChecks,
    emoji: "📚",
    titleKey: "lessons.sectionVocabularyQuiz",
  },
  {
    slug: "yakuniy-test",
    type: "lesson-quiz",
    icon: ClipboardCheck,
    emoji: "📝",
    titleKey: "lessons.sectionLessonQuiz",
  },
  { slug: "natijalar", type: "results", icon: Trophy, emoji: "📊", titleKey: "lessons.sectionResults" },
];

export const DEFAULT_SECTION_SLUG = lessonSections[0].slug;

export function getSectionBySlug(slug: string): LessonSectionMeta | undefined {
  return lessonSections.find((section) => section.slug === slug);
}

export function getSectionIndex(slug: string): number {
  return lessonSections.findIndex((section) => section.slug === slug);
}

// Maps a lesson-section type to its backend section-gate key — null for
// sections with no gate entry (Ergebnisse).
export const SECTION_GATE_KEYS: Record<LessonSectionType, SectionGateKey | null> = {
  video: "video",
  reading: "lesen",
  listening: "hoeren",
  writing: "schreiben",
  speaking: "sprechen",
  "vocabulary-quiz": "wortschatz_quiz",
  "lesson-quiz": "lesson_quiz",
  results: null,
};

// The sections that actually have a completion signal — mirrors the
// backend's GATED_ORDER (section_gate.py). Lesen/Hören are passage/audio
// only (no completion concept yet), so they are shown but never counted
// toward "X/Y abgeschlossen" (which could otherwise never reach 100%).
export const COMPLETION_TRACKED_GATE_KEYS: readonly SectionGateKey[] = [
  "video",
  "schreiben",
  "sprechen",
  "wortschatz_quiz",
  "lesson_quiz",
];

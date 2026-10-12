import {
  BookMarked,
  ClipboardCheck,
  FileText,
  Headphones,
  Languages,
  MessageCircleQuestion,
  Mic,
  PenLine,
  PlayCircle,
  Trophy,
  type LucideIcon,
} from "lucide-react";

import type { SectionGateKey } from "@/features/lessons/services/section-gate-service";

export type LessonSectionType =
  | "video"
  | "frage"
  | "grammar"
  | "reading"
  | "listening"
  | "writing"
  | "speaking"
  | "vocabulary"
  | "lesson-quiz"
  | "results";

export interface LessonSectionMeta {
  /** URL segment, e.g. /lessons/1/grammatik */
  slug: string;
  type: LessonSectionType;
  icon: LucideIcon;
  emoji: string;
  titleKey: string;
}

// Fixed student order (lesson flow v3, VIZU-DEUTSCH book): Video dars ->
// Frage des Themas -> Grammatik -> Lesen -> Hören -> Schreiben -> Sprechen
// -> Wortschatz -> Yakuniy Test -> Natijalar — identical for every lesson
// and level; a step the lesson has no content for is hidden in the
// sidebar (see section-progress.ts). There is no Hausaufgaben step.
//
// None of these sections gate each other — every one is independently
// reachable (backend app/services/lesson_progress/section_gate.py; its
// "unlocked" field is unconditionally true).
//
// Grammatik / Wortschatz / Yakuniy Test are server-graded exercise sets
// (skill_exercises); a lesson that still only has the legacy VOCABULARY /
// LESSON quiz shows that quiz in the same step. Frage des Themas is a voice
// answer recorded with the Sprechen recorder (speakings.task_kind FRAGE).
export const lessonSections: LessonSectionMeta[] = [
  { slug: "video", type: "video", icon: PlayCircle, emoji: "🎥", titleKey: "lessons.sectionVideo" },
  { slug: "frage", type: "frage", icon: MessageCircleQuestion, emoji: "❓", titleKey: "lessons.sectionFrage" },
  { slug: "grammatik", type: "grammar", icon: BookMarked, emoji: "📐", titleKey: "lessons.sectionGrammar" },
  { slug: "lesen", type: "reading", icon: FileText, emoji: "📖", titleKey: "lessons.sectionReading" },
  { slug: "hoeren", type: "listening", icon: Headphones, emoji: "🎧", titleKey: "lessons.sectionListening" },
  { slug: "schreiben", type: "writing", icon: PenLine, emoji: "✍️", titleKey: "lessons.sectionWriting" },
  { slug: "sprechen", type: "speaking", icon: Mic, emoji: "🎤", titleKey: "lessons.sectionSpeaking" },
  { slug: "wortschatz", type: "vocabulary", icon: Languages, emoji: "📚", titleKey: "lessons.sectionVocabulary" },
  { slug: "yakuniy-test", type: "lesson-quiz", icon: ClipboardCheck, emoji: "📝", titleKey: "lessons.sectionLessonQuiz" },
  { slug: "natijalar", type: "results", icon: Trophy, emoji: "📊", titleKey: "lessons.sectionResults" },
];

// Old links (lesson flow v2) keep working.
const SLUG_ALIASES: Record<string, string> = { "wortschatz-test": "wortschatz" };

export const DEFAULT_SECTION_SLUG = lessonSections[0].slug;

export function getSectionBySlug(slug: string): LessonSectionMeta | undefined {
  const target = SLUG_ALIASES[slug] ?? slug;
  return lessonSections.find((section) => section.slug === target);
}

export function getSectionIndex(slug: string): number {
  const target = SLUG_ALIASES[slug] ?? slug;
  return lessonSections.findIndex((section) => section.slug === target);
}

// Maps a lesson-section type to its backend section-gate key — null for
// sections with no gate entry (Natijalar).
export const SECTION_GATE_KEYS: Record<LessonSectionType, SectionGateKey | null> = {
  video: "video",
  frage: "frage",
  grammar: "grammatik_test",
  reading: "lesen_test",
  listening: "hoeren_test",
  writing: "schreiben",
  speaking: "sprechen",
  vocabulary: "wortschatz_test",
  "lesson-quiz": "yakuniy_test",
  results: null,
};

// Every step counts toward "X/Y abgeschlossen" — mirrors the backend's
// GATED_ORDER (section_gate.py); a step the lesson has no content for is
// not applicable and therefore never counted.
export const COMPLETION_TRACKED_GATE_KEYS: readonly SectionGateKey[] = [
  "video",
  "frage",
  "grammatik_test",
  "lesen_test",
  "hoeren_test",
  "schreiben",
  "sprechen",
  "wortschatz_test",
  "yakuniy_test",
];

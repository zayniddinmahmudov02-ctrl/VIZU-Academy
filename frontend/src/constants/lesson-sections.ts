import {
  BookOpenText,
  ClipboardList,
  FileText,
  Headphones,
  HelpCircle,
  Library,
  Mic,
  PenLine,
  PlayCircle,
  Trophy,
  type LucideIcon,
} from "lucide-react";

import type { SectionGateKey } from "@/features/lessons/services/section-gate-service";

export type LessonSectionType =
  | "video"
  | "vocabulary"
  | "grammar"
  | "grammar-quiz"
  | "reading"
  | "listening"
  | "writing"
  | "speaking"
  | "lesson-quiz"
  | "homework"
  | "results";

export interface LessonSectionMeta {
  /** URL segment, e.g. /lessons/1/grammatik */
  slug: string;
  type: LessonSectionType;
  icon: LucideIcon;
  emoji: string;
  titleKey: string;
}

// Fixed order — identical to the Admin CMS lesson-content order, never
// reordered based on which sections happen to have content (see
// LessonContentGate). "reading"/"listening" here render "Lesen"/"Hören"
// (their real titleKeys), each already the Universal Assessment Engine's
// combined passage+questions flow — there's no separate "Lesen Quiz"/
// "Hören Quiz" step to route to, only a labeled distinction in the admin
// content-status view. homework has no fixed point in the required
// 100-point order, so it's kept at the end rather than dropped.
export const lessonSections: LessonSectionMeta[] = [
  { slug: "video", type: "video", icon: PlayCircle, emoji: "▶️", titleKey: "lessons.sectionVideo" },
  { slug: "wortschatz", type: "vocabulary", icon: Library, emoji: "📖", titleKey: "lessons.sectionVocabulary" },
  { slug: "grammatik", type: "grammar", icon: BookOpenText, emoji: "📘", titleKey: "lessons.sectionGrammar" },
  { slug: "grammatik-quiz", type: "grammar-quiz", icon: HelpCircle, emoji: "❓", titleKey: "lessons.sectionGrammarQuiz" },
  { slug: "lesen", type: "reading", icon: FileText, emoji: "📄", titleKey: "lessons.sectionReading" },
  { slug: "hoeren", type: "listening", icon: Headphones, emoji: "🎧", titleKey: "lessons.sectionListening" },
  { slug: "schreiben", type: "writing", icon: PenLine, emoji: "✍️", titleKey: "lessons.sectionWriting" },
  { slug: "sprechen", type: "speaking", icon: Mic, emoji: "🎤", titleKey: "lessons.sectionSpeaking" },
  { slug: "lesson-quiz", type: "lesson-quiz", icon: Trophy, emoji: "🏆", titleKey: "lessons.sectionLessonQuiz" },
  { slug: "hausaufgabe", type: "homework", icon: ClipboardList, emoji: "📝", titleKey: "lessons.sectionHomework" },
  { slug: "ergebnis", type: "results", icon: Trophy, emoji: "📊", titleKey: "lessons.sectionResults" },
];

export const DEFAULT_SECTION_SLUG = lessonSections[0].slug;

export function getSectionBySlug(slug: string): LessonSectionMeta | undefined {
  return lessonSections.find((section) => section.slug === slug);
}

export function getSectionIndex(slug: string): number {
  return lessonSections.findIndex((section) => section.slug === slug);
}

// Maps a lesson-section type to its backend section-gate key — null for
// sections with no completion concept (Hausaufgabe, Ergebnis). Sections
// are no longer sequentially locked; this is only used to look up each
// section's completed/not-completed state for progress display (lesson
// nav checkmarks, results, admin per-student view).
export const SECTION_GATE_KEYS: Record<LessonSectionType, SectionGateKey | null> = {
  video: null,
  vocabulary: "wortschatz",
  grammar: "grammatik",
  "grammar-quiz": "grammatik_quiz",
  reading: "lesen",
  listening: "hoeren",
  writing: "schreiben",
  speaking: "sprechen",
  "lesson-quiz": "lesson_quiz",
  homework: null,
  results: null,
};

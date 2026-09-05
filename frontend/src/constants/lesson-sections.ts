import {
  ClipboardList,
  FileText,
  Headphones,
  HelpCircle,
  Languages,
  Library,
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
  | "vocabulary"
  | "vocabulary-quiz"
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

// Fixed student order (Video / Wortschatz / Wortschatz Quiz / Grammatik /
// Grammatik Quiz / Lesen / Hören / Schreiben / Sprechen / Hausaufgabe /
// Ergebnis), identical to the Admin CMS lesson-content order, never
// reordered based on which sections happen to have content. None of
// these sections gate each other — every one of them is independently
// reachable regardless of what has or hasn't been completed elsewhere
// (see backend/app/services/lesson_progress/section_gate.py; the
// "unlocked" field it still returns per section is now unconditionally
// true, kept only for API/consumer backward compatibility). "Grammatik"
// and "Grammatik Quiz" are two separate sections on purpose — Grammatik
// renders the published Grammar rows for this lesson (its own simple,
// non-gated content type: GrammarSection/grammar-service.ts, backed by
// GET /grammars/lesson/{id}), Grammatik Quiz is the separate multiple-
// choice check. (A prior refactor removed the standalone Grammatik nav
// entry while leaving its backend endpoints, service and section
// component in place unused — this restores the nav entry, not new
// functionality.)
// "reading"/"listening" here render "Lesen"/"Hören" (their real
// titleKeys), each already the Universal Assessment Engine's combined
// passage+questions flow — there's no separate "Lesen Quiz"/"Hören Quiz"
// step to route to, only a labeled distinction in the admin content-
// status view.
//
// "lesson-quiz" (Lesson Quiz) is deliberately NOT in this list — removed
// from student navigation entirely (getSectionBySlug("lesson-quiz") now
// returns undefined, so the route 404s). The Quiz model/admin CRUD/
// QuizManager and the QUIZ_TYPE_LESSON quiz-taking infra are untouched;
// only this student-facing entry point is gone. Backend: excluded from
// GATED_ORDER (section_gate.py) so a lesson with a published-but-
// unreachable Lesson Quiz can still be reported "completed".
//
// "wortschatz-quiz" (A1 only — see vocabulary-quiz-section.tsx, which
// self-detects and shows "nicht verfügbar" for B1-C1) does NOT add its
// own points to the 100-point total: it's how A1 students earn the
// existing 10 Wortschatz points (StudentProgress.vocabulary_score), same
// budget "wortschatz" already accounts for above.
export const lessonSections: LessonSectionMeta[] = [
  { slug: "video", type: "video", icon: PlayCircle, emoji: "▶️", titleKey: "lessons.sectionVideo" },
  { slug: "wortschatz", type: "vocabulary", icon: Library, emoji: "📖", titleKey: "lessons.sectionVocabulary" },
  { slug: "wortschatz-quiz", type: "vocabulary-quiz", icon: ListChecks, emoji: "📝", titleKey: "lessons.sectionVocabularyQuiz" },
  { slug: "grammatik", type: "grammar", icon: Languages, emoji: "🔤", titleKey: "lessons.sectionGrammar" },
  { slug: "grammatik-quiz", type: "grammar-quiz", icon: HelpCircle, emoji: "❓", titleKey: "lessons.sectionGrammarQuiz" },
  { slug: "lesen", type: "reading", icon: FileText, emoji: "📄", titleKey: "lessons.sectionReading" },
  { slug: "hoeren", type: "listening", icon: Headphones, emoji: "🎧", titleKey: "lessons.sectionListening" },
  { slug: "schreiben", type: "writing", icon: PenLine, emoji: "✍️", titleKey: "lessons.sectionWriting" },
  { slug: "sprechen", type: "speaking", icon: Mic, emoji: "🎤", titleKey: "lessons.sectionSpeaking" },
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
// sections with no completion concept (Hausaufgabe, Ergebnis — homework
// has no student-submission/review system yet, so it's never gated or
// required). Real sequential gating: see section-gate-boundary.tsx and
// backend/app/services/lesson_progress/section_gate.py.
export const SECTION_GATE_KEYS: Record<LessonSectionType, SectionGateKey | null> = {
  video: "video",
  vocabulary: "wortschatz",
  "vocabulary-quiz": "wortschatz_quiz",
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

import {
  BookOpenText,
  ClipboardList,
  FileText,
  Headphones,
  Library,
  Mic,
  PenLine,
  PlayCircle,
  Trophy,
  type LucideIcon,
} from "lucide-react";

export type LessonSectionType =
  | "video"
  | "grammar"
  | "vocabulary"
  | "reading"
  | "listening"
  | "writing"
  | "speaking"
  | "homework"
  | "quiz";

export interface LessonSectionMeta {
  /** URL segment, e.g. /lessons/1/grammatik */
  slug: string;
  type: LessonSectionType;
  icon: LucideIcon;
  emoji: string;
  titleKey: string;
}

export const lessonSections: LessonSectionMeta[] = [
  { slug: "video", type: "video", icon: PlayCircle, emoji: "▶️", titleKey: "lessons.sectionVideo" },
  { slug: "grammatik", type: "grammar", icon: BookOpenText, emoji: "📘", titleKey: "lessons.sectionGrammar" },
  { slug: "wortschatz", type: "vocabulary", icon: Library, emoji: "📖", titleKey: "lessons.sectionVocabulary" },
  { slug: "lesen", type: "reading", icon: FileText, emoji: "📄", titleKey: "lessons.sectionReading" },
  { slug: "hoeren", type: "listening", icon: Headphones, emoji: "🎧", titleKey: "lessons.sectionListening" },
  { slug: "schreiben", type: "writing", icon: PenLine, emoji: "✍️", titleKey: "lessons.sectionWriting" },
  { slug: "sprechen", type: "speaking", icon: Mic, emoji: "🎤", titleKey: "lessons.sectionSpeaking" },
  { slug: "hausaufgabe", type: "homework", icon: ClipboardList, emoji: "📝", titleKey: "lessons.sectionHomework" },
  { slug: "quiz", type: "quiz", icon: Trophy, emoji: "🏆", titleKey: "lessons.sectionQuiz" },
];

export const DEFAULT_SECTION_SLUG = lessonSections[0].slug;

export function getSectionBySlug(slug: string): LessonSectionMeta | undefined {
  return lessonSections.find((section) => section.slug === slug);
}

export function getSectionIndex(slug: string): number {
  return lessonSections.findIndex((section) => section.slug === slug);
}

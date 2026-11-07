import type { ExamSection, ResultLevel } from "../types/multilevel-exam.types";

type T = (key: string, vars?: Record<string, string | number>) => string;

export const SECTION_LABEL_KEY: Record<ExamSection, string> = {
  LESEN: "lessons.sectionReading",
  HOEREN: "lessons.sectionListening",
  SCHREIBEN: "lessons.sectionWriting",
  SPRECHEN: "lessons.sectionSpeaking",
};

export function levelLabel(t: T, level: ResultLevel | null | undefined): string {
  if (!level) return "—";
  return level === "B1" || level === "B2" || level === "C1" ? level : t(`multilevelExam.level${level}`);
}

export function levelTone(level: ResultLevel | null | undefined): string {
  if (level === "C1") return "bg-success/15 text-success";
  if (level === "B2") return "bg-accent-blue/15 text-accent-blue";
  if (level === "B1") return "bg-warning/15 text-warning";
  if (level === "NICHT_BESTANDEN") return "bg-danger/15 text-danger";
  return "bg-surface-hover text-text-muted";
}

export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return h ? `${h} h ${m} min` : `${m} min`;
}

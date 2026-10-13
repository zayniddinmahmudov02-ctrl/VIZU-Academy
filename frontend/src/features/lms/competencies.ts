import {
  BookMarked,
  BookOpen,
  ClipboardCheck,
  Dumbbell,
  Flag,
  Headphones,
  Languages,
  Mic,
  PenSquare,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import type { CompetencyKind } from "./types";

/** Display metadata of the ten competencies. The ORDER is never taken from
 * here — it always comes from the backend (`competency_order`, position). */
export const COMPETENCY_META: Record<CompetencyKind, { slug: string; name: string; icon: LucideIcon; descKey: string }> = {
  EINFUEHRUNG: { slug: "einfuehrung", name: "Einführung", icon: Flag, descKey: "lms.descEinfuehrung" },
  WORTSCHATZ: { slug: "wortschatz", name: "Wortschatz", icon: Languages, descKey: "lms.descWortschatz" },
  GRAMMATIK: { slug: "grammatik", name: "Grammatik", icon: BookMarked, descKey: "lms.descGrammatik" },
  LESEN: { slug: "lesen", name: "Lesen", icon: BookOpen, descKey: "lms.descLesen" },
  HOEREN: { slug: "hoeren", name: "Hören", icon: Headphones, descKey: "lms.descHoeren" },
  SPRECHEN: { slug: "sprechen", name: "Sprechen", icon: Mic, descKey: "lms.descSprechen" },
  SCHREIBEN: { slug: "schreiben", name: "Schreiben", icon: PenSquare, descKey: "lms.descSchreiben" },
  UEBUNGEN: { slug: "uebungen", name: "Übungen", icon: Dumbbell, descKey: "lms.descUebungen" },
  ABSCHLUSSTEST: { slug: "abschlusstest", name: "Abschlusstest", icon: ClipboardCheck, descKey: "lms.descAbschlusstest" },
  ZUSAMMENFASSUNG: { slug: "zusammenfassung", name: "Zusammenfassung", icon: Sparkles, descKey: "lms.descZusammenfassung" },
};

export function kindFromSlug(slug: string): CompetencyKind | null {
  const entry = Object.entries(COMPETENCY_META).find(([, meta]) => meta.slug === slug.toLowerCase());
  return entry ? (entry[0] as CompetencyKind) : null;
}

export const lessonHref = (lessonId: string) => `/lektion/${lessonId}`;
export const competencyHref = (lessonId: string, kind: CompetencyKind) => `/lektion/${lessonId}/${COMPETENCY_META[kind].slug}`;
export const levelHref = (level: string) => `/kurse/${level.toLowerCase()}`;

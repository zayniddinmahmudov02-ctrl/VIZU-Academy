import { FileText, Headphones, Mic, PenLine, type LucideIcon } from "lucide-react";

import type { VizuMultilevelSkill } from "../types/vizu-multilevel.types";

export interface VizuMultilevelSkillMeta {
  skill: VizuMultilevelSkill;
  slug: VizuMultilevelSkill;
  labelKey: string;
  icon: LucideIcon;
  /** Matches the 🔵🟣🟢🟠 module colors from the spec. */
  color: string;
  chipClass: string;
  durationMinutes: 20;
}

export const VIZU_MULTILEVEL_DURATION_MINUTES = 20;

export const VIZU_MULTILEVEL_SKILLS: VizuMultilevelSkillMeta[] = [
  {
    skill: "lesen",
    slug: "lesen",
    labelKey: "lessons.sectionReading",
    icon: FileText,
    color: "from-blue-600 to-blue-400",
    chipClass: "bg-blue-500/10 text-blue-600 dark:text-blue-300",
    durationMinutes: 20,
  },
  {
    skill: "hoeren",
    slug: "hoeren",
    labelKey: "lessons.sectionListening",
    icon: Headphones,
    color: "from-purple-600 to-purple-400",
    chipClass: "bg-purple-500/10 text-purple-600 dark:text-purple-300",
    durationMinutes: 20,
  },
  {
    skill: "schreiben",
    slug: "schreiben",
    labelKey: "lessons.sectionWriting",
    icon: PenLine,
    color: "from-emerald-600 to-emerald-400",
    chipClass: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-300",
    durationMinutes: 20,
  },
  {
    skill: "sprechen",
    slug: "sprechen",
    labelKey: "lessons.sectionSpeaking",
    icon: Mic,
    color: "from-orange-600 to-orange-400",
    chipClass: "bg-orange-500/10 text-orange-600 dark:text-orange-300",
    durationMinutes: 20,
  },
];

export function getSkillMeta(skill: string): VizuMultilevelSkillMeta | undefined {
  return VIZU_MULTILEVEL_SKILLS.find((s) => s.skill === skill);
}

export function getSkillIndex(skill: string): number {
  return VIZU_MULTILEVEL_SKILLS.findIndex((s) => s.skill === skill);
}

/** Route of one step of the flow: Lesen → Hören → Schreiben → Sprechen → Ergebnis. */
export function stepPath(attemptId: string, step: VizuMultilevelSkill | "natijalar"): string {
  return `/vizu-multilevel/${attemptId}/${step}`;
}

/** The step after `skill` — the results page after Sprechen. */
export function nextStepPath(attemptId: string, skill: VizuMultilevelSkill): string {
  const next = VIZU_MULTILEVEL_SKILLS[getSkillIndex(skill) + 1];
  return stepPath(attemptId, next ? next.skill : "natijalar");
}

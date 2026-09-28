import {
  COMPLETION_TRACKED_GATE_KEYS,
  SECTION_GATE_KEYS,
  lessonSections,
  type LessonSectionMeta,
} from "@/constants/lesson-sections";
import type { SectionGateState } from "@/features/lessons/services/section-gate-service";

/** A section is only listed if it's actually applicable to this lesson
 * (e.g. Wortschatz Test only when the lesson has a VOCABULARY quiz) *and*
 * has a real gate key (Natijalar doesn't). Reused as-is by the right
 * sidebar and its mobile trigger bar, so "X/Y abgeschlossen" never drifts
 * between the two. */
export function isSectionVisible(section: LessonSectionMeta, gate: SectionGateState | undefined): boolean {
  const key = SECTION_GATE_KEYS[section.type];
  if (!key) return true;
  return gate ? gate[key].applicable : true;
}

export function isSectionDone(section: LessonSectionMeta, gate: SectionGateState | undefined): boolean {
  const key = SECTION_GATE_KEYS[section.type];
  if (!key || !gate) return false;
  return gate[key].completed;
}

export interface SectionProgress {
  visibleSections: LessonSectionMeta[];
  completed: number;
  total: number;
  percentage: number;
}

export function computeSectionProgress(gate: SectionGateState | undefined): SectionProgress {
  const visibleSections = lessonSections.filter((section) => isSectionVisible(section, gate));
  const trackedSections = visibleSections.filter((section) => {
    const key = SECTION_GATE_KEYS[section.type];
    return key !== null && COMPLETION_TRACKED_GATE_KEYS.includes(key);
  });
  const completed = trackedSections.filter((section) => isSectionDone(section, gate)).length;
  const total = trackedSections.length;
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

  return { visibleSections, completed, total, percentage };
}

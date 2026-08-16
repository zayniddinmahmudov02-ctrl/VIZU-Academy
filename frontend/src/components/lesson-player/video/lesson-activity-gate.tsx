"use client";

import type { ReactNode } from "react";
import { Lock } from "lucide-react";

import Loading from "@/components/common/loading";
import { useSectionGate } from "@/features/lessons/hooks/use-section-gate";
import type { SectionGateKey } from "@/features/lessons/services/section-gate-service";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  lessonId: string;
  /** Which of the 9 sequential sections this gate protects. `null` for
   * sections outside the required order (Hausaufgabe, Ergebnis) — those
   * stay open once the video is done, same as before this feature. */
  section: SectionGateKey | null;
  children: ReactNode;
}

/** Blocks a lesson section behind its specific prerequisite in the
 *  sequence (Video -> Wortschatz -> Grammatik -> Grammatik Quiz -> Lesen
 *  -> Hören -> Schreiben -> Sprechen -> Lesson Quiz) — backed by
 *  GET /lessons/{id}/section-gate, itself backed by real StudentProgress/
 *  StudentQuiz/Assessment data server-side, not local/localStorage state.
 *  This is a UX convenience only: the actual content endpoints
 *  independently enforce the same gate (see
 *  app/api/dependencies/section_gate.py), so this can't be bypassed by
 *  skipping straight to a content URL either. */
export default function LessonActivityGate({ lessonId, section, children }: Props) {
  const { t } = useTranslation();
  const { data: gate, isLoading } = useSectionGate(lessonId);

  if (section === null) {
    return <>{children}</>;
  }

  if (isLoading || !gate) {
    return <Loading />;
  }

  if (gate[section].unlocked) {
    return <>{children}</>;
  }

  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-card border border-dashed border-surface-border bg-surface-hover/60 p-12 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-300 text-slate-600 dark:bg-slate-700 dark:text-slate-300">
        <Lock size={22} />
      </div>

      <p className="text-lg font-semibold text-text-primary">{t("lessons.sectionLocked")}</p>
      <p className="max-w-sm text-sm text-text-secondary">{t("lessons.sectionLockedHint")}</p>
    </div>
  );
}

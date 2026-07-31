"use client";

import type { ReactNode } from "react";
import { Lock } from "lucide-react";

import Loading from "@/components/common/loading";
import { useVideoCompletion } from "@/features/lessons/hooks/use-video-completion";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  lessonId: string;
  children: ReactNode;
}

/** Blocks a lesson activity behind "complete the video first" — backed by
 *  the server's StudentProgress.video_completed, not local/localStorage
 *  state, so it can't be bypassed by clearing storage. The locked visual
 *  treatment mirrors the existing module-lock pattern in
 *  components/courses/detail/module-card.tsx. */
export default function LessonActivityGate({ lessonId, children }: Props) {
  const { t } = useTranslation();
  const completed = useVideoCompletion(lessonId);

  if (completed === null) {
    return <Loading />;
  }

  if (completed) {
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

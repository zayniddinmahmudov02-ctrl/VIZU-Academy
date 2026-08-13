"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { Lock } from "lucide-react";

import Loading from "@/components/common/loading";
import { useLessonAccess } from "@/features/lessons/hooks/use-lesson-access";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  lessonId: string;
  children: ReactNode;
}

/** Wraps every section of a lesson (video included) behind the backend's
 *  can_access_lesson rule — first 3 lessons per level are free, the rest
 *  need Premium/staff. Backed by the real GET /lessons/{id} 403, not a
 *  client-side lesson-number guess, so it can't be bypassed by editing
 *  local state. Mirrors LessonActivityGate's visual treatment. */
export default function PremiumLessonGate({ lessonId, children }: Props) {
  const { t } = useTranslation();
  const state = useLessonAccess(lessonId);

  if (state === "loading") {
    return <Loading />;
  }

  if (state !== "premium_required") {
    return <>{children}</>;
  }

  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-card border border-dashed border-surface-border bg-surface-hover/60 p-12 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-warning/15 text-warning">
        <Lock size={22} />
      </div>

      <p className="text-lg font-semibold text-text-primary">{t("lessons.premiumRequiredTitle")}</p>
      <p className="max-w-sm text-sm text-text-secondary">{t("lessons.premiumRequiredHint")}</p>

      <Link
        href="/vizu-pay"
        className="mt-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
      >
        {t("vorbereitung.unlockPremium")}
      </Link>
    </div>
  );
}

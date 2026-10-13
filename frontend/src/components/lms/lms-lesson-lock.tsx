"use client";

import Link from "next/link";
import { Crown, Lock } from "lucide-react";

import { lessonHref } from "@/features/lms/competencies";
import type { LmsLesson } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";

/** Why a lesson is closed — exactly the reason the backend gave. */
export default function LmsLessonLock({ data }: { data: LmsLesson }) {
  const { t } = useTranslation();
  const reason = data.access.reason;
  const premium = reason === "PREMIUM_REQUIRED";
  const previous = data.navigation.previous;
  const text =
    reason === "PREMIUM_REQUIRED"
      ? ["lms.lockPremiumTitle", "lms.lockPremiumHint"]
      : reason === "PREVIOUS_LESSON_NOT_COMPLETED"
        ? ["lms.lockSequentialTitle", "lms.lockSequentialHint"]
        : reason === "ADMIN_LOCKED"
          ? ["lms.lockAdminTitle", "lms.lockAdminHint"]
          : ["lms.lockLockedTitle", "lms.lockLockedHint"];

  return (
    <div className="flex flex-col items-center gap-3 rounded-card border border-dashed border-surface-border bg-surface-hover/60 p-8 text-center sm:p-12" data-testid="lms-lesson-lock" data-reason={reason ?? ""}>
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-warning/15 text-warning">
        {premium ? <Crown size={24} /> : <Lock size={22} />}
      </div>
      <p className="text-lg font-semibold text-text-primary">{t(text[0])}</p>
      <p className="max-w-md text-sm text-text-secondary">{t(text[1])}</p>
      {premium && (
        <Link href="/angebote" className="mt-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90">
          {t("lms.toAngebote")}
        </Link>
      )}
      {reason === "PREVIOUS_LESSON_NOT_COMPLETED" && previous && (
        <Link href={lessonHref(previous.id)} className="mt-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90">
          {t("lms.toPreviousLesson", { n: previous.number })}
        </Link>
      )}
    </div>
  );
}

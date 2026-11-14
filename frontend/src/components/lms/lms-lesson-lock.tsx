"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Clock, CreditCard, Lock } from "lucide-react";

import { lessonHref, levelHref } from "@/features/lms/competencies";
import type { LmsLesson } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";

import LmsPurchaseModal from "./lms-purchase-modal";

/** Why a lesson is closed — exactly the reason the backend gave. The
 * backend also withholds the lesson content; this only explains it. A
 * lesson that needs a purchase opens the purchase sheet at once ("Ortga
 * qaytish" returns to the previous page, or to the level's lesson list). */
export default function LmsLessonLock({ data }: { data: LmsLesson }) {
  const { t } = useTranslation();
  const router = useRouter();
  const reason = data.access.reason;
  const level = data.lesson.level ?? "";
  const premium = reason === "PREMIUM_REQUIRED";
  const [buying, setBuying] = useState(premium && !!level);
  const back = () => {
    if (window.history.length > 1) router.back();
    else router.push(level ? levelHref(level) : "/kurse");
  };
  const salesClosed = reason === "LEVEL_SALES_CLOSED";
  const soon = reason === "LEVEL_COMING_SOON" || salesClosed;
  const previous = data.navigation.previous;
  const [title, hint] = premium
    ? [t("lms.lockPremiumTitle"), t("lms.lockBuyHint", { level })]
    : salesClosed
      ? [t("lms.lockComingSoonTitle"), t("lms.salesClosedHint")]
    : soon
      ? [t("lms.lockComingSoonTitle"), t("lms.lockComingSoonHint")]
      : reason === "PREVIOUS_LESSON_NOT_COMPLETED"
        ? [t("lms.lockSequentialTitle"), t("lms.lockSequentialHint")]
        : reason === "ADMIN_LOCKED"
          ? [t("lms.lockAdminTitle"), t("lms.lockAdminHint")]
          : [t("lms.lockLockedTitle"), t("lms.lockLockedHint")];

  return (
    <div className="flex flex-col items-center gap-3 rounded-card border border-dashed border-surface-border bg-surface-hover/60 p-8 text-center sm:p-12" data-testid="lms-lesson-lock" data-reason={reason ?? ""}>
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-warning/15 text-warning">
        {soon ? <Clock size={22} /> : <Lock size={22} />}
      </div>
      <p className="text-lg font-semibold text-text-primary">{title}</p>
      <p className="max-w-md text-sm text-text-secondary">{hint}</p>
      {premium && level && (
        <button onClick={() => setBuying(true)} data-testid="lms-lock-buy"
                className="mt-2 inline-flex items-center gap-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90">
          <CreditCard size={16} /> {t("lms.gateBuy")}
        </button>
      )}
      {reason === "PREVIOUS_LESSON_NOT_COMPLETED" && previous && (
        <Link href={lessonHref(previous.id)} className="mt-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90">
          {t("lms.toPreviousLesson", { n: previous.number })}
        </Link>
      )}
      {premium && level && <LmsPurchaseModal level={level} open={buying} onClose={() => setBuying(false)} onBack={back} />}
    </div>
  );
}

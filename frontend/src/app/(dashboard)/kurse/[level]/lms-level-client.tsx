"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, CreditCard, Lock, PlayCircle } from "lucide-react";

import LmsPurchaseModal from "@/components/lms/lms-purchase-modal";
import LmsSkeleton from "@/components/lms/lms-skeleton";
import LmsErrorCard from "@/components/lms/lms-error-card";
import LmsLessonCard from "@/components/lms/lms-lesson-card";
import { LEVEL_GRADIENT } from "@/components/lms/lms-level-card";
import ProgressBar from "@/components/ui/progress-bar";
import { lessonHref } from "@/features/lms/competencies";
import { useLmsLevel } from "@/features/lms/hooks/use-lms";
import { useTranslation } from "@/lib/i18n/use-translation";

/** One level: its published lessons in their order (drafts never reach a
 * student — the backend leaves them out). */
export default function LmsLevelClient({ level }: { level: string }) {
  const { t } = useTranslation();
  const { data, isLoading, error, refetch } = useLmsLevel(level);
  const code = level.toUpperCase();
  const [buying, setBuying] = useState(false);
  const sale = data?.sale;
  // sales_enabled: only a level the admin approved for sale can be bought
  const canBuy = !!sale && !sale.coming_soon && !!sale.sales_enabled && !sale.owned;
  const salesClosed = !!sale?.sales_closed && !sale.owned;

  return (
    <div className="space-y-6">
      <Link href="/kurse" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue">
        <ArrowLeft size={16} /> {t("lms.levelsTitle")}
      </Link>

      {isLoading && <LmsSkeleton variant="grid" />}
      {error ? <LmsErrorCard error={error} onRetry={() => refetch()} backHref="/kurse" backLabelKey="lms.levelsTitle" /> : null}

      {data && (
        <>
          <header className={`overflow-hidden rounded-card bg-gradient-to-br ${LEVEL_GRADIENT[code] ?? "from-brand-600 to-accent-blue"} p-6 text-white shadow-[var(--shadow-md)] sm:p-8`}>
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-white/80">{t("lms.level")}</p>
                <h1 className="text-3xl font-bold sm:text-4xl">{data.level} · {data.title}</h1>
                <p className="mt-2 text-sm text-white/85" data-testid="lms-level-summary">
                  {t("lms.levelSummary", { published: data.lessons_published, total: data.lessons_target, done: data.lessons_completed })}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {data.continue_lesson_id && (
                  <Link href={lessonHref(data.continue_lesson_id)} className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-brand-900 hover:opacity-90">
                    <PlayCircle size={16} /> {t(data.last_lesson_id ? "lms.continue" : "lms.start")}
                  </Link>
                )}
                {canBuy && sale?.offer?.purchasable && (
                  <button onClick={() => setBuying(true)} data-testid="lms-level-buy"
                          className="inline-flex items-center gap-2 rounded-xl bg-white/15 px-5 py-2.5 text-sm font-semibold text-white ring-1 ring-white/40 backdrop-blur hover:bg-white/25">
                    <CreditCard size={16} /> {t("lms.buyCourse")} · {t("lms.som", { n: (sale.offer.sale_price ?? 0).toLocaleString("ru-RU").replace(/ /g, " ") })}
                  </button>
                )}
              </div>
            </div>
            {sale?.coming_soon && (
              <p className="mt-4 inline-flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-semibold" data-testid="lms-level-coming-soon">
                <Lock size={15} /> {t("lms.comingSoonHint")}
              </p>
            )}
            {salesClosed && (
              <p className="mt-4 inline-flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-semibold" data-testid="lms-level-sales-closed">
                <Lock size={15} /> {t("lms.salesClosedHint")}
              </p>
            )}
            <div className="mt-5 max-w-md">
              <ProgressBar value={data.percent} trackClassName="h-2 bg-white/20" indicatorClassName="bg-white" />
              <p className="mt-1 text-xs text-white/80">{data.percent}%</p>
            </div>
          </header>

          {data.lessons.length === 0 ? (
            <p className="rounded-card bg-surface-card p-8 text-center text-text-secondary ring-1 ring-surface-border" data-testid="lms-level-empty">
              {t("lms.levelEmpty")}
            </p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="lms-lessons">
              {data.lessons.map((lesson) => (
                <LmsLessonCard key={lesson.id} lesson={lesson} onBuy={canBuy ? () => setBuying(true) : undefined} />
              ))}
            </div>
          )}
          <LmsPurchaseModal level={data.level} open={buying} onClose={() => setBuying(false)} />
        </>
      )}
    </div>
  );
}

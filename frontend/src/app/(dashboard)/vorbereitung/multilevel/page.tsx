"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Clock3, Crown, History, Lock, LockOpen, PlayCircle, Ticket } from "lucide-react";

import Button from "@/components/ui/button";
import MultilevelPremiumModal, { som, StatusNotice } from "@/features/vizu-pay/components/multilevel-premium-modal";
import { getMlStatus } from "@/features/vizu-pay/services/multilevel-premium-service";
import { formatDuration, levelLabel, levelTone, SECTION_LABEL_KEY, totalLabel } from "@/features/vorbereitung/lib/multilevel-labels";
import { getExams, getHistory, startAttempt } from "@/features/vorbereitung/services/multilevel-exam-service";
import type { ExamListItem } from "@/features/vorbereitung/types/multilevel-exam.types";
import { useTranslation } from "@/lib/i18n/use-translation";

// Multilevel (Zertifikatsprüfungen → Multilevel): every Modelltest (1–10) is a full B1–C1 exam, the result says B1, B2, C1 or
// "Nicht bestanden". Every Modelltest is locked until the student holds the Multilevel Premium (2026-11-19; one purchase, approved by the
// admin, or an approved 100 % promo code); a test that is not published yet shows "Tayyorlanmoqda". Which tests are free comes from the
// server (`tests.free`, 0 now): the free note hides itself.
export default function MultilevelPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modal, setModal] = useState<"intro" | "promo" | null>(null);
  const { data: exams = [], isLoading } = useQuery({ queryKey: ["multilevel-exams"], queryFn: getExams });
  const { data: history = [] } = useQuery({ queryKey: ["multilevel-history"], queryFn: getHistory });
  const { data: premium } = useQuery({ queryKey: ["multilevel-premium"], queryFn: getMlStatus });

  const hasAccess = !!premium && (premium.entitled || premium.staff);
  // the Premium is about the locked tests (all of them without it)
  const locked = exams.filter((e) => e.is_locked).length;
  const canBuy = !!premium && !hasAccess && !premium.pending_order && !premium.blocked && premium.product.purchasable && locked > 0;

  function refresh() {
    void queryClient.invalidateQueries({ queryKey: ["multilevel-premium"] });
    void queryClient.invalidateQueries({ queryKey: ["multilevel-exams"] });
  }

  async function start(exam: ExamListItem) {
    if (exam.open_attempt_id) {
      router.push(`/vorbereitung/multilevel/pruefung/${exam.open_attempt_id}`);
      return;
    }
    setBusy(exam.model_test_id);
    setError(null);
    try {
      const attempt = await startAttempt(exam.model_test_id);
      router.push(`/vorbereitung/multilevel/pruefung/${attempt.attempt_id}`);
    } catch {
      setError(t("multilevelExam.error"));
      setBusy(null);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <Link href="/vorbereitung" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary transition-colors hover:text-accent-blue">
        <ArrowLeft size={16} />
        Vorbereitung
      </Link>

      <header>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">{t("vorbereitung.multilevelSection")} · B1–C1</h1>
        <p className="mt-2 text-text-secondary">{t("vorbereitung.multilevelSubtitle")}</p>
        <p className="mt-1 text-sm text-text-muted">{t("multilevelExam.howItWorks")}</p>
      </header>

      {premium && (
        <section className="space-y-3 rounded-2xl bg-surface-card p-4 shadow-[var(--shadow-sm)] ring-1 ring-amber-500/30 sm:p-5"
          data-testid="ml-premium-banner" data-status={hasAccess ? "ACTIVE" : premium.pending_order ? "PENDING" : "LOCKED"}>
          <p className="flex items-center gap-2 text-sm font-extrabold tracking-tight text-text-primary">
            <Crown size={18} className="text-amber-500" /> {t("mlPremium.title")}
          </p>
          <StatusNotice status={premium} />
          {!hasAccess && !!premium.tests.free && <p className="text-sm font-semibold text-success" data-testid="ml-free-note">{t("mlPremium.freeNote", { free: premium.tests.free })}</p>}
          {canBuy && (
            <>
              <p className="text-sm text-text-secondary">{t("mlPremium.lockedBanner", { locked, price: som(premium.product.price) })}</p>
              <div className="flex flex-col gap-2 sm:flex-row">
                <button type="button" onClick={() => setModal("intro")} data-testid="ml-open-buy"
                  className="rounded-xl bg-accent-blue px-4 py-2.5 text-sm font-bold text-white transition hover:brightness-110">
                  {premium.last_rejected ? t("mlPremium.retry") : `${t("mlPremium.buy")} · ${t("mlPremium.price", { price: som(premium.product.price) })}`}
                </button>
                <button type="button" onClick={() => setModal("promo")} data-testid="ml-open-promo"
                  className="flex items-center justify-center gap-1.5 rounded-xl border border-surface-border px-4 py-2.5 text-sm font-bold text-text-primary transition hover:bg-surface-hover">
                  <Ticket size={15} />{t("mlPremium.enterPromo")}
                </button>
              </div>
            </>
          )}
        </section>
      )}

      {error && <p className="rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {isLoading && <p className="text-sm text-text-secondary">…</p>}
      {!isLoading && exams.length === 0 && (
        <p className="rounded-2xl bg-surface-card p-6 text-center text-sm text-text-secondary ring-1 ring-surface-border">{t("multilevelExam.noExams")}</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {exams.map((exam) => {
          const access = exam.is_locked ? "LOCKED" : exam.available ? "OPEN" : "PREPARING";
          return (
            <div key={exam.model_test_id} className={`flex flex-col gap-3 rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ${exam.is_locked ? "ring-amber-500/25" : "ring-surface-border"}`}
              data-testid={`multilevel-exam-${exam.number}`} data-state={exam.state} data-access={access}>
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-[11px] font-bold uppercase tracking-wide text-accent-blue">VIZU Multilevel · Modelltest {exam.number}</p>
                  <p className="font-semibold text-text-primary" data-testid="exam-title">{exam.title}</p>
                </div>
                <span className={`flex shrink-0 items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold ${
                  access === "LOCKED" ? "bg-amber-500/15 text-amber-600 dark:text-amber-400" : access === "OPEN" ? "bg-success/15 text-success" : "bg-surface-hover text-text-muted"}`}
                  data-testid="exam-access">
                  {access === "LOCKED" ? <Lock size={12} /> : access === "OPEN" ? <LockOpen size={12} /> : <Clock3 size={12} />}
                  {t(access === "LOCKED" ? "mlPremium.cardLocked" : access === "OPEN" ? "mlPremium.cardOpen" : "mlPremium.cardPreparing")}
                </span>
              </div>
              {/* ModelTest.description is the import's source note (PDF name) for the admin, not student text */}
              <p className="text-sm text-text-secondary" data-testid="exam-description">{t("mlPremium.cardDesc")}</p>
              <ul className="space-y-1.5 text-sm" data-testid="exam-sections">
                {exam.sections.map((s) => (
                  <li key={s.type} className="flex items-center justify-between gap-2" data-testid={`exam-section-line-${s.type}`}>
                    <span className="text-text-primary">{t(SECTION_LABEL_KEY[s.type])}</span>
                    <span className="text-text-muted">{t("multilevelExam.minutes", { count: s.duration_minutes })}</span>
                  </li>
                ))}
              </ul>
              <div className="flex items-center justify-between gap-2 border-t border-surface-border pt-2">
                <p className="flex items-center gap-1.5 text-sm font-semibold text-text-primary" data-testid="exam-total">
                  <Clock3 size={14} className="text-text-muted" /> {totalLabel(t, exam.total_minutes)}
                </p>
                <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold ${exam.state === "DONE" ? "bg-success/15 text-success" : exam.state === "IN_PROGRESS" ? "bg-warning/15 text-warning" : exam.state === "PREPARING" ? "bg-surface-hover text-text-muted" : "bg-accent-blue/15 text-accent-blue"}`}
                  data-testid="exam-state">{t(`multilevelExam.state${exam.state}`)}</span>
              </div>
              {exam.attempts > 0 && <p className="text-xs text-text-muted">{t("multilevelExam.attempts", { count: exam.attempts })}</p>}
              {exam.last_result && (
                <p className="text-sm text-text-secondary">
                  {t("multilevelExam.lastResult")}:{" "}
                  <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${levelTone(exam.last_result.result_level)}`}>
                    {levelLabel(t, exam.last_result.result_level)}
                  </span>{" "}
                  {exam.last_result.total_score !== null && `${exam.last_result.total_score} / ${exam.last_result.max_score ?? 300}`}
                </p>
              )}
              {exam.is_locked ? (
                <button type="button" onClick={() => setModal("intro")} data-testid="unlock-exam"
                  className="flex items-center justify-center gap-1.5 rounded-xl border border-amber-500/40 px-4 py-2.5 text-sm font-bold text-amber-600 transition hover:bg-amber-500/10 dark:text-amber-400">
                  <Lock size={14} /> {t("multilevelExam.premium")} · {t("mlPremium.unlock")}
                </button>
              ) : exam.available ? (
                <Button onClick={() => void start(exam)} disabled={busy === exam.model_test_id} data-testid="start-exam">
                  <PlayCircle size={16} />
                  {exam.open_attempt_id ? t("multilevelExam.continue") : exam.attempts ? t("multilevelExam.retake") : t("multilevelExam.start")}
                </Button>
              ) : (
                <p className="flex items-center justify-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2.5 text-sm font-semibold text-text-muted" data-testid="exam-preparing">
                  <Clock3 size={14} /> {t("mlPremium.cardPreparing")}
                </p>
              )}
            </div>
          );
        })}
      </div>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-bold text-text-primary"><History size={18} /> {t("multilevelExam.history")}</h2>
        {history.length === 0 ? (
          <p className="text-sm text-text-muted">{t("multilevelExam.noHistory")}</p>
        ) : (
          <ul className="space-y-2" data-testid="multilevel-history">
            {history.map((h) => (
              <li key={h.attempt_id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-surface-card px-4 py-3 ring-1 ring-surface-border">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-text-primary">{h.title}</p>
                  <p className="text-xs text-text-muted">
                    {new Date(h.started_at).toLocaleDateString("de-DE")} · {formatDuration(h.duration_seconds)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {h.status !== "IN_PROGRESS" && (
                    <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${levelTone(h.result_level)}`}>{levelLabel(t, h.result_level)}</span>
                  )}
                  <Link
                    href={h.status === "IN_PROGRESS" ? `/vorbereitung/multilevel/pruefung/${h.attempt_id}` : `/vorbereitung/multilevel/ergebnis/${h.attempt_id}`}
                    className="text-sm font-semibold text-accent-blue hover:underline"
                  >
                    {h.status === "IN_PROGRESS" ? t("multilevelExam.continue") : t("multilevelExam.viewResult")}
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <MultilevelPremiumModal open={modal !== null} initialStep={modal ?? "intro"} status={premium} onClose={() => setModal(null)} onChanged={refresh} />
    </div>
  );
}

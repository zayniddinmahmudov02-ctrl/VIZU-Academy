"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, History, Lock, PlayCircle } from "lucide-react";

import Button from "@/components/ui/button";
import { formatDuration, levelLabel, levelTone } from "@/features/vorbereitung/lib/multilevel-labels";
import { getExams, getHistory, startAttempt } from "@/features/vorbereitung/services/multilevel-exam-service";
import type { ExamListItem } from "@/features/vorbereitung/types/multilevel-exam.types";
import { useTranslation } from "@/lib/i18n/use-translation";

// Multilevel (Zertifikatsprüfungen → Multilevel): the student never picks a level — every published Modelltest is a
// full B1–C1 exam, the result says B1, B2, C1 or "Nicht bestanden". Only PUBLISHED tests come from the API.
export default function MultilevelPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { data: exams = [], isLoading } = useQuery({ queryKey: ["multilevel-exams"], queryFn: getExams });
  const { data: history = [] } = useQuery({ queryKey: ["multilevel-history"], queryFn: getHistory });

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

      {error && <p className="rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {isLoading && <p className="text-sm text-text-secondary">…</p>}
      {!isLoading && exams.length === 0 && (
        <p className="rounded-2xl bg-surface-card p-6 text-center text-sm text-text-secondary ring-1 ring-surface-border">{t("multilevelExam.noExams")}</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {exams.map((exam) => (
          <div key={exam.model_test_id} className="flex flex-col gap-3 rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border"
            data-testid={`multilevel-exam-${exam.number}`}>
            <div className="flex items-center justify-between gap-2">
              <p className="font-semibold text-text-primary">{exam.title}</p>
              {exam.attempts > 0 && <span className="text-xs text-text-muted">{t("multilevelExam.attempts", { count: exam.attempts })}</span>}
            </div>
            {exam.last_result && (
              <p className="text-sm text-text-secondary">
                {t("multilevelExam.lastResult")}:{" "}
                <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${levelTone(exam.last_result.result_level)}`}>
                  {levelLabel(t, exam.last_result.result_level)}
                </span>{" "}
                {exam.last_result.total_score !== null && `${exam.last_result.total_score} / 300`}
              </p>
            )}
            {exam.is_locked ? (
              <p className="flex items-center gap-1.5 text-sm font-semibold text-warning"><Lock size={14} /> {t("multilevelExam.premium")}</p>
            ) : (
              <Button onClick={() => void start(exam)} disabled={busy === exam.model_test_id} data-testid="start-exam">
                <PlayCircle size={16} />
                {exam.open_attempt_id ? t("multilevelExam.continue") : exam.attempts ? t("multilevelExam.retake") : t("multilevelExam.start")}
              </Button>
            )}
          </div>
        ))}
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
    </div>
  );
}

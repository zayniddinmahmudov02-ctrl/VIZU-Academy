"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, Clock3, PlayCircle } from "lucide-react";

import Button from "@/components/ui/button";
import VizuMultilevelFinishConfirmDialog from "@/features/vizu-multilevel/components/finish-confirm-dialog";
import ExamSection from "@/features/vorbereitung/components/multilevel/exam-section";
import { SECTION_LABEL_KEY } from "@/features/vorbereitung/lib/multilevel-labels";
import { finishAttempt, getAttempt, getSection, startSection } from "@/features/vorbereitung/services/multilevel-exam-service";
import type { ExamSection as Section, SectionPaper } from "@/features/vorbereitung/types/multilevel-exam.types";
import { useTranslation } from "@/lib/i18n/use-translation";

// Exam mode of one attempt: section overview → one running section at a time (server timer) → result page.
export default function MultilevelExamPage() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const { t } = useTranslation();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [paper, setPaper] = useState<SectionPaper | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmFinish, setConfirmFinish] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { data: view, isError } = useQuery({ queryKey: ["multilevel-attempt", attemptId], queryFn: () => getAttempt(attemptId) });

  async function open(section: Section, status: string) {
    setBusy(true);
    setError(null);
    try {
      setPaper(status === "OPEN" ? await getSection(attemptId, section) : await startSection(attemptId, section));
    } catch {
      setError(t("multilevelExam.error"));
      await queryClient.invalidateQueries({ queryKey: ["multilevel-attempt", attemptId] });
    } finally {
      setBusy(false);
    }
  }

  async function closed() {
    await queryClient.invalidateQueries({ queryKey: ["multilevel-attempt", attemptId] });
    setTimeout(() => setPaper(null), 1200);
  }

  async function finish() {
    setBusy(true);
    try {
      await finishAttempt(attemptId);
      await queryClient.invalidateQueries({ queryKey: ["multilevel-history"] });
      router.push(`/vorbereitung/multilevel/ergebnis/${attemptId}`);
    } finally {
      setBusy(false);
      setConfirmFinish(false);
    }
  }

  if (isError) return <p className="mx-auto max-w-3xl text-sm text-text-secondary">{t("multilevelExam.error")}</p>;
  if (paper) return <div className="mx-auto max-w-3xl"><ExamSection paper={paper} onClosed={closed} /></div>;

  const anyOpen = view?.sections.some((s) => s.status === "OPEN");

  return (
    <div className="mx-auto max-w-3xl space-y-6" data-testid="exam-overview">
      <Link href="/vorbereitung/multilevel" className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-accent-blue">
        <ArrowLeft size={16} /> {t("multilevelExam.back")}
      </Link>
      <header>
        <h1 className="text-2xl font-bold text-text-primary">{view?.title ?? "…"}</h1>
        <p className="mt-1 text-sm text-text-muted">{t("multilevelExam.resultsAfterFinish")}</p>
      </header>
      {error && <p className="rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}

      <div className="grid gap-3 sm:grid-cols-2">
        {view?.sections.map((s) => {
          const done = s.status === "SUBMITTED" || s.status === "EXPIRED";
          return (
            <div key={s.type} className="flex flex-col gap-3 rounded-2xl bg-surface-card p-5 ring-1 ring-surface-border" data-testid={`exam-section-${s.type}`}>
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold text-text-primary">{t(SECTION_LABEL_KEY[s.type])}</p>
                <span className="flex items-center gap-1 text-xs text-text-muted"><Clock3 size={13} /> {t("multilevelExam.minutes", { count: s.duration_minutes })}</span>
              </div>
              <p className={`flex items-center gap-1.5 text-sm ${done ? "text-success" : "text-text-secondary"}`}>
                {done && <CheckCircle2 size={14} />} {t(`multilevelExam.status${s.status}`)}
              </p>
              {!view.finished && !done && (
                <Button onClick={() => void open(s.type, s.status)} disabled={busy || (s.status !== "OPEN" && !s.can_start)} variant={s.status === "OPEN" ? "primary" : "secondary"}>
                  <PlayCircle size={15} /> {s.status === "OPEN" ? t("multilevelExam.openSection") : t("multilevelExam.startSection")}
                </Button>
              )}
              {!view.finished && s.status === "NOT_STARTED" && anyOpen && <p className="text-xs text-text-muted">{t("multilevelExam.oneAtATime")}</p>}
            </div>
          );
        })}
      </div>

      {view && (view.finished ? (
        <Link href={`/vorbereitung/multilevel/ergebnis/${attemptId}`}><Button fullWidth>{t("multilevelExam.viewResult")}</Button></Link>
      ) : (
        <Button variant="secondary" fullWidth onClick={() => setConfirmFinish(true)} disabled={busy} data-testid="finish-exam">
          {t("multilevelExam.finishExam")}
        </Button>
      ))}

      <VizuMultilevelFinishConfirmDialog
        open={confirmFinish}
        onCancel={() => setConfirmFinish(false)}
        onConfirm={() => void finish()}
        isSubmitting={busy}
        title={t("multilevelExam.finishExam")}
        body={t("multilevelExam.confirmFinish")}
        confirmLabel={t("multilevelExam.finishExam")}
      />
    </div>
  );
}

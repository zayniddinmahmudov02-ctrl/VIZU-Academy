"use client";

import { useMemo, useRef, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, CircleDot, History, RotateCcw, Trophy, XCircle } from "lucide-react";

import type { AttemptResult, AttemptSummary, PublicQuestion, SkillAttempt } from "@/features/lessons/services/lesson-skills-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

export interface SkillTestSection {
  id: string;
  header?: ReactNode;
  questions: PublicQuestion[];
}

interface Props {
  sections: SkillTestSection[];
  summary: AttemptSummary;
  attempts: SkillAttempt[];
  start: () => Promise<SkillAttempt>;
  submit: (attemptId: string, answers: Record<string, string>) => Promise<AttemptResult>;
  review: (attemptId: string) => Promise<AttemptResult>;
  /** react-query keys refreshed after a submission */
  invalidate: unknown[][];
  /** shown in the result view (e.g. the Hören transcript) */
  onResult?: (result: AttemptResult) => void;
  testId?: string;
}

const LETTERS = ["A", "B", "C", "D", "E", "F"];

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds < 0) return "—";
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

/** One Lesen / Hören test: answer -> "Antworten überprüfen" -> server-graded
 * result with the correct answers. The answer key never reaches the browser
 * before the attempt is submitted; the attempt (and its timer) starts on the
 * first selected answer. */
export default function SkillTest({ sections, summary, attempts, start, submit, review, invalidate, onResult, testId }: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const questions = useMemo(() => sections.flatMap((s) => s.questions), [sections]);

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [ownAttemptId, setAttemptId] = useState<string | null>(null);
  const [submittedIds, setSubmittedIds] = useState<string[]>([]);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const starting = useRef<Promise<SkillAttempt> | null>(null);

  // resume an open attempt from the server (e.g. after a reload), but never
  // one that was just submitted while the summary is still being refreshed
  const serverOpen = summary.in_progress_attempt_id;
  const attemptId = ownAttemptId ?? (!result && serverOpen && !submittedIds.includes(serverOpen) ? serverOpen : null);

  const answered = questions.filter((q) => answers[q.id]).length;
  const resultById = useMemo(() => new Map((result?.results ?? []).map((r) => [r.question_id, r])), [result]);

  async function ensureAttempt(): Promise<string> {
    if (attemptId) return attemptId;
    if (!starting.current) starting.current = start();
    const attempt = await starting.current;
    starting.current = null;
    setAttemptId(attempt.id);
    return attempt.id;
  }

  function choose(questionId: string, optionId: string) {
    if (result || busy) return;
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }));
    setError(null);
    void ensureAttempt().catch(() => setError(t("lessons.loadError")));
  }

  async function doSubmit() {
    setConfirming(false);
    setBusy(true);
    setError(null);
    try {
      const id = await ensureAttempt();
      const graded = await submit(id, answers);
      setSubmittedIds((prev) => [...prev, id]);
      setResult(graded);
      setAttemptId(null);
      onResult?.(graded);
      for (const key of invalidate) await queryClient.invalidateQueries({ queryKey: key });
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      setError(t("lessons.loadError"));
    } finally {
      setBusy(false);
    }
  }

  function check() {
    if (answered < questions.length) setConfirming(true);
    else void doSubmit();
  }

  function retake() {
    setResult(null);
    setAnswers({});
    setAttemptId(null);
  }

  async function showLast() {
    const last = [...attempts].reverse().find((a) => a.status === "SUBMITTED");
    if (!last) return;
    setBusy(true);
    try {
      const graded = await review(last.id);
      setResult(graded);
      setAnswers(Object.fromEntries(graded.results.filter((r) => r.selected_option_id).map((r) => [r.question_id, r.selected_option_id as string])));
      onResult?.(graded);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6" data-testid={testId}>
      {/* status bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-surface-card px-4 py-3 ring-1 ring-surface-border">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          {!result && (
            <span className="font-semibold text-text-primary" data-testid="test-progress">
              {t("lessons.testAnswered", { n: answered, total: questions.length })}
            </span>
          )}
          {summary.attempts_count > 0 && (
            <span className="text-text-secondary">{t("lessons.testAttempts", { n: summary.attempts_count })}</span>
          )}
          {summary.best_score !== null && (
            <span className="inline-flex items-center gap-1 font-semibold text-text-primary">
              <Trophy size={14} className="text-amber-500" />
              {t("lessons.testBest", { score: summary.best_score })}
            </span>
          )}
        </div>
        {!result && summary.attempts_count > 0 && (
          <button type="button" onClick={showLast} disabled={busy} className="inline-flex items-center gap-1.5 text-sm font-medium text-accent-blue hover:underline">
            <History size={14} />
            {t("lessons.testShowResult")}
          </button>
        )}
      </div>

      {result && (
        <div className="rounded-2xl bg-gradient-to-br from-brand-900 to-brand-700 p-6 text-white sm:p-7" data-testid="test-result">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-white/70">{t("lessons.testResult")}</p>
          <p className="mt-1 text-4xl font-extrabold tabular-nums">{t("lessons.testScore", { score: result.score })}</p>
          <p className="mt-1 text-sm text-white/85">
            {t("lessons.testCorrectCount", { correct: result.correct_count, total: result.question_count })}
            {" · "}
            {t("lessons.testDuration", { time: formatDuration(result.attempt.duration_seconds) })}
          </p>
          <button
            type="button"
            onClick={retake}
            className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-semibold backdrop-blur transition hover:bg-white/25"
            data-testid="test-retake"
          >
            <RotateCcw size={15} />
            {t("lessons.testRetake")}
          </button>
        </div>
      )}

      {sections.map((section) => (
        <div key={section.id} className="space-y-4">
          {section.header}
          {section.questions.map((q) => {
            const qIndex = questions.indexOf(q) + 1;
            const r = resultById.get(q.id);
            const chosen = answers[q.id];
            return (
              <div
                key={q.id}
                className={cn(
                  "rounded-2xl bg-surface-card p-4 ring-1 sm:p-5",
                  r ? (r.is_correct ? "ring-success/50" : "ring-danger/40") : chosen ? "ring-accent-blue/40" : "ring-surface-border",
                )}
                data-testid="test-question"
              >
                <div className="flex items-start gap-3">
                  <span
                    className={cn(
                      "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold",
                      r ? (r.is_correct ? "bg-success text-white" : "bg-danger text-white") : chosen ? "bg-accent-blue text-white" : "bg-surface-hover text-text-secondary",
                    )}
                    aria-hidden="true"
                  >
                    {r ? (r.is_correct ? <CheckCircle2 size={15} /> : <XCircle size={15} />) : qIndex}
                  </span>
                  <p className="pt-0.5 text-[15px] font-semibold text-text-primary">{q.question}</p>
                </div>

                <div className={cn("mt-3 grid gap-2", q.question_type === "TRUE_FALSE" ? "grid-cols-2" : "sm:grid-cols-1")} role="radiogroup" aria-label={q.question}>
                  {q.options.map((o, i) => {
                    const selected = chosen === o.id;
                    const isKey = r?.correct_option_id === o.id;
                    return (
                      <button
                        key={o.id}
                        type="button"
                        role="radio"
                        aria-checked={selected}
                        disabled={!!result || busy}
                        onClick={() => choose(q.id, o.id)}
                        className={cn(
                          "flex min-h-11 items-center gap-2.5 rounded-xl px-3.5 py-2.5 text-left text-sm ring-1 transition-colors",
                          r
                            ? isKey
                              ? "bg-success/10 font-semibold text-success ring-success/50"
                              : selected
                                ? "bg-danger/10 text-danger ring-danger/40"
                                : "text-text-secondary ring-surface-border"
                            : selected
                              ? "bg-accent-blue font-semibold text-white ring-accent-blue"
                              : "bg-surface-hover/50 text-text-primary ring-surface-border hover:ring-accent-blue/50",
                        )}
                        data-testid="test-option"
                      >
                        {q.question_type !== "TRUE_FALSE" && (
                          <span className={cn("text-xs font-bold", selected && !r ? "text-white/80" : "text-text-muted")}>{LETTERS[i]})</span>
                        )}
                        <span>{o.text}</span>
                        {selected && !r && <CircleDot size={14} className="ml-auto" />}
                      </button>
                    );
                  })}
                </div>

                {r && (
                  <div className="mt-3 space-y-1 text-xs">
                    {!r.selected_option_id && <p className="font-semibold text-danger">{t("lessons.testNotAnswered")}</p>}
                    {r.explanation && <p className="text-text-secondary">{r.explanation}</p>}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}

      {error && <p className="text-sm text-danger">{error}</p>}

      {!result && questions.length > 0 && (
        <div className="sticky bottom-3 z-10 flex flex-col gap-3 rounded-2xl bg-surface-card/95 p-3 shadow-[var(--shadow-md)] ring-1 ring-surface-border backdrop-blur sm:flex-row sm:items-center sm:justify-between">
          {confirming ? (
            <>
              <p className="text-sm font-medium text-warning">{t("lessons.testConfirmUnanswered", { n: questions.length - answered })}</p>
              <div className="flex gap-2">
                <button type="button" onClick={() => setConfirming(false)} className="min-h-11 rounded-xl px-4 text-sm font-semibold text-text-secondary ring-1 ring-surface-border">
                  {t("lessons.confirmNo")}
                </button>
                <button type="button" onClick={() => void doSubmit()} className="min-h-11 rounded-xl bg-accent-blue px-4 text-sm font-semibold text-white" data-testid="test-confirm">
                  {t("lessons.confirmYes")}
                </button>
              </div>
            </>
          ) : (
            <>
              <span className="text-sm text-text-secondary">{t("lessons.testAnswered", { n: answered, total: questions.length })}</span>
              <button
                type="button"
                onClick={check}
                disabled={busy || answered === 0}
                className="min-h-11 rounded-xl bg-accent-blue px-5 text-sm font-bold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
                data-testid="test-check"
              >
                {busy ? t("lessons.testChecking") : t("lessons.testCheck")}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
